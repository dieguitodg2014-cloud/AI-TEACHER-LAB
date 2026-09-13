# NotebookLM Resource Provider Boundary

## Purpose

NotebookLM is a downstream resource producer. It is not a pedagogical authority.

The pedagogical system must decide first:

1. learner level and objective
2. activity pattern and evidence
3. whether a specialized resource is necessary
4. resource type and constraints
5. approved Resource TaskPacket

Only then may tool selection choose NotebookLM.

## Contract

NotebookLM may receive an approved `TaskPacket` whose `task_type` is
`RESOURCE_PRODUCTION` and whose capabilities are satisfied by
`resource_generation`.

The provider may produce or adapt the requested resource, but it may not:

- change CEFR level
- change the learning objective
- decide that a resource is pedagogically necessary
- replace the approved interaction or evidence requirements
- bypass resource QC

## Routing rule

`select_resource_tool()` selects from capability-qualified tools. NotebookLM
can therefore be represented as a `ToolCandidate` with `resource_generation`
capability without hard-coding it into the pedagogical decision engine.

If no eligible provider is available, the system must use the existing
`HUMAN_HANDOFF` path rather than silently changing the task.

## MVP status

The repository now contains a routing guard test proving that NotebookLM can
be selected when an approved resource task exists and cannot be selected when
no resource task exists.

Actual NotebookLM execution remains an integration step requiring an authorized
provider/connector. This document intentionally separates routing from provider
execution.
