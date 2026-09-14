"""Load tool candidates from the runtime configuration."""

from __future__ import annotations

import json
from pathlib import Path

from core.orchestration.provider_capability_contract import validate_provider_capabilities
from core.orchestration.tool_selector import (
    VALID_CAPABILITY_VALIDATION_STATUSES,
    ToolCandidate,
)

DEFAULT_TOOL_CONFIG = Path(__file__).resolve().parents[2] / "config" / "tools.json"


def load_tool_registry_config(path: str | Path) -> tuple[list[ToolCandidate], dict]:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))

    raw_tools = data.get("tools")
    if not isinstance(raw_tools, list):
        raise ValueError("INVALID_TOOL_CONFIG:tools")

    tools: list[ToolCandidate] = []
    for raw in raw_tools:
        if not isinstance(raw, dict) or not isinstance(raw.get("tool_id"), str):
            raise ValueError("INVALID_TOOL_CONFIG:tool")
        capabilities = raw.get("capabilities", [])
        capability_errors = validate_provider_capabilities(capabilities)
        if capability_errors:
            raise ValueError(
                f"INVALID_PROVIDER_CAPABILITIES:{raw['tool_id']}:{capability_errors[0]}"
            )
        raw_validation = raw.get("capability_validation", {})
        if not isinstance(raw_validation, dict):
            raise ValueError(
                f"INVALID_CAPABILITY_VALIDATION:{raw['tool_id']}"
            )
        for capability, status in raw_validation.items():
            if not isinstance(capability, str) or status not in VALID_CAPABILITY_VALIDATION_STATUSES:
                raise ValueError(
                    f"INVALID_CAPABILITY_VALIDATION:{raw['tool_id']}:{capability}"
                )
        capability_validation = tuple(
            sorted((capability, status) for capability, status in raw_validation.items())
        )
        tools.append(
            ToolCandidate(
                tool_id=raw["tool_id"],
                capabilities=frozenset(capabilities),
                quality=float(raw.get("quality", 0.0)),
                reliability=float(raw.get("reliability", 0.0)),
                accessibility=float(raw.get("accessibility", 0.0)),
                speed=float(raw.get("speed", 0.0)),
                cost=float(raw.get("cost", 0.0)),
                capability_validation=capability_validation,
            )
        )

    policy = data.get("policy", {})
    if not isinstance(policy, dict):
        raise ValueError("INVALID_TOOL_CONFIG:policy")
    return tools, policy


def resource_provider_priority(policy: dict | None) -> tuple[str, ...]:
    """Return configured specialized resource providers in priority order."""
    if not isinstance(policy, dict):
        return ()
    provider_policy = policy.get("provider_policy", {})
    if not isinstance(provider_policy, dict):
        return ()
    configured = provider_policy.get("resource_provider_priority")
    if configured is None:
        configured = provider_policy.get("specialized_resource_creators", [])
    if not isinstance(configured, list):
        return ()
    return tuple(item for item in configured if isinstance(item, str))
