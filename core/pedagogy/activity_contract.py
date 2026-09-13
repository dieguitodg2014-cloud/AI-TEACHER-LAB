"""Bionic MVP-002: provider-agnostic contract for activity generation.

The contract carries pedagogical decisions into content generation. Generators
may instantiate the activity, but they must not silently change its pedagogical
parameters.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivityGenerationContract:
    """Immutable specification an activity generator must satisfy."""

    activity_id: str
    pattern_id: str
    level: str
    objective_ids: tuple[str, ...]
    skill: str
    language_target: tuple[str, ...]
    vocabulary: tuple[str, ...]
    interaction: str
    cognitive_demand: str
    scaffolding: int
    duration_minutes: int
    constraints: tuple[str, ...] = ()
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()
    evidence_expected: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContractValidationResult:
    """Deterministic validation result for a generation contract."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ActivityContractValidator:
    """Validate contract integrity before an activity is generated."""

    VALID_INTERACTIONS = {"INDIVIDUAL", "PAIR", "GROUP", "WHOLE_CLASS"}
    VALID_LEVELS = {"A0", "A1", "A2", "B1", "B2"}
    VALID_SKILLS = {
        "LISTENING", "SPEAKING", "READING", "WRITING",
        "GRAMMAR", "VOCABULARY", "PRONUNCIATION",
    }

    def validate(self, contract: ActivityGenerationContract) -> ContractValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not contract.activity_id.strip():
            errors.append("activity_id is required")
        if not contract.pattern_id.strip():
            errors.append("pattern_id is required")
        if contract.level not in self.VALID_LEVELS:
            errors.append(f"Unsupported level: {contract.level}")
        if not contract.objective_ids:
            errors.append("At least one objective_id is required")
        if contract.skill.upper() not in self.VALID_SKILLS:
            errors.append(f"Unsupported skill: {contract.skill}")
        if contract.interaction not in self.VALID_INTERACTIONS:
            errors.append(f"Unsupported interaction: {contract.interaction}")
        if contract.duration_minutes <= 0:
            errors.append("duration_minutes must be greater than zero")
        if not 0 <= contract.scaffolding <= 4:
            errors.append("scaffolding must be between 0 and 4")

        if contract.interaction in {"PAIR", "GROUP"} and not contract.evidence_expected:
            warnings.append("Interactive activity has no explicit evidence expectation")

        if contract.skill.upper() == "SPEAKING" and not contract.language_target:
            errors.append("Speaking activity requires a language target")

        if contract.level == "A0" and contract.scaffolding < 2:
            warnings.append("A0 contract has low scaffolding; verify visual/model support")

        if contract.must_include and contract.must_not_include:
            overlap = set(contract.must_include) & set(contract.must_not_include)
            if overlap:
                errors.append(
                    "must_include and must_not_include overlap: "
                    + ", ".join(sorted(overlap))
                )

        return ContractValidationResult(
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
