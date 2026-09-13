# Resource Task Contract

## Purpose

The Resource Task Contract is the provider-neutral boundary between Bionic's pedagogical resource decision and any resource producer.

The existing `TaskPacket` remains the transport model. `ResourceTaskContractValidator` makes the minimum invariants explicit before execution.

## Governing rule

A provider receives an approved task. It does not decide whether the resource is needed, redefine the objective, change the learner level, or change the requested resource type.

## Required invariants

- `task_type` must be `RESOURCE_PRODUCTION`.
- `task_id` must be present.
- `objective` must be present.
- `level` must be one of A0, A1, A2, B1, or B2.
- `required_output` must identify the approved resource type.
- At least one quality criterion must be supplied.
- The task should normally enter production with status `PENDING`.

## Production boundary

```text
Pedagogical Plan
      |
      v
Resource Decision
      |
      v
Resource TaskPacket
      |
      v
ResourceTaskContractValidator
      |
      +---- INVALID -> stop / handoff
      |
      +---- VALID
             |
             v
        Tool Selection
             |
             v
      Resource Provider
```

## Provider neutrality

The contract intentionally contains no NotebookLM, Canva, Gemini, or other provider-specific instruction. Provider-specific adapters consume the same approved task.

## Output boundary

A producer's result is not automatically trusted. `ResourceOutputValidator` checks the produced resource against the approved TaskPacket before the resource can be marked `READY`.

Therefore the complete resource circuit is:

`Decision -> Task Contract -> Tool Selection -> Production -> Output QC -> READY`

This prevents tool choice from becoming pedagogical authority and prevents produced resources from bypassing quality control.
