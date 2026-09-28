"""Persistence adapters; feature agents should add repositories by domain."""

from app.repositories.incident import IncidentRepository

__all__ = ["IncidentRepository"]
