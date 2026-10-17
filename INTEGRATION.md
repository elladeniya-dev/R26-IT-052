# Trend Analysis Component — Integration Summary

Owner: Gividu (branch `trend-analysis-gividu` on the group repo). This is one of 5 components in the OutfitIQ project. This file is what another component's agent/dev needs to read to call into this service — it is not the full internal design doc.

## What this component does

Scrapes ~20 Sri Lankan fashion e-commerce sites daily, tracks every product's price/stock/rank over time, and scores which **categories, colors, fabrics, and other attributes** are trending up or down right now. A hybrid engine (MRTF restock/disappearance signal + a small trained neural net, "TrendNet") produces the scores once a day. Everything else — API, database, ML — lives in this one FastAPI service.

This component **owns the product catalog data** (it's the one doing the scraping), so other components needing "what products exist / what's trending" should call this API rather than re-scraping anything themselves.

## Folder structure

```
trend-analysis-engine/
├── app/                        # the FastAPI backend
│   ├── main.py                 # app entrypoint, CORS, /health, /health/ready
│   ├── config.py                # env-based settings (DATABASE_URL, ADMIN_API_KEY, ...)
│   ├── database.py              # SQLAlchemy engine/session
│   ├── api/v1/                  # route handlers — trends.py, products.py, brands.py, stats.py, admin.py
│   ├── services/                 # business logic (one per API area)
│   ├── repositories/             # all SQL lives here, nowhere else
│   ├── models/                   # SQLAlchemy ORM tables
│   ├── schemas/                  # Pydantic request/response shapes
│   └── ml/                       # self-contained trend-scoring engine (TrendNet + MRTF)
├── alembic/versions/             # database migrations, numbered 0000–0007
├── jobs/
│   ├── ingest.py                 # loads scraper JSON into the DB (daily)
│   └── compute_trends.py         # runs the ML engine, writes trend scores (daily)
├── trend-data-collector/         # the scraper itself (separate concern, not an API)
├── tests/                        # pytest suite, incl. a golden-file ML test
├── outfitiq/                     # the shared Flutter app (all 5 components' screens live here)
├── requirements.txt              # single unified dependency set for the whole backend
└── render.yaml                   # deploy config (Render, service name "outfitiq-backend")
```

## Running it locally

```bash
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Needs a `.env` with `DATABASE_URL` (Postgres) and `ADMIN_API_KEY`. Ask Gividu for real values — don't invent your own DB.

- **Local base URL:** `http://127.0.0.1:8000/api/v1`
- **Deployed:** Render service `outfitiq-backend` — confirm the live URL with Gividu, don't guess it.
- **CORS** is currently open (`allow_origins=["*"]`) so any localhost port can call it during development.

## API — what's available

All routes below are under `/api/v1` except health checks. Everything is `GET` and public except `/admin/*`, which needs header `X-API-Key: <ADMIN_API_KEY>`.

| Endpoint | What it gives you |
|---|---|
| `GET /trends/products?horizon=3&limit=20` | **Most likely what you want** — real, current products (image, price, brand, url) picked from what's trending up right now. |
| `GET /trends?horizon=3&limit=5` | Raw attribute trend scores, grouped by type (category/color/fabric/...). |
| `GET /trends/meta?horizon=3` | When the latest trend snapshot was computed, and which model produced it. |
| `GET /trends/history/{attr_type}/{attr_value}` | How one attribute (e.g. `color=white`) has trended over the last N days. |
| `GET /trends/{attr_type}` | Top-ranked values for one attribute type. |
| `GET /products?brand=&category=&color=&page=&size=` | Paginated catalog browse/filter. |
| `GET /products/{product_id}` | One product + its raw attributes. |
| `GET /products/{product_id}/history` | Price/stock history for one product. |
| `GET /brands` | Active brands being tracked. |
| `GET /brands/{slug}/coverage` | Scrape health for one brand (did today's scrape run/succeed). |
| `GET /stats/overview` | Dataset size, date range, freshness. |
| `GET /stats/attributes/{attr_type}` | Value distribution for one attribute type. |
| `GET /health`, `GET /health/ready` | Liveness / readiness (DB + model + snapshot freshness). |

Full request/response shapes are in `app/schemas/*.py` — every route's return type is defined there.

## Things worth knowing before integrating

- **Trends are not computed live.** A daily GitHub Actions job (scrape → ingest → compute, see `.github/workflows/daily_trend_harvester.yml`) is the only thing that ever runs the ML engine. The API only ever reads what that job last wrote. Don't expect `/trends/*` to reflect something that happened 5 minutes ago.
- **`product_id` format** is `"{brand_slug}:{native_id}"` (e.g. `"gflock:mid-blue-wide-leg-jean-..."`) — stable, safe to use as a foreign key from another component.
- **Attribute values are mostly raw/unnormalized** (lowercase, trimmed, but as scraped) except `category`, which is canonicalized to a fixed H&M-style taxonomy (`app/ml/category_map.py`). Don't assume color/style/fabric values are a clean fixed enum.
- If you need something this API doesn't expose yet, ask Gividu rather than querying the database directly — the schema (`app/models/`) is expected to keep evolving.
