"""Explicit downstream boundary for pedagogically accepted activities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .activity_acceptance import ActivityAcceptanceGate, AcceptanceResult
from .activity_contract import ActivityGenerationContract
from .activity_revision import ActivityRevisionResult


@dataclass(frozen=True)
class AcceptedActivity:
    """A resource-safe activity that has crossed the pedagogical gate."""

    activity: Mapping[str, Any]
    contract: ActivityGenerationContract
    acceptance: AcceptanceResult


def materialize_accepted_activity(
    contract: ActivityGenerationContract,
    revision_result: ActivityRevisionResult,
    *,
    gate: ActivityAcceptanceGate | None = None,
) -> AcceptedActivity | None:
    """Return an activity only when the final acceptance decision is ACCEPT."""
    decision = revision_result.acceptance
    if decision is None:
        decision = (gate or ActivityAcceptanceGate()).evaluate(
            contract,
            revision_result.activity,
            attempts=len(revision_result.attempts),
        )

    if decision.decision != "ACCEPT" or revision_result.activity is None:
        return None

    return AcceptedActivity(
        activity=revision_result.activity,
        contract=contract,
        acceptance=decision,
    )
