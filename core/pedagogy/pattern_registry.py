"""Bionic MVP-002: reusable pedagogical activity patterns."""
from dataclasses import dataclass
from enum import Enum


class Level(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"


class Interaction(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    PAIR = "PAIR"
    GROUP = "GROUP"
    WHOLE_CLASS = "WHOLE_CLASS"


class CognitiveDemand(str, Enum):
    RECOGNIZE = "RECOGNIZE"
    IDENTIFY = "IDENTIFY"
    MATCH = "MATCH"
    RECALL = "RECALL"
    CONTROLLED_PRODUCTION = "CONTROLLED_PRODUCTION"
    GUIDED_PRODUCTION = "GUIDED_PRODUCTION"
    COMMUNICATIVE_PRODUCTION = "COMMUNICATIVE_PRODUCTION"
    CREATE = "CREATE"
    REFLECT = "REFLECT"


class SequenceRole(str, Enum):
    EXPOSURE = "EXPOSURE"
    COMPREHENSION = "COMPREHENSION"
    NOTICING = "NOTICING"
    CONTROLLED_PRACTICE = "CONTROLLED_PRACTICE"
    GUIDED_PRODUCTION = "GUIDED_PRODUCTION"
    COMMUNICATIVE_PRODUCTION = "COMMUNICATIVE_PRODUCTION"
    ASSESSMENT = "ASSESSMENT"


@dataclass(frozen=True)
class Pattern:
    pattern_id: str
    name: str
    purpose: str
    skills: tuple[str, ...]
    interaction: tuple[Interaction, ...]
    cognitive_demand: tuple[CognitiveDemand, ...]
    communicative_value: float
    scaffolding_min: int
    scaffolding_max: int
    recommended_levels: tuple[Level, ...]
    timing_min: int
    timing_max: int
    requires_student_output: bool
    requires_teacher_model: bool
    resource_dependency: str
    sequence_roles: tuple[SequenceRole, ...]
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    avoid_when: tuple[str, ...] = ()

    def supports_level(self, level: str) -> bool:
        return Level(level) in self.recommended_levels

    def supports_interaction(self, interaction: str) -> bool:
        return Interaction(interaction) in self.interaction


@dataclass(frozen=True)
class PatternFilter:
    level: str | None = None
    interaction: str | None = None
    skill: str | None = None
    requires_student_output: bool | None = None
    sequence_role: str | None = None


class PatternRegistry:
    """Single source of truth for pattern definitions; no tool selection here."""

    def __init__(self, patterns=None):
        self._patterns = {p.pattern_id: p for p in (patterns or DEFAULT_PATTERNS)}

    def get(self, pattern_id: str) -> Pattern:
        return self._patterns[pattern_id]

    def all(self) -> tuple[Pattern, ...]:
        return tuple(self._patterns.values())

    def ids(self) -> tuple[str, ...]:
        return tuple(self._patterns)

    def filter(self, criteria: PatternFilter) -> list[Pattern]:
        out = list(self.all())
        if criteria.level:
            out = [p for p in out if p.supports_level(criteria.level)]
        if criteria.interaction:
            out = [p for p in out if p.supports_interaction(criteria.interaction)]
        if criteria.skill:
            out = [p for p in out if criteria.skill.upper() in p.skills]
        if criteria.requires_student_output is not None:
            out = [p for p in out if p.requires_student_output == criteria.requires_student_output]
        if criteria.sequence_role:
            out = [p for p in out if SequenceRole(criteria.sequence_role) in p.sequence_roles]
        return out


def _p(pid, name, purpose, skills, interaction, cognitive, comm, smin, smax,
       levels, tmin, tmax, output, model, dependency, roles):
    return Pattern(pid, name, purpose, skills, interaction, cognitive, comm,
                   smin, smax, levels, tmin, tmax, output, model, dependency, roles)


A = (Level.A0, Level.A1, Level.A2)
AB = (Level.A1, Level.A2, Level.B1, Level.B2)
ALL = (Level.A0, Level.A1, Level.A2, Level.B1, Level.B2)

DEFAULT_PATTERNS = (
    _p("MODEL_AND_REPEAT", "Model & Repeat", "Build pronunciation, confidence, and initial accuracy.",
       ("SPEAKING", "PRONUNCIATION"), (Interaction.WHOLE_CLASS, Interaction.INDIVIDUAL),
       (CognitiveDemand.RECALL, CognitiveDemand.CONTROLLED_PRODUCTION), .20, 3, 4, A, 2, 8, True, True, "USEFUL",
       (SequenceRole.EXPOSURE, SequenceRole.NOTICING, SequenceRole.CONTROLLED_PRACTICE)),
    _p("VISUAL_NOTICING", "Visual Noticing", "Support comprehension and noticing through visual input.",
       ("VOCABULARY", "LISTENING", "READING"), (Interaction.WHOLE_CLASS, Interaction.INDIVIDUAL),
       (CognitiveDemand.RECOGNIZE, CognitiveDemand.IDENTIFY), .30, 2, 4, ALL, 4, 10, False, True, "USEFUL",
       (SequenceRole.EXPOSURE, SequenceRole.COMPREHENSION, SequenceRole.NOTICING)),
    _p("MATCHING", "Matching", "Connect forms, meanings, words, sounds, or visuals.",
       ("VOCABULARY", "READING", "LISTENING"), (Interaction.INDIVIDUAL, Interaction.PAIR),
       (CognitiveDemand.MATCH, CognitiveDemand.IDENTIFY), .20, 1, 3, A, 3, 8, False, False, "OPTIONAL",
       (SequenceRole.COMPREHENSION, SequenceRole.CONTROLLED_PRACTICE)),
    _p("SORTING", "Sorting", "Classify language or content using a meaningful criterion.",
       ("VOCABULARY", "READING", "GRAMMAR"), (Interaction.INDIVIDUAL, Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.IDENTIFY, CognitiveDemand.CREATE), .30, 1, 3, ALL, 4, 10, True, False, "OPTIONAL",
       (SequenceRole.COMPREHENSION, SequenceRole.NOTICING, SequenceRole.CONTROLLED_PRACTICE)),
    _p("IDENTIFICATION", "Identification", "Locate or recognize a target item in meaningful input.",
       ("VOCABULARY", "GRAMMAR", "LISTENING", "READING"), (Interaction.INDIVIDUAL, Interaction.WHOLE_CLASS),
       (CognitiveDemand.IDENTIFY, CognitiveDemand.RECOGNIZE), .15, 1, 3, A, 3, 7, True, True, "OPTIONAL",
       (SequenceRole.COMPREHENSION, SequenceRole.NOTICING)),
    _p("CONTROLLED_PRACTICE", "Controlled Practice", "Build accurate use of target language with constrained choices.",
       ("GRAMMAR", "VOCABULARY", "SPEAKING", "WRITING"), (Interaction.INDIVIDUAL, Interaction.PAIR, Interaction.WHOLE_CLASS),
       (CognitiveDemand.CONTROLLED_PRODUCTION,), .40, 2, 4, ALL, 5, 15, True, True, "USEFUL",
       (SequenceRole.CONTROLLED_PRACTICE,)),
    _p("GUIDED_PRODUCTION", "Guided Production", "Move toward supported independent production.",
       ("SPEAKING", "WRITING"), (Interaction.INDIVIDUAL, Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.GUIDED_PRODUCTION,), .65, 2, 4, ALL, 6, 15, True, True, "USEFUL",
       (SequenceRole.GUIDED_PRODUCTION,)),
    _p("INFORMATION_GAP", "Information Gap", "Create a genuine need to exchange information.",
       ("SPEAKING", "LISTENING"), (Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.COMMUNICATIVE_PRODUCTION,), .90, 2, 4, AB, 8, 20, True, False, "USEFUL",
       (SequenceRole.COMMUNICATIVE_PRODUCTION,)),
    _p("INTERVIEW", "Interview", "Exchange personally relevant information through questions and answers.",
       ("SPEAKING", "LISTENING"), (Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.GUIDED_PRODUCTION, CognitiveDemand.COMMUNICATIVE_PRODUCTION), .85, 2, 4, AB, 8, 20, True, True, "USEFUL",
       (SequenceRole.GUIDED_PRODUCTION, SequenceRole.COMMUNICATIVE_PRODUCTION)),
    _p("SURVEY", "Survey", "Repeat meaningful questions and aggregate responses.",
       ("SPEAKING", "LISTENING", "WRITING"), (Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.COMMUNICATIVE_PRODUCTION, CognitiveDemand.CREATE), .90, 2, 4, AB, 10, 20, True, False, "USEFUL",
       (SequenceRole.COMMUNICATIVE_PRODUCTION, SequenceRole.ASSESSMENT)),
    _p("FIND_SOMEONE_WHO", "Find Someone Who", "Use repeated questions to discover matching classmates.",
       ("SPEAKING", "LISTENING"), (Interaction.GROUP,),
       (CognitiveDemand.RECALL, CognitiveDemand.COMMUNICATIVE_PRODUCTION), .90, 2, 4, AB, 10, 20, True, False, "USEFUL",
       (SequenceRole.COMMUNICATIVE_PRODUCTION,)),
    _p("ROLE_PLAY", "Role Play", "Simulate a purposeful interaction.",
       ("SPEAKING", "LISTENING"), (Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.GUIDED_PRODUCTION, CognitiveDemand.COMMUNICATIVE_PRODUCTION), .85, 2, 4, AB, 8, 20, True, True, "USEFUL",
       (SequenceRole.GUIDED_PRODUCTION, SequenceRole.COMMUNICATIVE_PRODUCTION)),
    _p("PICTURE_DESCRIPTION", "Picture Description", "Bridge visual input to spoken or written language.",
       ("SPEAKING", "VOCABULARY", "WRITING"), (Interaction.INDIVIDUAL, Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.GUIDED_PRODUCTION, CognitiveDemand.COMMUNICATIVE_PRODUCTION), .65, 2, 4, ALL, 5, 15, True, True, "USEFUL",
       (SequenceRole.GUIDED_PRODUCTION, SequenceRole.COMMUNICATIVE_PRODUCTION)),
    _p("JIGSAW", "Jigsaw", "Combine distributed information to complete a shared task.",
       ("READING", "LISTENING", "SPEAKING"), (Interaction.GROUP, Interaction.PAIR),
       (CognitiveDemand.CREATE, CognitiveDemand.COMMUNICATIVE_PRODUCTION), .90, 2, 4, (Level.A2, Level.B1, Level.B2), 12, 25, True, False, "USEFUL",
       (SequenceRole.COMMUNICATIVE_PRODUCTION,)),
    _p("RETELL", "Retell", "Reconstruct and communicate key information from input or a model.",
       ("SPEAKING", "LISTENING", "READING"), (Interaction.INDIVIDUAL, Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.RECALL, CognitiveDemand.GUIDED_PRODUCTION), .70, 2, 4, AB, 6, 15, True, True, "USEFUL",
       (SequenceRole.GUIDED_PRODUCTION, SequenceRole.COMMUNICATIVE_PRODUCTION)),
    _p("PROBLEM_SOLVING", "Problem Solving", "Use language to negotiate a solution.",
       ("SPEAKING", "LISTENING", "READING"), (Interaction.PAIR, Interaction.GROUP),
       (CognitiveDemand.CREATE, CognitiveDemand.COMMUNICATIVE_PRODUCTION), .90, 2, 4, (Level.A2, Level.B1, Level.B2), 10, 25, True, False, "USEFUL",
       (SequenceRole.COMMUNICATIVE_PRODUCTION,)),
    _p("EXIT_TICKET", "Exit Ticket", "Collect concise evidence of learning.",
       ("SPEAKING", "WRITING", "GRAMMAR", "VOCABULARY"), (Interaction.INDIVIDUAL,),
       (CognitiveDemand.RECALL, CognitiveDemand.CONTROLLED_PRODUCTION, CognitiveDemand.REFLECT), .40, 1, 4, ALL, 2, 7, True, False, "OPTIONAL",
       (SequenceRole.ASSESSMENT,)),
    _p("QUICK_CHECK", "Quick Check", "Formatively check comprehension or target-language control.",
       ("GRAMMAR", "VOCABULARY", "LISTENING", "READING", "SPEAKING"), (Interaction.INDIVIDUAL, Interaction.WHOLE_CLASS),
       (CognitiveDemand.RECOGNIZE, CognitiveDemand.IDENTIFY, CognitiveDemand.RECALL), .40, 1, 4, ALL, 2, 7, True, False, "OPTIONAL",
       (SequenceRole.COMPREHENSION, SequenceRole.ASSESSMENT)),
)
