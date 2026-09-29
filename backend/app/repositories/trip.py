from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import SafeTrip


class SafeTripRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, trip: SafeTrip) -> SafeTrip:
        self.session.add(trip)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(trip)
        return trip

    async def get_by_id(self, trip_id: UUID) -> SafeTrip | None:
        return await self.session.get(SafeTrip, trip_id)

    async def update(self, trip: SafeTrip) -> SafeTrip:
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(trip)
        return trip
