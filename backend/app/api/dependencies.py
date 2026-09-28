from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.incident import IncidentRepository


async def get_incident_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IncidentRepository:
    return IncidentRepository(session)
