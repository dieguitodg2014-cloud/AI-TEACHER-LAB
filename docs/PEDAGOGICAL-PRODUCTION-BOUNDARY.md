# Pedagogical–Production Boundary

AI Teacher Lab separates the decision to produce a resource from the provider
that produces it.

## Rule

Only an approved `LearningPlanDecision` plus `ResourceDecision` may authorize a
`RESOURCE_PRODUCTION` `TaskPacket`.

The authorization boundary checks:

- the resource action is one of `CREATE`, `REUSE`, or `ADAPT`;
- the learning-plan objective matches the active context objective;
- the task packet can be constructed and passes the resource task contract.

The resulting `ResourceProductionAuthorization` records the decision IDs and
purpose alongside the authorized task.

## Provider responsibility

A provider receives the authorized task downstream. It may produce or revise the
requested artifact, but it must not decide whether a resource is pedagogically
needed, change the objective, or redefine the approved task.

## Failure behavior

A failed authorization is deterministic and returns errors without invoking a
provider. This keeps pedagogical decision-making upstream of production and
makes the production boundary auditable.

## Relationship to regression protection

Regression protection remains responsible for preventing resource revisions from
driving protected properties backward. The authorization boundary is earlier: it
prevents an unapproved pedagogical decision from entering production in the first
place.
