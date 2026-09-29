from dataclasses import dataclass

from app.schemas.routes import RouteCandidate, RouteMode


@dataclass(frozen=True)
class RouteModeWeights:
    time: float
    safety: float


DEFAULT_MODE_WEIGHTS = {
    RouteMode.FASTEST: RouteModeWeights(time=0.90, safety=0.10),
    RouteMode.BALANCED: RouteModeWeights(time=0.55, safety=0.45),
    RouteMode.SAFETY_PRIORITY: RouteModeWeights(time=0.25, safety=0.75),
}

MODE_DESCRIPTIONS = {
    RouteMode.FASTEST: "Prioritizes shorter travel time while retaining available safety indicators.",
    RouteMode.BALANCED: "Balances travel time with available safety indicators.",
    RouteMode.SAFETY_PRIORITY: "Places greater weight on available safety indicators than travel time.",
}


COMPARISON_DISCLAIMER = (
    "Route selection reflects the configured travel-time and contextual incident "
    "objectives. It is not a guarantee of safety."
)
NO_SAFETY_CONTEXT_EXPLANATION = (
    "Incident-derived safety indicators were unavailable for all candidates; "
    "selection used normalized travel time only."
)
SAFETY_PRIORITY_TIE_COST_DELTA = 2.0


class RouteComparisonService:
    """Compare normalized candidates without depending on providers or databases."""

    def __init__(self, mode_weights: dict[RouteMode, RouteModeWeights] | None = None):
        self.mode_weights = mode_weights or DEFAULT_MODE_WEIGHTS

    def compare(self, routes: list[RouteCandidate], mode: RouteMode) -> tuple[list[RouteCandidate], str | None]:
        if not routes:
            return [], None

        max_duration = max(route.estimated_duration_seconds for route in routes)
        has_complete_safety = all(route.safety_assessment is not None for route in routes)
        weights = self.mode_weights[mode]
        enriched: list[RouteCandidate] = []
        for route in routes:
            normalized_time = (
                (route.estimated_duration_seconds / max_duration) * 100
                if max_duration > 0
                else 0.0
            )
            if has_complete_safety:
                safety_score = route.safety_assessment.risk_score
                cost = weights.time * normalized_time + weights.safety * safety_score
                explanation = (
                    f"Normalized travel-time score {normalized_time:.1f} and contextual "
                    f"incident score {safety_score} were combined for {mode.value}."
                )
            else:
                safety_score = None
                cost = normalized_time
                explanation = NO_SAFETY_CONTEXT_EXPLANATION
            enriched.append(
                route.model_copy(
                    update={
                        "normalized_travel_score": round(normalized_time, 2),
                        "comparison_cost": round(cost, 2),
                        "comparison_explanation": explanation,
                    }
                )
            )

        selected = min(
            enriched,
            key=lambda route: (route.comparison_cost or 0.0, route.estimated_duration_seconds, route.route_id),
        )

        # Provider alternatives can share the same incident corridor and
        # therefore receive the same contextual risk estimate. For Safety
        # Priority, when that risk is tied and the weighted costs are close,
        # prefer the shorter physical route so the mode remains meaningfully
        # differentiated without fabricating a safety signal. Exact cost ties
        # retain the normal duration/id ordering for backwards compatibility.
        if mode == RouteMode.SAFETY_PRIORITY and has_complete_safety:
            selected_risk = selected.safety_assessment.risk_score  # type: ignore[union-attr]
            close_same_risk = [
                route
                for route in enriched
                if route.safety_assessment is not None
                and route.safety_assessment.risk_score == selected_risk
                and (route.comparison_cost or 0.0) > (selected.comparison_cost or 0.0)
                and (route.comparison_cost or 0.0) - (selected.comparison_cost or 0.0)
                <= SAFETY_PRIORITY_TIE_COST_DELTA
            ]
            if close_same_risk:
                selected = min(
                    [selected, *close_same_risk],
                    key=lambda route: (
                        route.distance_meters,
                        route.estimated_duration_seconds,
                        route.route_id,
                    ),
                )
        return enriched, selected.route_id
