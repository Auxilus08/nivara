---
name: safety-engine
description: Implement Nivara contextual safety scoring, route comparison, incident weighting, geospatial signals, explainable safety indicators, and safety heatmaps.
---

# Nivara Safety Engine

## Purpose

Estimate contextual safety indicators for routes and locations.

The engine must never claim to predict whether harm will occur.

---

## Potential Signals

- incident density
- incident recency
- incident severity
- community report confidence
- time of day
- lighting indicators
- activity indicators
- open businesses
- emergency resources
- route isolation
- historical incident activity

---

## Routing Modes

### Fastest

Travel time has the strongest influence.

### Balanced

Travel time and contextual safety indicators are balanced.

### Safety Priority

Safety indicators receive substantially higher weight while preserving reasonable travel time.

---

## Design Principles

- Keep scoring configurable.
- Keep scoring explainable.
- Separate deterministic scoring from AI.
- Avoid unsupported probabilities.
- Do not use a single report as definitive truth.
- Account for incident recency.
- Account for confidence.
- Account for time context.
- Prefer normalized inputs.

---

## Example Concept

routeCost =
    timeWeight * normalizedTravelTime
    +
    safetyWeight * normalizedSafetyRisk
    +
    isolationWeight * normalizedIsolationRisk

The implementation may evolve.

Architectural changes must be documented.
