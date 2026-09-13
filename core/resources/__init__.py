"""Pedagogical resource decision and output-validation components."""

from .decision_engine import apply_resource_decision, decide_resource
from .output_validator import ResourceValidationResult, validate_resource_output
from .task_contract import ResourceTaskContractValidator, ResourceTaskValidationResult

__all__ = [
    "ResourceTaskContractValidator",
    "ResourceTaskValidationResult",
    "ResourceValidationResult",
    "apply_resource_decision",
    "decide_resource",
    "validate_resource_output",
]
