"""create agents table and seed built-in agents

Revision ID: 0001_create_agents
Revises:
Create Date: 2026-06-16

"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_create_agents"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    agents_table = op.create_table(
        "agents",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "pipeline",
            sa.String(length=32),
            nullable=False,
            server_default="general",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    now = datetime.now(timezone.utc)
    op.bulk_insert(
        agents_table,
        [
            {
                "id": "general",
                "name": "General Chat",
                "description": (
                    "Versatile AI assistant for everyday tasks and general "
                    "queries."
                ),
                "prompt": "You are a helpful assistant.",
                "pipeline": "general",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "clinical_rag",
                "name": "Clinical Guidelines Agent",
                "description": (
                    "Specialized healthcare assistant grounded in CDC and WHO "
                    "guidelines."
                ),
                "prompt": (
                    "You are a clinical guidelines assistant. Answer strictly "
                    "from the retrieved CDC and WHO guideline context and cite "
                    "your sources."
                ),
                "pipeline": "clinical_rag",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("agents")
