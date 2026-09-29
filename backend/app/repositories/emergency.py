from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emergency import Emergency, EmergencyStatus


class EmergencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, emergency: Emergency) -> Emergency:
        self.session.add(emergency)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(emergency)
        return emergency

    async def get_by_id(self, emergency_id: UUID) -> Emergency | None:
        return await self.session.get(Emergency, emergency_id)

    async def get_active_for_trip(self, trip_id: UUID) -> Emergency | None:
        statement = select(Emergency).where(
            Emergency.trip_id == trip_id,
            Emergency.status.in_((EmergencyStatus.ACTIVE.value, EmergencyStatus.ACKNOWLEDGED.value)),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def update(self, emergency: Emergency) -> Emergency:
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(emergency)
        return emergency
