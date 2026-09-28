from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base metadata shared by persistence models and Alembic."""
