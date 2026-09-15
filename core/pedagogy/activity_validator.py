"""Bionic MVP-002: deterministic validation of generated activities.

This validator checks observable properties of a generated activity against its
pedagogical contract. It does not judge aesthetics and it never lets a quality
score override a critical failure.
"""
from dataclasses import dataclass

from .activity_contract import ActivityGenerationContract


@dataclass(frozen=True)
class ActivityValidationResult:
    status: str
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ActivityValidator:
    """Validate a generated activity represented as a plain mapping.

    The mapping intentionally remains provider-agnostic so adapters can supply
    content from Canva, NotebookLM, a local model, or another generator.
    """

    def validate(
        self,
        activity: dict,
        contract: ActivityGenerationContract,
    ) -> ActivityValidationResult:
        failures: list[str] = []
        warnings: list[str] = []

        self._check_equal(activity, "pattern_id", contract.pattern_id, failures)
        self._check_equal(activity, "level", contract.level, failures)
        self._check_equal(activity, "interaction", contract.interaction, failures)
        self._check_equal(activity, "cognitive_demand", contract.cognitive_demand, failures)
        self._check_equal(activity, "duration_minutes", contract.duration_minutes, failures)

        skill = str(activity.get("skill", "")).upper()
        if skill != contract.skill.upper():
            failures.append("Skill does not match the generation contract")

        targets = set(activity.get("language_target", ()))
        missing_targets = [item for item in contract.language_target if item not in targets]
        if missing_targets:
            failures.append("Required language target is missing")

        vocab = set(activity.get("vocabulary", ()))
        missing_vocab = [item for item in contract.vocabulary if item not in vocab]
        if missing_vocab:
            warnings.append("One or more contracted vocabulary items are not explicitly listed")

        for item in contract.must_include:
            if not self._contains(activity, item):
                failures.append(f"Missing required element: {item}")

        for item in contract.must_not_include:
            if self._contains(activity, item):
                failures.append(f"Prohibited element present: {item}")

        if contract.interaction in {"PAIR", "GROUP"}:
            roles = activity.get("student_roles", ())
            if len(roles) < 2:
                failures.append("Interactive activity must define at least two student roles")

            output_by_student = activity.get("oral_output_by_student", {})
            if contract.skill.upper() == "SPEAKING":
                if not output_by_student or len(output_by_student) < 2:
                    failures.append("Speaking interaction must provide oral output for at least two learners")

        if contract.level == "A0":
            if contract.scaffolding >= 2:
                support = set(activity.get("scaffolding_support", ()))
                if not support.intersection({"model", "visual", "sentence_frame", "word_bank"}):
                    failures.append("A0 activity lacks an observable core scaffold")

        if contract.skill.upper() == "SPEAKING" and not activity.get("student_output"):
            failures.append("Speaking activity has no explicit student oral output")

        if not contract.evidence_expected:
            warnings.append("No explicit evidence requirement was provided by the contract")

        status = "REJECT" if failures else ("PASS_WITH_WARNINGS" if warnings else "PASS")
        return ActivityValidationResult(status, tuple(failures), tuple(warnings))

    @staticmethod
    def _check_equal(activity: dict, key: str, expected, failures: list[str]) -> None:
        if activity.get(key) != expected:
            failures.append(f"{key} does not match the generation contract")

    @staticmethod
    def _contains(activity: dict, expected: str) -> bool:
        if expected in activity:
            return True
        text = str(activity).lower()
        return expected.lower() in text
