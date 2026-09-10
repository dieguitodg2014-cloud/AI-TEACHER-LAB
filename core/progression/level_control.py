"""Level Control Engine for the AI-TEACHER-LAB vertical slice."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.foundation.models import Context, LevelDecision
from core.foundation.validation import validate_level_decision


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "level-profiles.json"


def load_level_profiles(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, dict[str, str]]:
    """Load level profiles from configuration; fail clearly if the contract is invalid."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        profiles = json.load(file)

    required = {
        "linguistic_complexity",
        "cognitive_demand",
        "interaction_expectation",
        "scaffolding",
        "autonomy_expectation",
        "grammar_precision",
        "fluency_expectation",
        "register",
        "assessment_expectation",
    }

    for level, profile in profiles.items():
        missing = required - profile.keys()
        if missing:
            raise ValueError(f"Invalid profile for {level}: missing {sorted(missing)}")

    return profiles


def decide_level(
    context: Context,
    profiles: dict[str, dict[str, str]] | None = None,
) -> LevelDecision:
    """Translate the already-established context level into pedagogical boundaries."""
    profiles = profiles or load_level_profiles()

    if context.level not in profiles:
        raise ValueError(f"Unsupported level: {context.level}")

    profile = profiles[context.level]
    decision = LevelDecision(
        decision_id=f"level-{uuid4().hex[:12]}",
        level=context.level,
        linguistic_complexity=profile["linguistic_complexity"],
        cognitive_demand=profile["cognitive_demand"],
        interaction_expectation=profile["interaction_expectation"],
        scaffolding=profile["scaffolding"],
        autonomy_expectation=profile["autonomy_expectation"],
        grammar_precision=profile["grammar_precision"],
        fluency_expectation=profile["fluency_expectation"],
        register=profile["register"],
        assessment_expectation=profile["assessment_expectation"],
    )

    errors = validate_level_decision(decision)
    if errors:
        raise ValueError("Invalid level decision: " + "; ".join(errors))

    return decision


def level_decision_to_dict(decision: LevelDecision) -> dict[str, Any]:
    """Return a serializable decision for downstream engines."""
    return asdict(decision)
