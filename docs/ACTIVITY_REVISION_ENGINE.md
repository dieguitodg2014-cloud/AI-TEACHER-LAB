# Activity Revision Engine

## Purpose

The Activity Revision Engine closes the generation-validation loop without allowing the generator to redefine the pedagogical decision.

## Flow

1. Generate activity from an immutable `ActivityGenerationContract`.
2. Validate observable properties with `ActivityValidator`.
3. If rejected, create a `RevisionContract` containing failures and fields that must be preserved.
4. Send the revision contract to a provider-neutral reviser.
5. Validate the revised activity against the original contract.
6. Stop on acceptance or after the configured maximum number of attempts.

## Safety rules

- The original pedagogical contract is immutable during revision.
- A rejected activity is never accepted by score alone.
- Revision is bounded by `max_attempts`.
- If no reviser is available, the engine stops with `REVISION_PROVIDER_REQUIRED`.
- If the contract itself is invalid, the engine stops with `CONTRACT_INVALID`.
- The engine records every attempt and its failures for observability.

## Architectural boundary

The revision engine does not know whether the reviser is an LLM, NotebookLM, a local model, or another provider. Provider selection remains outside this component.
