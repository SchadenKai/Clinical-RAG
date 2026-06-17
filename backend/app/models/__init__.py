"""SQLAlchemy ORM models.

Importing models here ensures they are registered on ``Base.metadata`` for
Alembic autogeneration and ``create_all`` in tests.
"""

from app.models.agent import Agent

__all__ = ["Agent"]
