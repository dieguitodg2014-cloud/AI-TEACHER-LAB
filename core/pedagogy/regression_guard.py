"""Bionic MVP-002: regression protection for activity revisions.

A revision must preserve previously satisfied contract properties and may not
replace one failure with a newly introduced contract failure.
"""
from dataclasses import dataclass
from typing import Any, Mapping

from .activity_contract import ActivityGenerationContract
from .activity_validator import ActivityValidator


@dataclass(frozen=True)
class RegressionResult:
    """Comparison between validation states before and after revision."""

    regression: bool
    introduced_failures: tuple[str, ...] = ()
    resolved_failures: tuple[str, ...] = ()
    remaining_failures: tuple[str, ...] = ()


class ActivityRegressionGuard:
    """Reject revisions that introduce new validation failures."""

    def __init__(self, validator: ActivityValidator | None = None):
        self.validator = validator or ActivityValidator()

    def compare(
        self,
        previous_activity: Mapping[str, Any],
        revised_activity: Mapping[str, Any],
        contract: ActivityGenerationContract,
    ) -> RegressionResult:
        previous = self.validator.validate(dict(previous_activity), contract)
        revised = self.validator.validate(dict(revised_activity), contract)

        before = set(previous.failures)
        after = set(revised.failures)
        introduced = tuple(sorted(after - before))
        resolved = tuple(sorted(before - after))

        return RegressionResult(
            regression=bool(introduced),
            introduced_failures=introduced,
            resolved_failures=resolved,
            remaining_failures=tuple(sorted(after)),
        )
