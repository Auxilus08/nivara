from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import SafeTripCheckIn


class SafeTripCheckInRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, check_in: SafeTripCheckIn) -> SafeTripCheckIn:
        self.session.add(check_in)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(check_in)
        return check_in
