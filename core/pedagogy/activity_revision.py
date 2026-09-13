"""Bionic MVP-002: bounded revision loop with regression protection.

The revision engine never changes the pedagogical contract. It delegates the
actual rewrite to a provider-neutral reviser, re-validates every revision, and
rejects revisions that introduce new validation failures.
"""
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .activity_pipeline import ActivityPipeline, RevisionContract
from .activity_contract import ActivityGenerationContract
from .regression_guard import ActivityRegressionGuard


@dataclass(frozen=True)
class RevisionAttempt:
    """Observable record of one generation/revision attempt."""

    attempt_number: int
    status: str
    failures: tuple[str, ...] = ()
    regression: bool = False
    introduced_failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActivityRevisionResult:
    """Bounded revision outcome."""

    accepted: bool
    activity: Mapping[str, Any] | None
    attempts: tuple[RevisionAttempt, ...]
    revision_contract: RevisionContract | None
    stop_reason: str


class ActivityRevisionEngine:
    """Retry rejected activities without allowing pedagogical drift or regression."""

    def __init__(
        self,
        pipeline: ActivityPipeline | None = None,
        regression_guard: ActivityRegressionGuard | None = None,
        max_attempts: int = 3,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.pipeline = pipeline or ActivityPipeline()
        self.regression_guard = regression_guard or ActivityRegressionGuard()
        self.max_attempts = max_attempts

    def run(
        self,
        contract: ActivityGenerationContract,
        generator: Callable[[ActivityGenerationContract], Mapping[str, Any]],
        reviser: Callable[[RevisionContract], Mapping[str, Any]] | None = None,
    ) -> ActivityRevisionResult:
        attempts: list[RevisionAttempt] = []
        current_activity: Mapping[str, Any] | None = None
        revision_contract: RevisionContract | None = None

        for attempt_number in range(1, self.max_attempts + 1):
            if attempt_number == 1:
                result = self.pipeline.run(contract, generator)
            else:
                if reviser is None or revision_contract is None:
                    return ActivityRevisionResult(
                        False, current_activity, tuple(attempts), revision_contract,
                        "REVISION_PROVIDER_REQUIRED",
                    )
                revised_activity = reviser(revision_contract)
                if current_activity is not None:
                    regression = self.regression_guard.compare(
                        current_activity, revised_activity, contract
                    )
                    if regression.regression:
                        failures = regression.introduced_failures
                        attempts.append(
                            RevisionAttempt(
                                attempt_number,
                                "REGRESSION_REJECTED",
                                failures,
                                True,
                                failures,
                            )
                        )
                        return ActivityRevisionResult(
                            False,
                            revised_activity,
                            tuple(attempts),
                            revision_contract,
                            "REGRESSION_DETECTED",
                        )
                result = self.pipeline.run(contract, lambda _: revised_activity)

            if result.accepted:
                attempts.append(
                    RevisionAttempt(attempt_number, result.validation.status)
                )
                return ActivityRevisionResult(
                    True, result.activity, tuple(attempts), None, "ACCEPTED"
                )

            failures = (
                result.validation.failures
                if result.validation
                else result.contract_validation.errors
            )
            attempts.append(RevisionAttempt(attempt_number, "REJECT", tuple(failures)))
            current_activity = result.activity
            revision_contract = result.revision_contract

            if revision_contract is None:
                return ActivityRevisionResult(
                    False, current_activity, tuple(attempts), None,
                    "CONTRACT_INVALID",
                )

            if attempt_number == self.max_attempts:
                return ActivityRevisionResult(
                    False, current_activity, tuple(attempts), revision_contract,
                    "MAX_ATTEMPTS_REACHED",
                )

        return ActivityRevisionResult(
            False, current_activity, tuple(attempts), revision_contract,
            "REVISION_STOPPED",
        )
