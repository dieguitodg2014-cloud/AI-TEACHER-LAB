# ResourceValidationResult immutability boundary

`ResourceValidationResult` is a validation-gate contract consumed by downstream resource handoff and return orchestration. Its decision evidence must not be mutable after validation.

The contract should therefore normalize `checks`, `feedback`, and `blocking_errors` into immutable representations while preserving ordinary dict/list representations at explicit serialization boundaries.

This is a contract-hardening change only. It does not alter validation rules, provider behavior, resource decisions, or acceptance semantics.
