from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trusted_contact import TrustedContact
from app.models.trusted_contact_sharing_preference import TrustedContactSharingPreference


class TrustedContactRepository:
    MAX_LIST_SIZE = 100

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, contact: TrustedContact) -> TrustedContact:
        self.session.add(contact)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def update(self, contact: TrustedContact) -> TrustedContact:
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def list_active(self) -> list[TrustedContact]:
        statement = select(TrustedContact).where(TrustedContact.is_active.is_(True)).order_by(
            TrustedContact.created_at.desc(), TrustedContact.id.desc()
        ).limit(self.MAX_LIST_SIZE)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_active_by_id(self, contact_id: UUID) -> TrustedContact | None:
        statement = select(TrustedContact).where(
            TrustedContact.id == contact_id,
            TrustedContact.is_active.is_(True),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def deactivate(self, contact: TrustedContact) -> TrustedContact:
        contact.is_active = False
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(contact)
        return contact


class TrustedContactSharingPreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_contact_id(self, contact_id: UUID) -> TrustedContactSharingPreference | None:
        statement = select(TrustedContactSharingPreference).where(
            TrustedContactSharingPreference.trusted_contact_id == contact_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self, preference: TrustedContactSharingPreference
    ) -> TrustedContactSharingPreference:
        self.session.add(preference)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(preference)
        return preference

    async def update(
        self, preference: TrustedContactSharingPreference
    ) -> TrustedContactSharingPreference:
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(preference)
        return preference
