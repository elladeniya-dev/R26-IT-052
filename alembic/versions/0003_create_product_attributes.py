"""create product_attributes

One row per (product, attribute type, value) — replaces ';'-joined multi-value
strings. Raw labels are never canonicalised: merging synonyms (navy/dark blue,
spandex/lycra/elastane) was tested and measurably lowered IC (architecture
spec §2).

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-30
"""
import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

ATTR_TYPE_VALUES = (
    "category", "color", "pattern", "fabric",
    "sleeve_length", "garment_length", "neckline", "style_detail",
)


def upgrade() -> None:
    # create_table's own before_create hook creates the enum type as part of
    # creating this table — do not also create it explicitly beforehand,
    # that hook always runs with checkfirst=False and errors on a duplicate.
    attr_type_enum = sa.Enum(*ATTR_TYPE_VALUES, name="attr_type")

    op.create_table(
        "product_attributes",
        sa.Column(
            "product_id", sa.String(),
            sa.ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("attr_type", attr_type_enum, primary_key=True),
        sa.Column("attr_value", sa.String(), primary_key=True),  # lowercase, trimmed, RAW label
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_product_attributes_type_value", "product_attributes", ["attr_type", "attr_value"])


def downgrade() -> None:
    op.drop_table("product_attributes")
    sa.Enum(name="attr_type").drop(op.get_bind(), checkfirst=True)
