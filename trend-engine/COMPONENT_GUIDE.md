# Trend Analysis Component: file-by-file guide

Everything here describes the code in `OutfitIQ-App/trend-engine/` as it is today. Read it in order once, then use the tables as a cheat sheet.

---

## 1. The whole thing in one picture

```
 20ish Sri Lankan stores
        │  (every day, GitHub Actions at 00:00 UTC)
        ▼
 trend-data-collector/        SCRAPE   → output/run_<date>/<store>_garments.json
        │
        ▼
 jobs/ingest.py               INGEST   → Postgres: brands, products, product_attributes, observations, scrape_runs
        │
        ▼
 jobs/compute_trends.py       COMPUTE  → app/ml (panel → engine) → trend_snapshots, trend_scores, trend_segments
        │
        ▼
 app/ (FastAPI)               SERVE    → reads the saved snapshots only (never computes inside a request)
        │
        ▼
 OutfitIQ app / recommender   USE      → POST /trends/score-products with the partner (Koji) catalogue
```

Key rule: **scoring never happens inside an API request.** The daily job computes, the API only reads.

### What "trend" means here
An attribute (colour white, category dress, fabric linen…) or a pair of attributes (white + dress) whose **share of store listings** is forecast to rise over the next 3–5 days. It is a supply-side signal (what stores list), not sales.

### The numbers that matter
| Thing | Value | Where |
|---|---|---|
| Items taken per store | first 100 | `MAX_ITEMS_PER_STORE` in the three tier files |
| Minimum listings for a trend to exist | 8 (mean per day) | `MIN_SUPPORT` in `features.py` |
| Listing-movement window | 6 days | `WINDOW` in `features.py` |
| TrendNet input window | 4 days | `TRENDNET_WINDOW` in `engine.py` |
| Blend | 0.90 TrendNet + 0.10 listing movement | `W_TEMPORAL` in `engine.py` |
| Movement formula | 0.60 × restock − 0.40 × disappear (z-scores) | `W_RESTOCK`, `W_DISAPPEAR` |
| Confidence | high: score ≥ 0.97 and ≥ 3 stores; medium: ≥ 0.39; else low | `confidence_label` |
| Cloth score | sum of its 3 strongest matches | `TOP_MATCHES` |

---

## 2. Folder map

```
trend-engine/
├── app/                      the API and the ML code
│   ├── main.py               app creation, error handlers, health checks
│   ├── config.py             settings (database URL, admin key)
│   ├── database.py           database connection
│   ├── api/                  HTTP routes (thin)
│   ├── services/             business logic
│   ├── repositories/         all database queries
│   ├── models/               database table definitions
│   ├── schemas/              request/response shapes
│   ├── ml/                   everything about attributes, scoring and the model
│   └── core/                 small shared helpers (errors, logging, cache)
├── jobs/                     scripts run on a schedule or by hand
├── alembic/                  database migrations (0000 to 0008)
├── tests/                    48 automated tests
├── trend-data-collector/     the scraper
├── INTEGRATION.md            how the other components use this one
├── render.yaml               deployment settings (Render)
└── requirements.txt          dependencies
```

Layering rule: **api → services → repositories → database.** `app/ml` is self-contained (no database, no HTTP), which is why it is easy to test.

---

## 3. The scraper: `trend-data-collector/`

| File | What it does |
|---|---|
| `main.py` | Entry point. `run_hybrid_harvester()` loops over every store in the config, calls `harvest_store_catalog`, writes one `<store>_garments.json` per store into a timestamped `output/run_YYYY-MM-DD_HHMMSS/` folder, plus a combined file and `run_metadata.json`. A failing store is logged and skipped; it never stops the run. `save_json` writes files; `main()` prints a summary. |
| `config/target_stores.py` | The list of stores (name, domain, segment, which scraping tier to try). Segments: high-velocity boutiques, department stores, workwear/specialty. |
| `services/harvester.py` | The orchestrator. `harvest_store_catalog(store)` tries methods from cheapest to heaviest and stops at the first that returns at least 3 items: Tier 1 → sitemap discovery → Tier 2 JSON-LD → Tier 2b static detail pages → Tier 3 browser/AI. `execute_tier3_smart_dom` is a sync wrapper over the async Tier 3. |
| `services/tier1_shopify.py` | Shopify stores: reads `/products.json` directly (fast, structured). If rate-limited (HTTP 429) it falls back to the store's search-suggest endpoint with keywords. Also pulls colour from variants and parses compare-at price. Capped at 100 items. |
| `services/tier2_jsonld.py` | Stores that embed schema.org product data in the page. `execute_tier2_json_ld` reads it; `execute_tier2_static_detail_scrape` follows listing links to product pages (max 30 pages) for plain-HTML stores. |
| `services/tier3_smart_dom.py` | Last resort: renders the page in a browser (Crawl4AI/Playwright), tries the Gemini AI extractor first, then falls back to reading product cards from the page structure. |
| `services/gemini_ai_extractor.py` | `GeminiAIExtractor`: sends page content to Google Gemini and asks it to return clean product records. Falls back to an older model if quota is hit. Needs `GEMINI_API_KEY`. |
| `services/sitemap_discovery.py` | `discover_catalog_urls` reads a store's sitemap and returns fashion-related URLs (skips men, kids, cart, blog…). |
| `services/spec_parser.py` | `parse_spec_fields` reads spec lines the store wrote itself ("Material: Linen", "Fit Type: Regular") out of the description HTML. Higher quality than guessing from the title. |
| `services/garment_validator.py` | `GarmentValidator.validate_and_sanitize`: the data firewall. Rejects menswear/kids/baby items, menu clutter titles, prices under 500 or over 500,000 LKR, missing or placeholder images, bad URLs. Returns a clean record in one fixed schema, or `{}`. |
| `check_store_candidate.py` / `audit_all_stores.py` | Helper tools (not part of the daily run) to test whether a new store is Shopify and how many products carry real spec sheets. |

**Why the 100-item cap matters:** every store contributes at most its first 100 products. So "a product disappeared" means "left that top-100", not necessarily "sold out".

---

## 4. The daily jobs: `jobs/`

### `ingest.py`: scraper files → database (365 lines)
Run as `python jobs/ingest.py --latest-only`. For each store file it filters, extracts attributes and upserts rows.

| Function | Purpose |
|---|---|
| `parse_run_date` | Reads the date out of the folder name `run_2026-10-19_000102`. |
| `is_inappropriate` | Drops underwear, swimwear, nightwear etc. by keyword. |
| `clean_title` | Strips codes like "- 220826D", "#tag", "UK 8" from a title. |
| `extract_image_name` | Uses words in the image file name as a last-resort colour hint. |
| `is_valid_color`, `scan_text_for_color`, `extract_color` | Colour detection, in priority order: store's colour field → colour tags → title → image name. Rejects garbage like size codes and ids. |
| `extract_category` | Uses the store's product type, else the title, then `map_category` to the closed list. |
| `get_or_create_brand` | Finds or creates the store row. |
| `upsert_product` | Inserts a product once (`first_seen` never changes); later runs update title/image/category. |
| `upsert_attribute` | Inserts (product, attribute type, value) and ignores duplicates. |
| `upsert_observation` | One row per product per day: price, compare-at price, rank, on-sale flag, in-stock flag. Re-running the same day overwrites. |
| `ingest_run` | The main loop for one run folder. Skips a store file that won't parse and records a failed run for it. Records a scrape run (seen vs kept) per store. |
| `run` | Finds the run folders (all, or only the latest). |

### `compute_trends.py`
Creates a `TrendService` and calls `compute_snapshot` for horizon 3 and 5. Prints the snapshot ids. One horizon failing does not stop the other.

### `backfill_attributes.py`
Re-extracts sleeve/neckline/pattern/length/style attributes from existing product titles. Safe to re-run.

### `backfill_segments.py`
Computes pair-trend rows for snapshots that were stored before pairs existed, using only data up to each snapshot's own date (no peeking). Skips snapshots with under 8 days of history.

### `validate_engine.py`: the backtest
Walk-forward test. For every past day it scores using only data up to that day, then compares with what happened over the next 3 or 5 days. It reports:
- **Test 1:** rank correlation (IC) of the engine vs simple baselines: random, current share, recent growth, restock-only.
- **Test 2:** effective sample size and a bootstrap 95% confidence interval ("SIGNIFICANT" if the lower bound is above 0).
- **Test 3:** ranking stability from day to day.

### `validate_live.py`: grades what the live system actually stored
Takes each stored snapshot (a real forward prediction made on its own date), waits until its horizon has passed, and measures IC, realised share change of the top-3 vs bottom-3 predictions, and how often the top-3 picks really rose. Note in its output: consecutive snapshots overlap, so they are not independent trials.

---

## 5. The database: `app/models/` and `alembic/`

| Table | Meaning |
|---|---|
| `brands` | One row per store (slug, name, tier, segment, active flag). |
| `products` | One row per product, id `"{store}:{native id}"`. Title, normalised category, urls, `first_seen`. |
| `product_attributes` | (product, type, value) rows. Types: category, color, pattern, fabric, sleeve_length, garment_length, neckline, style_detail. Raw labels. |
| `observations` | (date, product) rows: price, compare-at, rank, on-sale, new-arrival, in-stock. This is the time series everything is built on. |
| `scrape_runs` | One row per store per day: status, products seen vs kept, error. Unique on (date, store). |
| `dropped_records` | Items rejected during ingest and why. |
| `trend_snapshots` | One row per computed run (date, horizon, model name, window). Unique on (date, horizon, model). |
| `trend_scores` | One row per attribute per snapshot: score, rank, share, share change, restock/disappear rate, breadth, stores, confidence, lifecycle stage, Mann-Kendall p. |
| `trend_segments` | Same idea for pairs, plus the two parts of the pair. |
| `product_lifecycle` (view) | Computed from observations: first/last seen, price range, best rank, still listed. |

Files in `app/models/`: `brand.py`, `product.py` (also `AttrType` enum, `ProductAttribute`, `ProductLifecycle`), `observation.py`, `scrape_run.py` (`ScrapeRun`, `DroppedRecord`), `trend.py` (`TrendSnapshot`, `TrendScore`, `TrendSegment`). `__init__.py` exports them all (Alembic needs that).

Migrations (`alembic/versions/`): `0000` drops the old schema, `0001` brands, `0002` products, `0003` attributes, `0004` observations, `0005` scrape runs + dropped records, `0006` trend snapshots + scores, `0007` the lifecycle view, `0008` trend segments (undo with `alembic downgrade 0007`). `env.py` points Alembic at the app's database URL.

---

## 6. The brain: `app/ml/`

### `features.py`: `build_panel`
Turns raw rows into the model's input. Returns `S, N, RES, DIS, pb, T, days`:
- **S** (share): for each day and each `type|value` key, the fraction of that type's listings carrying it. White's share = listings with white ÷ listings with any colour.
- **N**: the raw counts behind S.
- **RES** (restock): per day, how many products with that key **reappeared** (absent yesterday, present today).
- **DIS** (disappear): how many **left** (present yesterday, absent today).
- **pb**: the same share but per store.
- **T, days**: number of days and the date list.

Details that matter:
- A key is kept only if it averages at least 8 listings a day (`MIN_SUPPORT`).
- Restock/disappear only count when the **store itself was scraped on both days**, so a failed scrape doesn't look like mass disappearance.
- Disappearances of **items on sale are ignored** (`FULL_PRICE_ONLY`), because clearance removal isn't a demand signal.

### `engine.py`: `TrendEngine`
| Piece | What it does |
|---|---|
| `confidence_label(score, stores)` | high / medium / low from the thresholds above. |
| `TrendEngine.__init__` | Loads the TrendNet weights from `app/ml/weights/outfitiq_trendnet.pt` (resolved from the file location, not the working folder). If missing it falls back to the listing-movement score alone. |
| `model_name`, `model_ic` | `"trendnet+mrtf"` or `"mrtf"`, and the IC stored with the checkpoint. |
| `rank(attrs, presence, top_k, horizon)` | The main scorer (below). |
| `rank_by_type` | Same, grouped by attribute type. |
| `_trendnet(S)` | Runs the neural net on the last 4 days of every key. |

**What `rank` does, step by step**
1. Build the panel. Look at the last 6 days (the window).
2. For each key compute: restock rate and disappear rate (events ÷ listings), share now (mean of the last 3 days) vs before (first 3 of the window), **breadth** (what fraction of stores show the share rising from the early to the late half), a Mann-Kendall trend test, how many stores carry it, and a lifecycle label (emerging / peaking / declining / stable) from the slope and its change.
3. **Movement score:** within each attribute type, standardise (z-score) restock and disappear, then `0.6 × restock − 0.4 × disappear`.
4. **TrendNet score:** the net predicts each key's next change; standardise within type.
5. **Final score** = `0.9 × TrendNet + 0.1 × movement`. Without the net, just the movement score.
6. Attach confidence, sort, return one dictionary per key (score, share %, share change %, rates, stores, confidence, stage, window, as-of date).

Honest note: the `horizon` argument is accepted but not used inside `rank`. The 3-day and 5-day snapshots contain the same scores; the horizon changes only what they are graded against.

### `trendnet.py`: the neural network
`TrendNet`: a small GRU (64 units) reads 4 days of normalised share; its last state is joined with an 8-dimension embedding of the attribute type and the log of the attribute's average size; a 3-layer network (73 → 48 → 24 → 1) outputs the predicted change. `load_trendnet(path)` loads weights and returns `(model, checkpoint info)`. The comment at the top is a warning: do not change the architecture without retraining.

### `segments.py`: pairs
- `SEGMENT_PAIRS`: the six pair types (colour×category, fabric×category, colour×fabric, category×neckline, category×sleeve length, category×pattern).
- `segment_rows(attrs)`: for each pair type, joins the two attributes **of the same product on the same day** and emits rows like `white + dress` in the same shape as single attributes, so the same panel builder and engine score them.
- `parse_segment("color_x_category", "white + dress")` → the two parts. `segment_type`, `is_segment_type` are small helpers.

Note: segments reuse the same TrendNet; the net's type embedding only knows the 8 single-attribute types, so pair types fall back to embedding 0.

### `attr_clean.py`
`normalize_color` collapses shades onto base colours ("light blue" → blue, "off-white"/"ivory" → off white, "maroon" → burgundy) and drops anything that isn't a real colour. `clean_attributes` applies it to the whole table, removes the "unknown" category and de-duplicates. Fixed domain rules only; nothing fitted to outcomes.

### `category_map.py`
`map_category(raw)` maps any store wording onto a closed list of 25 categories (H&M style): exact match → synonym table → substring → fuzzy match (cutoff 0.7) → "Unknown". Example: "jeans", "pants", "joggers" → Trousers.

### `extractors.py`
Shared word lists and readers, used both when scraping and when scoring partner products so both sides describe a garment with the same words.
- `extract_material(text)`: prefers a percentage ("95% cotton") else the earliest known fabric word.
- `extract_style_attrs(text)`: returns sleeve length, neckline, silhouette (style detail), pattern and garment length found in text.
- Note: the neckline list contains both "v neck" and "v-neck" as separate labels, which is why those split into two trends.

### `taxonomy.py`: the shared vocabulary
- `canonical_attributes(product)`: turns a partner product (title, description, category, colours, tags) into the engine's canonical attributes: category (with a **title override**: a title naming only pants overrides a "blazer" label, and a blazer filed as a generic "top" becomes a blazer), colours (normalised), fabric, and style attributes (garment length only counts for dresses/skirts etc.).
- `family_of(type, value)`: close-substitute groups: outerwear (jacket, blazer, coat), knitwear, shirting, legwear, one-piece, and colour families (white / off white / cream; blue / navy). A family match counts half.
- `TAXONOMY_VERSION` ("2026.10.3"): bump on any mapping change so other components can pin to it.

### `product_scoring.py`: score a cloth by single attributes
`score_products(products, trends)`: for each product, match it against rising, medium/high-confidence trends.
`contribution = trend score × confidence weight (high 1.0, medium 0.6) × match weight (exact 1.0, family 0.5) × specificity`. Specificity = `log(N/df)/log(N)`, floored at 0.15, so an attribute carried by most of the batch counts less (only applied if the batch has at least 10 cloths). The product's `trend_score` = sum of its top 3 contributions. Returns per-product results plus coverage `meta`.

### `segment_scoring.py`: score a cloth by pairs (what the app uses)
`score_segments(products, segments)`: same idea, but a cloth only matches a pair when it carries **both** parts (each exact = 1.0 or family = 0.5, multiplied). Falling and low-confidence pairs are ignored. `segment_score` = sum of the top 3 contributions; every match is returned with its explanation.

---

## 7. The API: `app/api/`, `services/`, `repositories/`, `schemas/`

### Routes (`app/api/v1/`, all under `/api/v1`)
| Route | What it returns |
|---|---|
| `GET /trends` | Top attributes per type. Params: horizon (3/5), min_confidence, limit. |
| `GET /trends/{attr_type}` | Ranked values for one type. |
| `GET /trends/segments` | Ranked pairs. Params: horizon, min_confidence, segment_type, rising_only, limit. |
| `GET /trends/meta` | When the latest snapshot was computed and by which model. |
| `GET /trends/history/{type}/{value}` | How one attribute's score changed over time. |
| `GET /trends/products` | Real scraped products picked from rising attributes (round-robin across the top 12, per-store cap). **Our own catalogue; the app never shows it.** |
| `POST /trends/score-products` | The main integration call: send up to 500 partner cloths, get back `trend_score`, `segment_score`, and the reasons. Stateless, nothing stored. |
| `GET /products`, `/products/{id}`, `/products/{id}/history` | Browse the scraped catalogue, one product, its price/stock history. |
| `GET /brands`, `/brands/{slug}/coverage` | Stores, and their scrape health. |
| `GET /stats/overview`, `/stats/attributes/{type}` | Dataset size/freshness, value distribution. |
| `GET /admin/runs`, `/admin/dropped`, `POST /admin/compute` | Operations; need the `X-API-Key` header. |
| `GET /health`, `GET /health/ready` | Alive; database + model + snapshot freshness. |

Other API files: `router.py` joins the routers; `deps.py` has the admin-key check (`require_admin_key`; no key set means always refused) and a `pagination` helper that no route currently uses (`/products` declares its own page/size).

### `main.py`
Creates the app, CORS (open for development), and:
- an **error envelope** `{"error": {"code", "message"}}` for every error,
- a guard that rejects NUL characters (400),
- database outage / timeout → 503 `DATABASE_UNAVAILABLE`,
- any unexpected exception → 500 without leaking internals,
- `/health` (no database) and `/health/ready` (database, model file, snapshot no older than 1 day).

### Services (`app/services/`)
- `trend_service.py`: `compute_snapshot` (builds the panel, ranks attributes and pairs, saves a snapshot), `get_trends`, `get_trends_for_type`, `get_history`, `get_meta`, `get_trending_products`, `score_partner_products` (loads the latest snapshot and runs both scorers), `get_segment_trends`. Raises `StaleSnapshotError` (503) if nothing is computed yet.
- `product_service.py`: product/brand lookups with not-found errors, price history.
- `stats_service.py`: dataset overview and attribute distributions.

### Repositories (`app/repositories/`): the only place with database queries
- `trend_repo.py`: `get_latest_snapshot`, `get_scores`, `get_segments`, `get_history`, `save_snapshot` (replaces a same-day snapshot; ranks within each type), `replace_segments`.
- `observation_repo.py`: `get_price_history`, `build_ml_panel_inputs` (reads presence + attributes into the two tables the engine needs, and cleans them).
- `product_repo.py`: product list with filters, lifecycle, bulk lookups, counts and distributions.
- `run_repo.py`: record a scrape run (upsert), log dropped items, runs/coverage queries.
- `base.py`: holds the database session.

### Schemas (`app/schemas/`)
Pydantic shapes for every response: `trend.py` (scores, history, meta, score-products request/response, pair shapes), `product.py`, `brand.py`, `common.py` (page wrapper, error shapes, health).

### Core (`app/core/`)
`exceptions.py` (`AppError` and its 404/401/503 subclasses), `logging.py` (structured JSON logs), `cache.py` (a small time-based cache class that nothing uses yet, so don't describe it as a feature).

### Config
`config.py`: reads `DATABASE_URL` and `ADMIN_API_KEY` from `.env` (found next to the app folder, wherever you start from), forces the modern database driver. `database.py`: the connection, with connection health checks, recycling for Neon, an 8-second connect timeout and a 10-second wait for a free connection.

---

## 8. Tests: `tests/` (48)

| File | What it protects |
|---|---|
| `test_ml_engine.py` | A fixed synthetic dataset must always produce the exact same ranking (golden test); grouping by type; confidence follows score size, not store count. |
| `test_product_scoring.py` | Category/colour/length mapping, family vs exact weights, ignoring falling and low-confidence trends, the common-attribute discount, top-3 sum, coverage, and the pants-filed-as-blazer title fixes. |
| `test_segments.py` | Pair building, the both-parts rule, family weighting, top-3 sum, the segments endpoint, score-products pair fields. |
| `test_api.py` | Health, error envelope, validation (horizon, limits, confidence), admin protection, NUL characters, database-down 503, unexpected-error envelope, paths independent of the working folder. |
| `conftest.py` | Runs tests against the real Postgres inside a transaction that is rolled back, so nothing persists. |

---

## 9. Deployment and automation

`.github/workflows/daily_trend_harvester.yml` (in the component repo): at 00:00 UTC (5:30 am Sri Lanka) it installs dependencies, runs the scraper (`main.py`), then `alembic upgrade head` + `jobs/ingest.py --latest-only`, then `jobs/compute_trends.py`, and uploads the raw output as a 90-day backup. Ingest and compute are skipped if the `DATABASE_URL` secret is missing. `render.yaml` describes the hosted API (builds with `pip install` + `alembic upgrade head`, health check `/health`).

---

## 10. Questions an examiner could ask about the code (and the honest answer)

- **"What do the 3-day and 5-day horizons change?"** Nothing in the scores; the same ranking is graded against the next 3 or 5 days.
- **"Do pairs use a separate model?"** No. The same engine and the same TrendNet; the net's type embedding falls back to a default for pair types.
- **"Why is a declining item sometimes rising?"** Score = forecast of the next change, not the current direction. After a sharp drop the model expects a rebound; graded, those forecasts came true 74% of the time.
- **"Where could data go wrong?"** Top-100 cap per store; a store failing silently; wrong labels from stores (handled partly by the title override); the "v neck" / "v-neck" label split.
- **"Is it deterministic?"** Yes: same data and weights give the same scores; the golden test checks it.
