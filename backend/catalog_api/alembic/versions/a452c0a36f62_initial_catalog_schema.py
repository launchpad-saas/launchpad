
"""initial catalog schema

Revision ID: a452c0a36f62
Revises:
Create Date: 2026-11-06 15:34:15.196564
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a452c0a36f62"

down_revision: Union[str, None] = None

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


SCHEMA = "acme"


def upgrade() -> None:

    # Categories table
    op.create_table(
        "categories",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "slug",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.String(length=2000),
            nullable=True,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),

        schema=SCHEMA,
    )

    # Categories indexes
    op.create_index(
        op.f("ix_categories_slug"),
        "categories",
        ["slug"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_index(
        op.f("ix_categories_tenant_id"),
        "categories",
        ["tenant_id"],
        unique=False,
        schema=SCHEMA,
    )

    # Products table
    op.create_table(
        "products",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "category_id",
            sa.UUID(),
            nullable=True,
        ),

        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "slug",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.String(length=5000),
            nullable=True,
        ),

        sa.Column(
            "sku",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "price_cents",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),

        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        # Schema-qualified foreign key
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["acme.categories.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint("id"),

        schema=SCHEMA,
    )

    # Products indexes
    op.create_index(
        op.f("ix_products_category_id"),
        "products",
        ["category_id"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_index(
        op.f("ix_products_name"),
        "products",
        ["name"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_index(
        op.f("ix_products_sku"),
        "products",
        ["sku"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_index(
        op.f("ix_products_slug"),
        "products",
        ["slug"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_index(
        op.f("ix_products_tenant_id"),
        "products",
        ["tenant_id"],
        unique=False,
        schema=SCHEMA,
    )


def downgrade() -> None:

    # Drop products indexes
    op.drop_index(
        op.f("ix_products_tenant_id"),
        table_name="products",
        schema=SCHEMA,
    )

    op.drop_index(
        op.f("ix_products_slug"),
        table_name="products",
        schema=SCHEMA,
    )

    op.drop_index(
        op.f("ix_products_sku"),
        table_name="products",
        schema=SCHEMA,
    )

    op.drop_index(
        op.f("ix_products_name"),
        table_name="products",
        schema=SCHEMA,
    )

    op.drop_index(
        op.f("ix_products_category_id"),
        table_name="products",
        schema=SCHEMA,
    )

    # Drop products table
    op.drop_table(
        "products",
        schema=SCHEMA,
    )

    # Drop categories indexes
    op.drop_index(
        op.f("ix_categories_tenant_id"),
        table_name="categories",
        schema=SCHEMA,
    )

    op.drop_index(
        op.f("ix_categories_slug"),
        table_name="categories",
        schema=SCHEMA,
    )

    # Drop categories table
    op.drop_table(
        "categories",
        schema=SCHEMA,
    )
