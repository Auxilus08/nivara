---
name: agent-handoff
description: Maintain Nivara multi-agent development state, task tracking, documentation, testing, git hygiene, and agent-to-agent handoff.
---

# Nivara Agent Handoff

## Purpose

Ensure that another agent can continue development without relying on chat history.

---

## Before Finishing

Run:

1. git status
2. git diff
3. relevant tests
4. relevant build/type checks

---

## Update

Update:

docs/tasks.md
docs/transfer.md

Also update:

docs/architecture.md
docs/api.md
docs/flow.md
docs/decisions.md

when relevant.

---

## Transfer Must Include

- current status
- last completed task
- files changed
- tests run
- verification commands
- known issues
- blockers
- next exact task

---

## Rules

- Do not claim tests passed unless actually run.
- Do not hide known failures.
- Do not overwrite another agent's work unnecessarily.
- Keep commits focused.
- Inspect git diff before handoff.
- Repository state is the source of truth.
