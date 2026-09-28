---
name: security4her-backend
description: Build and maintain the Nivara FastAPI backend, services, repositories, APIs, validation, security, geospatial operations, and tests.
---

# Nivara Backend Skill

## Purpose

Use this skill when implementing or modifying the FastAPI backend.

---

## Architecture

Prefer:

API
 ->
Service
 ->
Repository
 ->
Database

---

## API Layer

Responsible for:

- HTTP routing
- request validation
- authentication
- authorization
- response serialization
- error mapping

Keep route handlers thin.

---

## Service Layer

Responsible for:

- business rules
- safety calculations
- trip state transitions
- emergency state transitions
- orchestration

---

## Repository Layer

Responsible for:

- database queries
- persistence
- PostGIS operations
- spatial filtering

---

## Rules

- Inspect before editing.
- Preserve existing interfaces.
- Use typed request/response models.
- Validate external input.
- Keep secrets out of source code.
- Treat location as sensitive.
- Avoid unnecessary logging of precise locations.
- Use appropriate HTTP status codes.
- Write meaningful tests.
- Keep business logic out of route handlers.
- Update docs/api.md when API contracts change.
- Update docs/tasks.md when tasks are completed.
- Update docs/transfer.md before handoff.

---

## Security

Never trust:

- client-provided authorization
- client-provided user IDs
- client-provided permissions
- unvalidated AI output

Authorization must be enforced server-side.

---

## Testing

Important backend tests include:

- service logic
- safety calculations
- state transitions
- API validation
- authorization
- repository behavior where practical
