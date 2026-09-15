# Activity Regression Protection

Bionic must not accept a revision merely because one previous failure disappeared.
A revision is evaluated against the same immutable pedagogical contract.

## Rule

Given a previous rejected activity and a revised activity:

- `introduced_failures = revised_failures - previous_failures`
- `resolved_failures = previous_failures - revised_failures`
- Any introduced failure is a regression.
- A regression is a blocking outcome for the current revision attempt.

## Why this matters

A generator may fix a speaking-output problem by changing interaction, duration,
level, target language, or another protected property. Regression protection makes
that drift observable and blocks the revised activity.

## Boundary

`ActivityRegressionGuard` is deterministic and provider-neutral. It does not
choose a generator or reviser and does not change the pedagogical contract.
