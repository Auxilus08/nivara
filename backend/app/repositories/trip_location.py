from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import SafeTripLocation
from app.schemas.routes import Coordinate


class SafeTripLocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, location: SafeTripLocation) -> SafeTripLocation:
        self.session.add(location)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def get_latest_for_trip(self, trip_id: UUID) -> SafeTripLocation | None:
        statement = (
            select(SafeTripLocation)
            .where(SafeTripLocation.trip_id == trip_id)
            .order_by(
                SafeTripLocation.recorded_at.desc(),
                SafeTripLocation.received_at.desc(),
                SafeTripLocation.id.desc(),
            )
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def distance_from_route_meters(
        self,
        location: SafeTripLocation,
        coordinates: Sequence[Coordinate],
    ) -> float:
        if len(coordinates) < 2:
            raise ValueError("planned route geometry requires at least two coordinates")
        line_wkt = "LINESTRING(" + ", ".join(
            f"{coordinate.longitude} {coordinate.latitude}" for coordinate in coordinates
        ) + ")"
        route_line = func.ST_GeomFromText(line_wkt, 4326)
        # ST_DistanceSphere accepts the stored geometry directly and returns
        # metres. Casting a GeoAlchemy WKBElement to Geography through
        # asyncpg can make PostgreSQL parse the bound WKB bytes as WKT.
        statement = select(func.ST_DistanceSphere(location.location, route_line))
        result = await self.session.execute(statement)
        distance = result.scalar_one()
        return float(distance)
