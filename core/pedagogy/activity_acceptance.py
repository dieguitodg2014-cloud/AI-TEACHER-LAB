"""Bionic MVP-002: final pedagogical acceptance gate.

This gate converts contract validation, activity validation, and revision state
into one explicit downstream decision. It does not generate or revise content.
"""
from dataclasses import dataclass
from typing import Any, Mapping

from .activity_contract import ActivityGenerationContract, ActivityContractValidator
from .activity_validator import ActivityValidator
from .regression_guard import RegressionResult


@dataclass(frozen=True)
class AcceptanceResult:
    """Final decision for downstream consumers."""

    decision: str
    reasons: tuple[str, ...] = ()
    blocking: bool = True


class ActivityAcceptanceGate:
    """Single authority for final activity acceptance."""

    def __init__(self, contract_validator=None, activity_validator=None):
        self.contract_validator = contract_validator or ActivityContractValidator()
        self.activity_validator = activity_validator or ActivityValidator()

    def evaluate(
        self,
        contract: ActivityGenerationContract,
        activity: Mapping[str, Any] | None,
        *,
        regression: RegressionResult | None = None,
        attempts: int = 1,
        max_attempts: int = 3,
    ) -> AcceptanceResult:
        contract_result = self.contract_validator.validate(contract)
        if not contract_result.valid:
            return AcceptanceResult("REJECT_AND_REDESIGN", tuple(contract_result.errors))

        if activity is None:
            return AcceptanceResult("REVISION_REQUIRED", ("No generated activity is available.",))

        validation = self.activity_validator.validate(dict(activity), contract)
        if regression is not None and regression.regression:
            return AcceptanceResult(
                "REJECT_AND_REDESIGN",
                tuple(regression.introduced_failures),
            )

        if validation.status == "PASS" or validation.status == "PASS_WITH_WARNINGS":
            return AcceptanceResult(
                "ACCEPT",
                tuple(validation.warnings),
                blocking=False,
            )

        if attempts >= max_attempts:
            return AcceptanceResult(
                "HUMAN_HANDOFF",
                tuple(validation.failures),
            )

        return AcceptanceResult("REVISION_REQUIRED", tuple(validation.failures))
