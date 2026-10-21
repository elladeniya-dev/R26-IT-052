"""create products

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-30
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("product_id", sa.String(), primary_key=True),  # brand_slug:native_id
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.brand_id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),  # normalised, H&M taxonomy
        sa.Column("raw_product_type", sa.String(), nullable=True),
        sa.Column("product_url", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("num_images", sa.SmallInteger(), nullable=True),
        sa.Column("has_rich_desc", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_tier", sa.SmallInteger(), nullable=False),
        sa.Column("first_seen", sa.Date(), nullable=False),  # set once, never updated
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
        ),
    )
    op.create_index("ix_products_brand_id", "products", ["brand_id"])
    op.create_index("ix_products_category", "products", ["category"])


def downgrade() -> None:
    op.drop_table("products")
