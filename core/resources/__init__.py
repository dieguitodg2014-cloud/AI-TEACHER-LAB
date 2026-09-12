"""Pedagogical resource decision and output-validation components."""

from .decision_engine import apply_resource_decision, decide_resource
from .output_validator import ResourceValidationResult, validate_resource_output

__all__ = [
    "ResourceValidationResult",
    "apply_resource_decision",
    "decide_resource",
    "validate_resource_output",
]
