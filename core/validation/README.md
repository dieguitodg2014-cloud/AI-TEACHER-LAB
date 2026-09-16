# Independent Lesson Validator

The lesson validator is an independent pedagogical gate between lesson generation and resource production.

## Boundary

`TaskPacket` is authoritative. Generated lesson content is evidence to evaluate, not a source of truth for level, audience, objective, duration, constraints, or quality criteria.

The validator may return:

- `READY` — no material structural issue was found.
- `REVISION_REQUIRED` — the lesson has bounded, actionable issues that can be revised and revalidated.
- `CRITICAL_FAILURE` — a critical contract failure requires the existing handoff path.

Semantic validation can be supplied by an external validator (for example, a VLM Run skill) through `LessonQualityValidator`; this module provides the provider-neutral contract and deterministic checks that do not depend on an external model.

Resource production and `ResourceValidationResult` remain downstream and separate.
