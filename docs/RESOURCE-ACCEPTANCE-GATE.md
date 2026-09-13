# Resource Acceptance Gate

The resource pipeline now has an explicit boundary between production and delivery:

`Approved TaskPacket -> Provider -> Produced Resource -> Resource QC -> Resource Acceptance Gate -> Delivery`

## Rules

1. The provider executes only the approved TaskPacket.
2. `PRODUCED` is an execution status, not an acceptance decision.
3. `validate_resource_output()` checks the returned resource against the TaskPacket.
4. `ResourceAcceptanceGate` converts QC into the downstream decision `ACCEPT`, `REVISION_REQUIRED`, `REJECT_AND_REDESIGN`, or `HUMAN_HANDOFF`.
5. Only `ACCEPT` returns the resource as a deliverable result from the production pipeline.
6. A provider cannot mark an output `READY` and bypass QC or acceptance.
7. Revision or redesign must preserve the approved TaskPacket; the resource layer does not redefine pedagogy.

## Integration point

Use `execute_resource_production_pipeline()` when the system wants the complete provider -> QC -> acceptance path. The lower-level `execute_resource_provider()` remains available for provider execution tests and integrations that intentionally stop at production.
