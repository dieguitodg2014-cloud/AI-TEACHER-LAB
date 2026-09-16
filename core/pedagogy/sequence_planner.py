"""Bionic MVP-002: deterministic minimum-effective-sequence planning.

The planner chooses pedagogical activity patterns from the registry. It does not
select external tools or generate activity content. Those responsibilities belong
to later pipeline stages.
"""
from dataclasses import dataclass

from .pattern_registry import Interaction, Level, Pattern, PatternFilter, PatternRegistry, SequenceRole


@dataclass(frozen=True)
class SequenceRequest:
    """Pedagogical inputs needed to build a minimum effective sequence."""

    level: str
    duration_minutes: int
    primary_skill: str
    interaction: str = Interaction.INDIVIDUAL.value
    requires_communication: bool = False
    requires_assessment: bool = True


@dataclass(frozen=True)
class PlannedPattern:
    """A selected pattern plus its planned time and sequence role."""

    pattern_id: str
    sequence_role: str
    timing_minutes: int


@dataclass(frozen=True)
class SequencePlan:
    """Deterministic planner output."""

    patterns: tuple[PlannedPattern, ...]
    total_minutes: int
    uncovered_roles: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def pattern_ids(self) -> tuple[str, ...]:
        return tuple(item.pattern_id for item in self.patterns)


class SequencePlanner:
    """Build the smallest useful sequence that covers core learning roles."""

    _ROLE_ORDER = (
        SequenceRole.EXPOSURE, SequenceRole.NOTICING,
        SequenceRole.CONTROLLED_PRACTICE, SequenceRole.GUIDED_PRODUCTION,
        SequenceRole.COMMUNICATIVE_PRODUCTION, SequenceRole.ASSESSMENT,
    )

    _PREFERRED_BY_ROLE = {
        SequenceRole.EXPOSURE: ("MODEL_AND_REPEAT", "VISUAL_NOTICING"),
        SequenceRole.NOTICING: ("VISUAL_NOTICING", "MODEL_AND_REPEAT"),
        SequenceRole.CONTROLLED_PRACTICE: ("CONTROLLED_PRACTICE", "MATCHING"),
        SequenceRole.GUIDED_PRODUCTION: ("GUIDED_PRODUCTION", "INTERVIEW", "PICTURE_DESCRIPTION"),
        SequenceRole.COMMUNICATIVE_PRODUCTION: ("INTERVIEW", "INFORMATION_GAP", "SURVEY", "ROLE_PLAY", "PICTURE_DESCRIPTION"),
        SequenceRole.ASSESSMENT: ("EXIT_TICKET", "QUICK_CHECK"),
    }

    def __init__(self, registry: PatternRegistry | None = None):
        self.registry = registry or PatternRegistry()

    def plan(self, request: SequenceRequest) -> SequencePlan:
        level = Level(request.level)
        interaction = Interaction(request.interaction)
        primary_skill = request.primary_skill.upper()
        if request.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than zero")

        candidates = self.registry.filter(PatternFilter(level=level.value, interaction=interaction.value))
        candidate_ids = {pattern.pattern_id for pattern in candidates}
        # Noticing and assessment can legitimately use whole-class or individual
        # interaction inside a pair/group lesson; do not report them uncovered
        # merely because their own interaction differs from the lesson default.
        for pattern in self.registry.filter(PatternFilter(level=level.value)):
            if SequenceRole.NOTICING in pattern.sequence_roles or SequenceRole.ASSESSMENT in pattern.sequence_roles:
                candidate_ids.add(pattern.pattern_id)

        selected: list[PlannedPattern] = []
        selected_ids: set[str] = set()
        required_roles = [SequenceRole.CONTROLLED_PRACTICE]
        if request.requires_communication:
            required_roles.extend([SequenceRole.GUIDED_PRODUCTION, SequenceRole.COMMUNICATIVE_PRODUCTION])
        else:
            required_roles.append(SequenceRole.GUIDED_PRODUCTION)
        if request.requires_assessment:
            required_roles.append(SequenceRole.ASSESSMENT)
        if request.duration_minutes >= 25:
            required_roles.insert(0, SequenceRole.NOTICING)

        for role in self._ROLE_ORDER:
            if role not in required_roles:
                continue
            pattern = self._choose_pattern(role, candidate_ids, selected_ids, level, primary_skill)
            if pattern is None:
                continue
            selected.append(PlannedPattern(pattern.pattern_id, role.value, self._initial_time(pattern, role)))
            selected_ids.add(pattern.pattern_id)

        if level in (Level.A0, Level.A1) and request.duration_minutes >= 40:
            if "MODEL_AND_REPEAT" in candidate_ids and "MODEL_AND_REPEAT" not in selected_ids:
                selected.insert(0, PlannedPattern("MODEL_AND_REPEAT", SequenceRole.EXPOSURE.value, 5))
                selected_ids.add("MODEL_AND_REPEAT")

        selected = self._fit_to_duration(selected, request.duration_minutes)
        uncovered = tuple(role.value for role in required_roles if not any(item.sequence_role == role.value for item in selected))
        warnings = []
        if uncovered:
            warnings.append("Required sequence roles could not all be covered within the available constraints.")
        if not selected:
            warnings.append("No compatible activity pattern was found.")
        return SequencePlan(tuple(selected), sum(item.timing_minutes for item in selected), uncovered, tuple(warnings))

    def _choose_pattern(self, role, candidate_ids, selected_ids, level, primary_skill):
        for pattern_id in self._PREFERRED_BY_ROLE[role]:
            if pattern_id not in candidate_ids or pattern_id in selected_ids:
                continue
            pattern = self.registry.get(pattern_id)
            if not pattern.supports_level(level.value):
                continue
            if role not in (SequenceRole.EXPOSURE, SequenceRole.NOTICING) and primary_skill not in pattern.skills:
                continue
            return pattern
        return None

    @staticmethod
    def _initial_time(pattern: Pattern, role: SequenceRole) -> int:
        preferred = {SequenceRole.NOTICING: 8, SequenceRole.CONTROLLED_PRACTICE: 10, SequenceRole.GUIDED_PRODUCTION: 10, SequenceRole.COMMUNICATIVE_PRODUCTION: 15, SequenceRole.ASSESSMENT: 7, SequenceRole.EXPOSURE: 5}.get(role, pattern.timing_min)
        return max(pattern.timing_min, min(preferred, pattern.timing_max))

    @staticmethod
    def _fit_to_duration(items, duration_minutes):
        if not items:
            return items
        total = sum(item.timing_minutes for item in items)
        if total <= duration_minutes:
            return items
        adjusted = list(items)
        for index in range(len(adjusted) - 1, -1, -1):
            item = adjusted[index]
            reduction = min(item.timing_minutes - 2, total - duration_minutes)
            if reduction > 0:
                adjusted[index] = PlannedPattern(item.pattern_id, item.sequence_role, item.timing_minutes - reduction)
                total -= reduction
            if total <= duration_minutes:
                break
        return adjusted
