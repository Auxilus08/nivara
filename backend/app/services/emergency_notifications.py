from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from app.models.emergency import Emergency


class EmergencyNotificationProvider(Protocol):
    async def notify(self, emergency: Emergency, contact_ids: list[UUID]) -> None:
        """Record or deliver a future emergency notification."""


@dataclass
class MockEmergencyNotificationProvider:
    """Development-only provider; it never sends SMS, email, or push messages."""

    notifications: list[dict] = field(default_factory=list)

    async def notify(self, emergency: Emergency, contact_ids: list[UUID]) -> None:
        self.notifications.append(
            {
                "emergency_id": emergency.id,
                "trip_id": emergency.trip_id,
                "contact_ids": list(contact_ids),
                "mode": "mock_demo_only",
            }
        )
