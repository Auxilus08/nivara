from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.incident import IncidentRepository
from app.repositories.emergency import EmergencyRepository
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.repositories.trip_check_in import SafeTripCheckInRepository
from app.repositories.trusted_contact import (
    TrustedContactRepository,
    TrustedContactSharingPreferenceRepository,
)
from app.repositories.trip_trusted_contact import SafeTripTrustedContactRepository


async def get_incident_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IncidentRepository:
    return IncidentRepository(session)


async def get_emergency_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmergencyRepository:
    return EmergencyRepository(session)


async def get_safe_trip_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SafeTripRepository:
    return SafeTripRepository(session)


async def get_safe_trip_location_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SafeTripLocationRepository:
    return SafeTripLocationRepository(session)


async def get_safe_trip_check_in_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SafeTripCheckInRepository:
    return SafeTripCheckInRepository(session)


async def get_trusted_contact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TrustedContactRepository:
    return TrustedContactRepository(session)


async def get_trusted_contact_sharing_preference_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TrustedContactSharingPreferenceRepository:
    return TrustedContactSharingPreferenceRepository(session)


async def get_safe_trip_trusted_contact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SafeTripTrustedContactRepository:
    return SafeTripTrustedContactRepository(session)
