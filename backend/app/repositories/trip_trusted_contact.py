from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trusted_contact import TrustedContact
from app.models.trip_trusted_contact import SafeTripTrustedContact


class SafeTripTrustedContactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, trip_id: UUID, contact_id: UUID) -> SafeTripTrustedContact | None:
        statement = select(SafeTripTrustedContact).where(
            SafeTripTrustedContact.safe_trip_id == trip_id,
            SafeTripTrustedContact.trusted_contact_id == contact_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, association: SafeTripTrustedContact) -> SafeTripTrustedContact:
        self.session.add(association)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(association)
        return association

    async def list_for_trip(
        self, trip_id: UUID
    ) -> list[tuple[SafeTripTrustedContact, TrustedContact]]:
        statement = (
            select(SafeTripTrustedContact, TrustedContact)
            .join(TrustedContact, TrustedContact.id == SafeTripTrustedContact.trusted_contact_id)
            .where(
                SafeTripTrustedContact.safe_trip_id == trip_id,
                TrustedContact.is_active.is_(True),
            )
            .order_by(SafeTripTrustedContact.created_at.desc(), TrustedContact.id.desc())
        )
        result = await self.session.execute(statement)
        return list(result.all())

    async def delete(self, association: SafeTripTrustedContact) -> None:
        await self.session.delete(association)
        await self.session.commit()
