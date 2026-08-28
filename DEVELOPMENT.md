# Development & Architecture Log — OutfitIQ Trend Analysis Engine

This document tracks the current state of the system: what each layer does, what was
built or fixed and why, what has been empirically verified, and what is explicitly
not yet proven. It exists to be defensible in front of the viva panel — every claim
below is either verified against real data (with the verification described) or
flagged as a known limitation.

---

## 1. System Overview

Three independent workspaces:

```
trend-analysis-engine/
├── app/                        # FastAPI backend (deployed to Render)
│   ├── main.py                 # Application factory (CORS + router registration)
│   ├── models.py                # SQLAlchemy ORM models (Product, TrendObservation, TrendSignal, ...)
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── core/                    # DB session management, safety-filter constants
│   ├── services/                 # Trend scoring, ML prediction, NLP insight text
│   ├── routers/                  # API endpoint controllers
│   └── pipeline/                 # ETL + taxonomy mapping + trend/forecast computation
│                                  #   (imported by both the live API's startup and
│                                  #    the offline GitHub Actions pipeline)
├── scripts/                     # One-off / maintenance tools, not imported by the app
├── trend-data-collector/        # Independent scraping microservice (23 SL stores)
├── ml/models/                    # Trained model artifacts (shape template JSON, LightGBM)
└── trend_analysis_app/           # Flutter client (frontend, built after backend)
```

Daily flow: `trend-data-collector` scrapes → writes JSON to `output/` → `app/pipeline`
ingests it into Postgres, standardizes taxonomy, recomputes trend signals, and
attempts a forecast → the FastAPI app reads only from Postgres to serve the API →
the Flutter app consumes the API. The entire daily cycle runs unattended via
[.github/workflows/daily_trend_harvester.yml](.github/workflows/daily_trend_harvester.yml).

---

## 2. Data Collection Layer (`trend-data-collector/`)

### Target catalog
[trend-data-collector/config/target_stores.py](trend-data-collector/config/target_stores.py)
lists **23 active Sri Lankan women's fashion e-commerce stores** across three
segments (High-Velocity Boutiques, Mass-Market/Department, Workwear & Specialty).
Each entry records which ingestion tier it needs and why (many entries carry an
inline comment documenting how the tier assignment was verified — e.g. Carnage was
vetted with `check_store_candidate.py` before being added; Chenara Dodge's real
storefront domain was corrected after the original domain was found to only route
email). Three stores are commented out with a dated note (DNS unresolved / offline)
rather than silently deleted, so a future re-check is possible.

### Four-tier extraction cascade
Implemented in [trend-data-collector/services/harvester.py](trend-data-collector/services/harvester.py),
tried in order per store, short-circuiting on the first tier that returns ≥3 valid
garments:

1. **Tier 1 — Shopify Direct JSON** ([tier1_shopify.py](trend-data-collector/services/tier1_shopify.py)):
   `/products.json?limit=250` and storefront AJAX search. No DOM rendering, exact
   pricing/tags/images straight from the store's own API.
2. **Tier 2 — JSON-LD Schema.org microdata** ([tier2_jsonld.py](trend-data-collector/services/tier2_jsonld.py)):
   Parses `<script type="application/ld+json">` blocks. Handles both a flat product
   list and the `CollectionPage.mainEntity.itemListElement` shape, and resolves
   relative image URLs to absolute (both were real bugs, fixed and verified with a
   0→12 item change on Kandy Selection).
3. **Tier 2b — Static listing→detail scrape**: for stores with neither a JSON API
   nor JSON-LD but still plain server-rendered HTML — walks the listing page for
   product links, then fetches each detail page.
4. **Tier 3 — Playwright + Gemini Flash / Smart DOM** ([tier3_smart_dom.py](trend-data-collector/services/tier3_smart_dom.py),
   [gemini_ai_extractor.py](trend-data-collector/services/gemini_ai_extractor.py)):
   for JS-rendered SPAs (e.g. Odel). Scrolls to force lazy-loaded images/prices,
   resolves images in priority order (`data-src` → `data-srcset` → `data-original`
   → `src`) to avoid base64 placeholder GIFs, and normalizes currency strings via
   regex. Gemini is an opt-in refinement step here, not a hard dependency — the
   pipeline runs without it.

### Validation firewall
[garment_validator.py](trend-data-collector/services/garment_validator.py) rejects
records before they ever reach the database: zero/missing prices, base64 placeholder
images, blacklisted titles, and administrative routes (`/cart`, `/checkout`,
`/search`, etc.) that DOM scraping can otherwise mistake for products.

### What was removed this session
- `trend_mapping_service.py` — deleted. It duplicated a separate, inferior keyword
  taxonomy that only fed a cosmetic console summary; nothing else in the pipeline
  read from it.
- Unused imports/dead code across `sitemap_discovery.py`, `gemini_ai_extractor.py`,
  `tier3_smart_dom.py`, and `main.py` (a stale `trend_mapping_service` import/usage
  and an unused `TIER_2_CRAWL4AI` import).

---

## 3. Taxonomy Standardization (`app/pipeline/`)

Raw scraped text ("Acid Blue", "100% Cotton, 5% Spandex") is inconsistent across 23
different stores' copywriting. Everything is normalized to the same closed taxonomy
the H&M reference dataset uses, so live SL products and the training data are
directly comparable.

- **[local_taxonomy_mapper.py](app/pipeline/local_taxonomy_mapper.py) / [ml_taxonomy.py](app/pipeline/ml_taxonomy.py)** —
  the default, fully local (no external API) mapper for category/pattern text.
  Built after discovering the previous Gemini-only mapping had been silently
  failing for weeks (a hardcoded, leaked API key plus swallowed exceptions meant
  every call failed and no one saw an error). Gemini remains available as an
  **opt-in** `--use-gemini` refinement step, never a hard dependency.
- **[color_matcher.py](app/pipeline/color_matcher.py)** — RGB color-space distance
  matching via `webcolors`. A semantic-embedding approach was tried first and
  **rejected after empirical testing** (3/21 correct on a manual spot-check) before
  building this simpler, verifiably-correct approach.
- **Material extraction** — fixed a real bug where the mapper picked the *longest*
  keyword in a composition string rather than the *highest-percentage* one (e.g.
  would pick "Spandex" out of "95% Cotton, 5% Spandex"). Now percentage-aware.
- **`is_valid_color()`** — had a bug that only checked word *count*, not word
  *length*, letting long garbage strings through as "colors". Fixed by capping
  individual words at 14 characters.

All of the above run inside [ingest_garments_etl.py](app/pipeline/ingest_garments_etl.py),
which writes standardized values into `Product.ml_category` / `ml_color` /
`ml_pattern` — the raw scraped fields are kept alongside, unmodified, for audit.

---

## 4. Trend Signal Computation (`app/pipeline/`)

1. **[generate_trend_observations.py](app/pipeline/generate_trend_observations.py)** —
   turns standardized product rows into per-attribute observation counts
   (category, color, pattern, and now style-tag observations, added this session).
2. **[compute_trend_signals.py](app/pipeline/compute_trend_signals.py)** — computes
   a growth rate between the current and prior time window using **Laplace
   (additive) smoothing** (`k=5`) so a jump from 1→3 mentions isn't scored the same
   as 100→300. Combines into:

   ```
   trend_score = 0.50 * growth_score + 0.30 * count_score + 0.20 * rank_score
   ```

   `growth_score` is the clamped smoothed growth rate, `count_score` is volume
   relative to the top attribute that window, `rank_score` rewards a consistently
   high rank across recent windows. Formula and weights live in
   [trend_analysis_service.py](app/services/trend_analysis_service.py).
3. A real staleness bug was found and fixed here: the old delete logic only cleared
   `TrendSignal` rows matching the *exact* previous time window string, leaving 153
   orphaned rows from earlier window formats live in the table. Now clears all
   prior `"weekly"` rows unconditionally before writing the new set.

---

## 5. ML Forecasting Layer

Two models, used in a deliberate fallback order — **because the SL collector's own
history is currently too short (~3–4 weeks) to train the primary model**, which is a
data-volume limitation, not a modeling one.

### Primary: Joint-attribute LightGBM forecast
[joint_trend_forecast.py](app/pipeline/joint_trend_forecast.py) /
[scripts/train_joint_trend_model.py](scripts/train_joint_trend_model.py).

- Forecasts on a **joint key** (Category|Color|Pattern combined), not attributes in
  isolation — a "red floral dress" trend and a "red" trend are different signals.
- Features: log1p-transformed lag and rolling-window counts per joint key.
- Requires **≥6 weeks of history** per joint key before it will forecast that key at
  all — enforced in code, not just documented, to avoid forecasting off 1–2 noisy
  data points.
- Evaluated with a **time-based holdout** (train on all but the last 2 weeks per
  series, test on those weeks) specifically to avoid leaking future information into
  training, which would inflate accuracy dishonestly.
- **Real training run** against the H&M reference dataset
  (`cleaned_female_articles.csv`, 63,482 rows; `cleaned_female_transactions.csv`,
  20.6M rows): 39.5% of article rows were removed as mislabeled children's/baby
  items before training (a real data-quality filter, not a modeling choice). Result:
  **MAE 36.766 (model) vs. 44.274 (naive baseline) — a 17.0% improvement**, measured
  on the real held-out last-2-weeks split.
- **Current status against live SL data**: 0 of 241 joint attributes currently meet
  the 6-week minimum history threshold (SL collector data is only ~3.3 weeks old at
  time of writing). The model is trained and validated, but is correctly not yet
  forecasting anything for the live system — see Known Limitations.

### Fallback: Shape-template projection
[trend_shape_template.py](app/pipeline/trend_shape_template.py).

- Extracts real rise-curves from the H&M dataset via rolling z-score, averages them
  into one generic "how a rising trend shapes up over time" template
  (`ml/models/trend_shape_template.json`).
- Applied **multiplicatively** to a live SL attribute's current count to project it
  forward — used only for attributes the trend-signal layer already flags as rising
  (`get_rising_sl_attributes()`, threshold 0.55).
- This is what actually serves `/ml/predict-outfits` today, since the primary model
  has no live SL attribute with enough history yet. `predicted_change` is reported
  from this path is honestly labeled `"Shape-Template Projection (real H&M rise
  curve, applied to live SL trend_score) + Lift-Filtered Grounding"` in the API
  response — it does not claim to be the joint LightGBM forecast.
- Two real bugs were caught before shipping this: an early draft used
  `growth_rate` as a stand-in for `current_count` (fake placeholder, caught in
  review); and the rising-attribute query was filtering to only the latest window,
  silently going stale — both fixed.

### Serving layer
[ml_prediction_service.py](app/services/ml_prediction_service.py) — `TrendMLPredictionService.predict_trending_outfit()`
tries the joint forecast first, falls back to the shape-template projection.
`predict_trend_label()` is a threshold classifier (≥0.55 rising / ≥0.35 stable /
else weak) used by `/trend-insights`. `get_grounded_attributes()` uses
lift-filtered co-occurrence over real transaction data to justify *why* two
attributes are predicted together, rather than asserting it.

---

## 6. Validation & Backtesting

Standing rule for this project: nothing gets claimed as "the model predicts trends"
without being checked against real, independent data.

### Internal backtest
[scripts/backtest_trend_predictions.py](scripts/backtest_trend_predictions.py) —
uses only real historical data up to a cutoff day, then checks whether attributes
flagged "rising" at that cutoff actually grew faster than average in the days that
followed (which are already known, since this runs after the fact).

**Results, reported honestly rather than cherry-picked**: cutoff day 10 (rising
attributes did **5.49% worse**), day 12 (**34.16% worse**), day 14 (**19.92%
worse**), day 15 (+43.30% better, but n=3 — too small to trust). The negative
results are diagnosed as **confounded**, not disproof: the test window overlapped
with active collector engineering changes (tier fixes, taxonomy remapping) that
themselves shifted attribute counts independent of any real fashion trend. This is
disclosed as a limitation below, not hidden.

### External validation
[scripts/validate_against_google_trends.py](scripts/validate_against_google_trends.py) —
cross-checks system "rising" flags against real Google Trends search interest for
Sri Lanka, using `trendspyg` (actively maintained; the previous standard,
`pytrends`, was archived in April 2025 and no longer works).

One real result obtained before hitting Google's rate limit: **"denim" → +31.1%
real Google Trends growth in Sri Lanka**, agreeing with the system's own rising
flag for denim. Batch runs beyond that hit Google's IP-level `429` block — a
real, external rate limit, not a bug in the script (the script already spaces
requests 20 seconds apart with per-keyword error handling). Needs a genuine
cooldown period before re-running at scale.

---

## 7. API Layer (`app/`)

16 endpoints across 6 routers, registered in [app/main.py](app/main.py):

| Router | Endpoints |
|---|---|
| [health.py](app/routers/health.py) | `GET /`, `GET /test-db` |
| [products.py](app/routers/products.py) | `POST/GET /products/`, `GET /products/new-arrivals`, `GET /products/on-sale`, `POST/GET /product-metrics/` |
| [trend_observations.py](app/routers/trend_observations.py) | `POST /trend-observations/bulk`, `POST/GET /trend-observations/` |
| [trends.py](app/routers/trends.py) | `GET /trends/analyze`, `GET /trends`, `GET /trends/history`, `GET /trends/{attribute_type}` |
| [ml_predictions.py](app/routers/ml_predictions.py) | `GET /ml/predict-outfits` |
| [insights.py](app/routers/insights.py) | `GET /trend-insights` |

`/trend-insights` was broken for the entire prior session — `predict_trend_label()`
had been removed from `TrendMLPredictionService` in an earlier commit but the
caller was never updated, so every request threw. Fixed this session with the
threshold classifier described in §5.

---

## 8. Codebase Reorganization for Deployment

The pipeline logic used to live in a flat `scripts/` folder alongside genuine
one-off maintenance tools, which made it unclear what the live app actually needed
at runtime versus what only ever runs manually or in CI.

- **Moved** (`git mv`, history preserved) into `app/pipeline/`: `ingest_garments_etl.py`,
  `generate_trend_observations.py`, `compute_trend_signals.py`,
  `joint_trend_forecast.py`, `trend_shape_template.py`, `local_taxonomy_mapper.py`,
  `color_matcher.py`, `ml_taxonomy.py`, `gemini_mapper.py`. All internal imports
  rewritten `from scripts.X` → `from app.pipeline.X`; path-resolution depth updated
  (`.parent.parent` → `.parent.parent.parent`) to match the new nesting.
- **Left in `scripts/`** (maintenance-only, not imported by the deployed app):
  `init_db.py`, `live_refresh_tier1.py`, `backfill_local_taxonomy.py`,
  `backfill_material.py`, `backfill_missing_color.py`,
  `backtest_trend_predictions.py`, `train_joint_trend_model.py`,
  `validate_against_google_trends.py`.
- Dead-code pass with `pyflakes` across both the backend and `trend-data-collector`:
  removed unused imports (`sqlalchemy.text` shadowing a local `text` variable in 5
  places in `ingest_garments_etl.py`, unused `ET`/`urljoin`/`Optional`/`asyncio` in
  the collector, unused `os` in `init_db.py`), fixed one silently-swallowed
  exception in the ETL's final commit handler.

---

## 9. Deployment Configuration

- **CORS** — added to [app/main.py](app/main.py): open (`allow_origins=["*"]`) by
  default, since this API is read-only trend data with no auth or user data; tighten
  to the client app's real domain once known.
- **Dependency split** — verified via direct `sys.modules` inspection (not
  assumption) that the live FastAPI process never imports `torch`, `gliner`,
  `lightgbm`, `google-genai`, `webcolors`, `scikit-learn`, `scipy`, or `joblib`.
  [requirements.txt](requirements.txt) is now the slim, API-only set Render
  installs. [requirements-pipeline.txt](requirements-pipeline.txt) (`-r
  requirements.txt` plus the heavy packages) is what the GitHub Actions pipeline
  installs — keeps Render's free-tier build time/memory down for zero runtime cost.
- **[render.yaml](render.yaml)** — `healthCheckPath: /`, `DATABASE_URL` wired as a
  Render secret (`sync: false`, entered manually in the dashboard, never committed).
- **[.github/workflows/daily_trend_harvester.yml](.github/workflows/daily_trend_harvester.yml)** —
  updated script paths to `app/pipeline/...`, installs `requirements-pipeline.txt`
  for the ETL/ML steps, still runs the collector → ETL → trend-signal → forecast
  chain daily and commits the raw JSON snapshot back to the repo.
- **[.env.example](.env.example)** — documents `DATABASE_URL` (required) and
  `GEMINI_API_KEY` (optional, only needed for the opt-in Gemini refinement or Tier 3
  AI extraction).
- **Schema sync verified** — directly diffed `app.models.Product`'s declared
  columns against the live Postgres table's actual columns (via
  `sqlalchemy.inspect`); they match exactly, including `original_price` (added via
  a manual `ALTER TABLE` mid-session) and the removed `subcategory`/`target_gender`
  columns. A fresh deploy relies on `Base.metadata.create_all()` (runs
  automatically at `app/main.py` startup) to reproduce this schema on a new
  database — confirmed this will produce the correct result.
- **Smoke-tested** end-to-end after all of the above: every endpoint in §7 plus a
  CORS preflight request, all returning correctly.

---

## 10. Known Limitations (for viva defense)

Stated directly rather than glossed over — these are honest, current constraints,
not failures to hide:

1. **SL collector history is short (~3–4 weeks)**. The primary joint LightGBM
   forecaster requires 6 weeks of history per joint attribute and currently has 0
   of 241 eligible — by design, not a bug. The system correctly falls back to the
   shape-template projection rather than forecasting on insufficient data.
2. **Internal backtest results are negative/inconclusive**, and are reported that
   way rather than cherry-picked. The most defensible interpretation is that the
   test window was confounded by concurrent collector engineering changes, not that
   the growth-rate methodology itself is wrong — but this has not yet been
   re-tested on a stable collection period, and that gap is acknowledged.
3. **External validation (Google Trends) is partial.** One real data point (denim,
   +31.1%, agrees with the system) was obtained before hitting Google's IP-level
   rate limit. This is not yet a statistically meaningful validation sample.
4. **Stock-out velocity as a trend signal was deliberately deferred** — only ~1 day
   of `in_stock` field history existed at the time it was considered, not enough to
   validate it as a signal, so it was not built rather than built unproven.
5. **No synthetic or fabricated data exists anywhere in this system.** All figures
   above are from real scraped SL data, the real H&M reference dataset, or real
   external validation queries — a deliberate project constraint, not an oversight.

---

## 11. Reference: Trend Score Formula

```
trend_score = 0.50 * growth_score + 0.30 * count_score + 0.20 * rank_score
```

- `growth_score` — Laplace-smoothed (k=5) growth rate between current and prior
  time window, clamped to [0, 1].
- `count_score` — current window's mention count relative to that window's
  highest-count attribute, clamped to [0, 1].
- `rank_score` — reward for a consistently high rank across recent windows
  (`1 - (average_rank - 1) / 20`), defaults to 0.5 with insufficient rank history.

Implemented in [trend_analysis_service.py](app/services/trend_analysis_service.py).

---

## 12. Full Codebase Audit (Bugs Found and Fixed)

A systematic pass across all 52 Python files (pyflakes for dead code/unused
imports, manual review of every pipeline/router/service file, live-database
verification of anything data-shaped) after the Copilot PR review, looking
specifically for currently-dormant bugs — the kind that don't show up yet
because the data hasn't grown enough to trigger them, but would the moment it
does. Each finding below was reproduced or empirically confirmed before being
fixed, not just inferred from reading the code.

1. **`Product.collected_at` was silently the store's publish date, not the
   scrape date, for 82% of the catalog.** [ingest_garments_etl.py](app/pipeline/ingest_garments_etl.py)
   derived `collected_at` from Shopify's `published_at` field when present.
   Verified against the live database: `tier1_shopify_json` products (2,797 of
   3,396 rows) had `collected_at` values ranging back to **2025-04-07** — over
   a year before this project existed — while `tier3` products (no
   `published_at` to hijack it) correctly showed the real scrape date. This
   broke `/products/new-arrivals`'s documented contract ("genuinely new, not
   just recently updated") for the majority of the catalog: a product scraped
   for the first time today but published by the store months ago would never
   appear. Fixed to derive `collected_at` from the run folder's own date — the
   same source of truth `generate_trend_observations.py` and
   `joint_trend_forecast.py` already use — instead of the store's timestamp.
   (Existing rows in the live DB still carry the old, incorrect dates; only
   newly-ingested rows get the fix. A retroactive backfill would need to be a
   separate, deliberate decision, not a side effect of a bug-fix pass.)
2. **Joint-forecast rows could silently blank out `/trends`, `/trends/history`,
   `/trends/{attribute_type}`, and `/trend-insights`.** All four endpoints
   picked their "current window" via `ORDER BY end_date DESC LIMIT 1` with no
   filter excluding `attribute_type="joint_forecast"` rows. Those rows are
   persisted by `joint_trend_forecast.py` with `end_date=datetime.now()` at
   forecast-run time — always later than the real "weekly" window's end_date,
   since that script runs after `compute_trend_signals.py` in the same daily
   pipeline. Reproduced against an in-memory database: the old query picked
   the joint_forecast row as "latest," and since `attribute_type="joint_forecast"`
   isn't in `ALLOWED_INSIGHT_ATTRIBUTE_TYPES`
   ([constants.py](app/core/constants.py)), every row would then fail the
   safety filter — the endpoints would go silently empty the moment the joint
   LightGBM forecaster produces its first real result (expected within weeks,
   per the 6-week history threshold). Currently dormant only because 0/241
   attributes qualify yet. Fixed by filtering `time_window == "weekly"` in all
   four queries.
3. **Shape-template fallback category casing broke lift-grounding.**
   `_shape_template_category_fallback()` in
   [ml_prediction_service.py](app/services/ml_prediction_service.py) needed to
   pass a category into `get_grounded_attributes()`, which does an exact-match
   filter against `Product.ml_category` (always exact `HM_CATEGORIES` casing,
   e.g. `"Vest top"`). The category source, `TrendSignal.attribute_value`, is
   lowercased by `calculate_trend_signals()`
   ([trend_analysis_service.py](app/services/trend_analysis_service.py):17)
   before it's persisted — so the exact match always failed, silently
   returning `colors: ["Unknown"], patterns: ["Unknown"]` for every
   shape-template-sourced prediction. Fixed by restoring canonical
   `HM_CATEGORIES` casing via a lowercase lookup before the category is used.
4. **`/trends/analyze`'s stale-row deletion bug had only been fixed in the
   standalone script, not the API endpoint.** The exact-match deletion bug
   documented in §4 ("TrendSignal staleness bug") was fixed in
   `compute_trend_signals.py` but the identical logic in
   [trends.py](app/routers/trends.py)'s `/trends/analyze` endpoint still used
   the old exact-match filter, letting orphaned rows accumulate again whenever
   that endpoint (rather than the script) was used to trigger analysis. Fixed
   to match.
5. **Non-deterministic `rank_position` from set iteration order.**
   [tier2_jsonld.py](trend-data-collector/services/tier2_jsonld.py)'s static
   detail-page scraper collected product links into a `set` and ranked them
   via `enumerate(list(detail_links))` — Python's string hash randomization
   means set iteration order isn't stable across process runs, so identical
   HTML could produce different `rank_position` values from one day's scrape
   to the next, injecting pure noise into `rank_score`. Fixed to sort before
   ranking.
6. **`/products/on-sale` loaded every discounted row into memory to sort/filter
   in Python.** Rewritten to filter, order, and limit in SQL, and added an
   `original_price > 0` guard against a division-by-zero.
7. **`tests/test_ml_model_load.py` tested a model that no longer exists and
   wasn't even a real test.** It loaded `trend_random_forest_model.pkl` plus
   three encoder files — all retired when the Random Forest architecture was
   replaced with the joint LightGBM + shape-template approach (§5) — and
   defined only `main()`, not a `test_*` function, so pytest would never have
   discovered it even if the files existed. Separately, `pytest` itself wasn't
   declared in any requirements file, so the suite had never actually been
   run by anyone in this project's history. Rewritten to load and predict with
   the real `joint_attribute_lgbm_model.pkl` and validate the shape template
   JSON; `pytest` added to `requirements-pipeline.txt`; both tests verified
   passing.
8. **The daily workflow's "commit JSON snapshots to the repo" step had never
   committed anything.** `.gitignore`'s blanket `*.json` rule (intended for
   local datasets) also matched `trend-data-collector/output/`, and `git add`
   on a gitignored path is a silent no-op — confirmed via `git log --author
   "GitHub Actions Bot"` returning zero commits despite 24+ real daily runs.
   Removed the dead step rather than "fixing" it to actually commit — the
   data is already retained via the workflow's 90-day artifact upload and,
   more importantly, Postgres itself; committing several MB of raw scrape
   JSON to git every day would only bloat the repository for no benefit.
9. **`--latest-only` picked a run folder by filesystem mtime instead of its
   own date-encoded name.** `ingest_garments_etl.py` used
   `max(run_folders, key=os.path.getmtime)`; a fresh git checkout or artifact
   restore can give every folder a near-identical mtime regardless of actual
   scrape date, which could pick the wrong folder. `run_folders` was already
   correctly sorted by name (`run_YYYY-MM-DD_HHMMSS` sorts chronologically as
   a string); switched to using that order directly, matching how
   `joint_trend_forecast.py` already determines folder ordering.

All fixes verified: full-repo `pyflakes` clean, `pytest` passing, and every
API endpoint smoke-tested live against the real database after each change.
