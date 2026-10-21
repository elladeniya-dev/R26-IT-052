-- Add the cached FashionCLIP vector used by Senu's outfit compatibility model.
-- Safe to apply to an existing PostgreSQL database and safe to rerun.
ALTER TABLE IF EXISTS products
    ADD COLUMN IF NOT EXISTS image_embedding JSON;
