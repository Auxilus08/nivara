from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import SafeTripLocation


class SafeTripLocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, location: SafeTripLocation) -> SafeTripLocation:
        self.session.add(location)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(location)
        return location
