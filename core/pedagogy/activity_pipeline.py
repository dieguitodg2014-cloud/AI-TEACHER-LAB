"""Bionic MVP-002: bridge sequence planning to activity generation and validation.

The pipeline makes the pedagogical contract the boundary between planning and
content generation. A generator can produce content, but acceptance remains the
responsibility of ActivityValidator. Rejected output is converted into a
provider-neutral revision contract rather than silently accepted.
"""
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .activity_contract import (
    ActivityContractValidator,
    ActivityGenerationContract,
    ContractValidationResult,
)
from .activity_validator import ActivityValidationResult, ActivityValidator
from .pattern_registry import PatternRegistry
from .sequence_planner import PlannedPattern


@dataclass(frozen=True)
class RevisionContract:
    """Deterministic instructions for correcting rejected generated output."""

    activity_id: str
    source_contract: ActivityGenerationContract
    failures: tuple[str, ...]
    preserve: tuple[str, ...]


@dataclass(frozen=True)
class ActivityPipelineResult:
    """Complete result for one planned activity."""

    contract: ActivityGenerationContract
    contract_validation: ContractValidationResult
    activity: Mapping[str, Any] | None
    validation: ActivityValidationResult | None
    revision_contract: RevisionContract | None = None

    @property
    def accepted(self) -> bool:
        return (
            self.contract_validation.valid
            and self.validation is not None
            and self.validation.status in {"PASS", "PASS_WITH_WARNINGS"}
        )


class ActivityContractFactory:
    """Translate a planner decision into an executable generation contract."""

    def __init__(self, registry: PatternRegistry | None = None):
        self.registry = registry or PatternRegistry()

    def build(
        self,
        planned: PlannedPattern,
        *,
        activity_id: str,
        level: str,
        objective_ids: tuple[str, ...],
        skill: str,
        language_target: tuple[str, ...],
        vocabulary: tuple[str, ...] = (),
        scaffolding: int | None = None,
        constraints: tuple[str, ...] = (),
        must_include: tuple[str, ...] = (),
        must_not_include: tuple[str, ...] = (),
        evidence_expected: tuple[str, ...] = (),
    ) -> ActivityGenerationContract:
        pattern = self.registry.get(planned.pattern_id)

        if scaffolding is None:
            scaffolding = pattern.scaffolding_min

        if not pattern.supports_level(level):
            raise ValueError(
                f"Pattern {planned.pattern_id} does not support level {level}"
            )
        if skill.upper() not in pattern.skills:
            raise ValueError(
                f"Pattern {planned.pattern_id} does not support skill {skill}"
            )
        if planned.timing_minutes < pattern.timing_min or planned.timing_minutes > pattern.timing_max:
            raise ValueError(
                f"Timing {planned.timing_minutes} is outside the pattern range "
                f"{pattern.timing_min}-{pattern.timing_max}"
            )

        interaction = planned.interaction or pattern.interaction[0].value
        if not pattern.supports_interaction(interaction):
            raise ValueError(
                f"Pattern {planned.pattern_id} does not support interaction {interaction}"
            )

        return ActivityGenerationContract(
            activity_id=activity_id,
            pattern_id=planned.pattern_id,
            level=level,
            objective_ids=objective_ids,
            skill=skill.upper(),
            language_target=language_target,
            vocabulary=vocabulary,
            interaction=interaction,
            cognitive_demand=pattern.cognitive_demand[0].value,
            scaffolding=scaffolding,
            duration_minutes=planned.timing_minutes,
            constraints=constraints,
            must_include=must_include,
            must_not_include=must_not_include,
            evidence_expected=evidence_expected,
        )


class ActivityPipeline:
    """Run contract validation, generation, validation, and revision handoff."""

    def __init__(
        self,
        contract_validator: ActivityContractValidator | None = None,
        activity_validator: ActivityValidator | None = None,
    ):
        self.contract_validator = contract_validator or ActivityContractValidator()
        self.activity_validator = activity_validator or ActivityValidator()

    def run(
        self,
        contract: ActivityGenerationContract,
        generator: Callable[[ActivityGenerationContract], Mapping[str, Any]],
    ) -> ActivityPipelineResult:
        contract_result = self.contract_validator.validate(contract)
        if not contract_result.valid:
            return ActivityPipelineResult(contract, contract_result, None, None)

        activity = generator(contract)
        validation = self.activity_validator.validate(dict(activity), contract)

        revision_contract = None
        if validation.status == "REJECT":
            revision_contract = RevisionContract(
                activity_id=contract.activity_id,
                source_contract=contract,
                failures=validation.failures,
                preserve=(
                    "level",
                    "objective_ids",
                    "skill",
                    "language_target",
                    "interaction",
                    "cognitive_demand",
                    "duration_minutes",
                    "scaffolding",
                    "must_include",
                    "must_not_include",
                    "evidence_expected",
                ),
            )

        return ActivityPipelineResult(
            contract,
            contract_result,
            activity,
            validation,
            revision_contract,
        )
