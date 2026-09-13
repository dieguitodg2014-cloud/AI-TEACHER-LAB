# Activity Acceptance Gate

The acceptance gate is the final pedagogical boundary before an activity can be handed to downstream resource, formatting, or delivery systems.

## Decisions

- `ACCEPT`: the activity satisfies the contract and validator.
- `REVISION_REQUIRED`: the activity fails validation but the revision budget remains.
- `REJECT_AND_REDESIGN`: the contract is invalid or a revision introduces a regression.
- `HUMAN_HANDOFF`: the activity still fails after the allowed revision attempts.

## Authority

The gate does not generate content. It evaluates evidence produced by upstream components and provides one explicit decision to downstream systems.

## Architectural principle

No external generator, resource tool, or presentation layer may bypass this gate and treat generated content as pedagogically accepted.
