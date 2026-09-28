---
name: security4her-frontend
description: Build and maintain the Nivara Next.js frontend, navigation UX, map interfaces, safety indicators, Safe Trip, emergency flows, privacy controls, and responsive UI.
---

# Nivara Frontend Skill

## Stack

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

---

## Principles

Build a clear, fast and trustworthy safety interface.

Safety information should be understandable without being alarmist.

---

## Rules

- Inspect before editing.
- Reuse existing components.
- Keep components focused.
- Keep API access separated from presentation.
- Use TypeScript types for API data.
- Handle loading states.
- Handle error states.
- Handle empty states.
- Make important actions accessible.
- Avoid accidental SOS activation.
- Protect sensitive location information.
- Do not expose internal API secrets.
- Never present safety estimates as guarantees.
- Never label a location as objectively safe or dangerous.

---

## Navigation UI

Route options should make it easy to compare:

- travel time
- distance
- contextual safety indicators
- important contributing factors

Supported modes:

- Fastest
- Balanced
- Safety Priority

---

## Emergency UI

Emergency actions must be visually clear.

SOS should use an intentional activation mechanism.

Do not hide emergency actions behind confusing navigation.

---

## Testing

Test important user flows such as:

- destination search
- route selection
- Safe Trip
- deviation handling
- check-in
- SOS
- privacy controls
