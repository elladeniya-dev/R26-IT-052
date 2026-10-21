# Senu Outfit Compatibility Engine

FastAPI backend service for Module 04 of the Smart Fashion Assistant research project.

## Overview

The Outfit Compatibility Engine generates complete outfit suggestions around a clothing item selected by the user. It works after the recommendation engine: when a user selects one recommended product, this service finds compatible items from other categories and returns ranked outfit combinations.

The service does not sell products directly. It stores product metadata from external fashion websites and returns product links that redirect users to the original stores.

## System Flow

```text
Koji Recommendation Engine
    -> User selects recommended item
    -> Senu Outfit Compatibility Engine
    -> Compatible outfit suggestions
    -> Flutter app displays outfits
```

## Backend Layout

```text
server/
|-- app/
|   |-- main.py
|   |-- routers/
|   |-- compatibility.py
|   |-- outfit_generator.py
|   |-- outfit_storage.py
|   |-- models.py
|   |-- schemas.py
|   |-- database.py
|   `-- config.py
|-- ml_models/
|-- scripts/
|   `-- seed_products.py
|-- tests/
|   |-- test_compatibility.py
|   `-- test_outfit_generator.py
`-- requirements.txt
```

## Local Setup

Create a `.env` file in this directory with `DATABASE_URL`, then run:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/s_apply_migrations.py
uvicorn app.main:app --reload --port 8004
```

Run migrations from this directory after configuring `DATABASE_URL` in `.env`.
The migration runner applies numbered SQL files to the Senu database only and
tracks completed migrations in `s_schema_migrations`. The image embedding
migration is safe to rerun. After syncing new Koji products, run
`python scripts/s_generate_embeddings.py` to backfill their embeddings. The
product sync clears an existing embedding when a product's image URL changes;
run the backfill after each sync so the ML scorer uses the current image. To do
both steps in one command, use
`python scripts/s_sync_koji_products.py --with-embeddings` (the first embedding
run may download the FashionCLIP model).

## Useful Commands

```bash
python scripts/seed_products.py
python tests/test_outfit_generator.py
```

The service prevents duplicate saved outfits for the same user and selected item, stores each generation request with a batch ID, and exposes the latest outfit batch through `GET /outfits/{user_id}/latest`.
