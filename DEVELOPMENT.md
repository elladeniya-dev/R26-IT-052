# Development & Architecture Log — Gividu Trend Analysis Engine & OutfitIQ

This document tracks the technical evolution, architectural refactoring, and system achievements across the **Trend Analysis Engine**, **Trend Data Collector**, and **Client Frontend** application workspace.

---

## 1. System Architecture Refactoring (Option A Completed)

### Background & Challenge
Originally, the core backend service contained an **866-line monolithic controller file** ([app/main.py](file:///d:/ProjectFiles/trend-analysis-engine/app/main.py)) that combined database initialization, safety filters, domain calculations, ML feature preparation, NLP text formatting, and all API endpoints into a single namespace. Additionally, one-off test scripts resided loosely in the project root.

### Engineering Solution: Layered Modular Architecture
We successfully migrated the codebase to an enterprise-grade **Modular Monolith Layered Architecture** while maintaining 100% cloud deployment compatibility ([render.yaml](file:///d:/ProjectFiles/trend-analysis-engine/render.yaml) entry command `python -m uvicorn app.main:app`).

#### Layer Summary:
1. **Core Layer (`app/core/`)**:
   - [app/core/database.py](file:///d:/ProjectFiles/trend-analysis-engine/app/core/database.py): Manages PostgreSQL environment configuration, SQLAlchemy engine creation, and declarative base sessions.
   - [app/core/constants.py](file:///d:/ProjectFiles/trend-analysis-engine/app/core/constants.py): Centralizes user-facing trend safety blocklists (`EXCLUDED_INSIGHT_KEYWORDS`) and filtering logic.
2. **Domain Services Layer (`app/services/`)**:
   - [app/services/ml_prediction_service.py](file:///d:/ProjectFiles/trend-analysis-engine/app/services/ml_prediction_service.py): Encapsulates Random Forest ML classification inference and attribute encoder handling.
   - [app/services/trend_analysis_service.py](file:///d:/ProjectFiles/trend-analysis-engine/app/services/trend_analysis_service.py): Implements trend score math formulas ($0.50 \times \text{growth\_score} + 0.30 \times \text{count\_score} + 0.20 \times \text{rank\_score}$) and feature engineering derivations.
   - [app/services/trend_insight_service.py](file:///d:/ProjectFiles/trend-analysis-engine/app/services/trend_insight_service.py): Manages NLP fashion text generators and term pluralization rules.
3. **API Routers Layer (`app/routers/`)**:
   - Split API endpoints into modular domain controllers: [health.py](file:///d:/ProjectFiles/trend-analysis-engine/app/routers/health.py), [products.py](file:///d:/ProjectFiles/trend-analysis-engine/app/routers/products.py), [trend_observations.py](file:///d:/ProjectFiles/trend-analysis-engine/app/routers/trend_observations.py), [trends.py](file:///d:/ProjectFiles/trend-analysis-engine/app/routers/trends.py), [ml_predictions.py](file:///d:/ProjectFiles/trend-analysis-engine/app/routers/ml_predictions.py), and [insights.py](file:///d:/ProjectFiles/trend-analysis-engine/app/routers/insights.py).
4. **Lightweight Application Factory (`app/main.py`)**:
   - Replaced the 866-line monolith with a clean **24-line application factory** that bootstraps FastAPI and registers domain routers with organized OpenAPI documentation tags.
5. **Formalized Test Suite (`tests/`)**:
   - Moved [test_ml_model_load.py](file:///d:/ProjectFiles/trend-analysis-engine/tests/test_ml_model_load.py) into `tests/`, updated relative model artifact paths, and resolved Windows console encoding collisions.

---

## 2. Active Verification Results
- **ML Integrity Test**: `.\venv\Scripts\python.exe tests\test_ml_model_load.py` passed with `Model loaded successfully [OK]`, confirming all model classes and attribute encoders load from `ml/models/`.
- **Route Registration Check**: Confirmed clean importing of `app.main:app` and verified exact preservation of all 20 REST API endpoint paths.

---

## 3. Current Directory Layout
```
trend-analysis-engine/
├── app/                            # Modularized FastAPI Backend Engine
│   ├── main.py                     # Application Bootstrapper (<30 lines)
│   ├── models.py                   # SQLAlchemy ORM Models
│   ├── schemas.py                  # Pydantic Schemas
│   ├── core/                       # Database sessions & filtering rules
│   ├── services/                   # ML inference & analytical formulas
│   └── routers/                    # Functional API route controllers
├── ml/models/                      # Pre-trained ML binary (.pkl) files
├── tests/                          # Automated testing suite
├── trend-data-collector/           # Independent Data Scraping & Ingestion Service
└── trend_analysis_app/             # Flutter Mobile & Web Client
```

---

## 4. Upcoming Milestone: Hybrid Two-Tier Scraper Architecture

We are advancing the **`trend-data-collector/`** microservice from basic DOM scraping (`requests` + `BeautifulSoup`) to a **Hybrid Two-Tier Ingestion Engine** targeting **26 top Sri Lankan women's fashion e-commerce platforms**.

### Key Architectural Pillars:
1. **Tier 1: Shopify Direct JSON Pipeline (High-Velocity Modern Boutiques)**
   - Leveraging the *"Shopify Advantage"* (`/products.json?limit=250`) for brands like *ZigZag, Mimosa, Chenara Dodge, Arienti, Lurreli, JoeY Clothing*, and *Kelly Felder*.
   - Zero HTML parsing; extracts exact timestamps, high-res CDN garment imagery, variants, and semantic design tags instantly.
2. **Tier 2: Crawl4AI Headless & Schema Extraction (Mass-Market & Department Stores)**
   - Using automated browser contexts (`Crawl4AI` + Playwright) for JavaScript SPAs and enterprise portals (*Odel, Cool Planet, Nolimit, House of Fashions, Fashion Bug, Mondy, Aviraté*).
   - Extracts structured Pydantic schemas natively while bypassing anti-bot mechanisms and triggering lazy-loading image grids.
3. ** downstream Integration**:
   - Extracted product metadata feeds directly into the FastAPI backend (`trend_observations` table) and sets up high-resolution image arrays for future **YOLOv8 silhouette & K-Means color clustering** analysis.
