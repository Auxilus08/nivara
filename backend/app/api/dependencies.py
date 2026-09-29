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
from app.core.config import get_settings
from app.demo import (
    DemoAssociationRepository,
    DemoCheckInRepository,
    DemoContactRepository,
    DemoEmergencyRepository,
    DemoIncidentRepository,
    DemoLocationRepository,
    DemoPreferenceRepository,
    DemoSafeTripRepository,
)


async def get_incident_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> IncidentRepository | DemoIncidentRepository:
    return DemoIncidentRepository() if get_settings().demo_mode else IncidentRepository(session)


async def get_emergency_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> EmergencyRepository | DemoEmergencyRepository:
    return DemoEmergencyRepository() if get_settings().demo_mode else EmergencyRepository(session)


async def get_safe_trip_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> SafeTripRepository | DemoSafeTripRepository:
    return DemoSafeTripRepository() if get_settings().demo_mode else SafeTripRepository(session)


async def get_safe_trip_location_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> SafeTripLocationRepository | DemoLocationRepository:
    return DemoLocationRepository() if get_settings().demo_mode else SafeTripLocationRepository(session)


async def get_safe_trip_check_in_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> SafeTripCheckInRepository | DemoCheckInRepository:
    return DemoCheckInRepository() if get_settings().demo_mode else SafeTripCheckInRepository(session)


async def get_trusted_contact_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> TrustedContactRepository | DemoContactRepository:
    return DemoContactRepository() if get_settings().demo_mode else TrustedContactRepository(session)


async def get_trusted_contact_sharing_preference_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> TrustedContactSharingPreferenceRepository | DemoPreferenceRepository:
    return DemoPreferenceRepository() if get_settings().demo_mode else TrustedContactSharingPreferenceRepository(session)


async def get_safe_trip_trusted_contact_repository(
    session: AsyncSession | None = Depends(get_db_session),
) -> SafeTripTrustedContactRepository | DemoAssociationRepository:
    return DemoAssociationRepository() if get_settings().demo_mode else SafeTripTrustedContactRepository(session)
