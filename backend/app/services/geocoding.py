from app.providers.routing import (
    GeocodingProvider,
    GeocodingProviderError,
)
from app.schemas.routes import DestinationSearchResponse


class GeocodingService:
    """Coordinates validated destination search with a provider adapter."""

    max_results = 5

    def __init__(self, provider: GeocodingProvider):
        self.provider = provider

    async def search(self, query: str) -> DestinationSearchResponse:
        normalized_query = query.strip()
        if len(normalized_query) < 2:
            raise ValueError("Destination search requires at least 2 characters.")
        if len(normalized_query) > 200:
            raise ValueError("Destination search is limited to 200 characters.")
        try:
            suggestions = await self.provider.search(normalized_query)
        except GeocodingProviderError:
            raise
        except Exception as exc:
            raise GeocodingProviderError("External geocoding provider request failed") from exc
        results = suggestions[: self.max_results]
        return DestinationSearchResponse(results=results, count=len(results))
