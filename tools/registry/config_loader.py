"""Load tool candidates from the runtime configuration."""

from __future__ import annotations

import json
from pathlib import Path

from core.orchestration.provider_capability_contract import validate_provider_capabilities
from core.orchestration.tool_selector import ToolCandidate


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
        tools.append(
            ToolCandidate(
                tool_id=raw["tool_id"],
                capabilities=frozenset(capabilities),
                quality=float(raw.get("quality", 0.0)),
                reliability=float(raw.get("reliability", 0.0)),
                accessibility=float(raw.get("accessibility", 0.0)),
                speed=float(raw.get("speed", 0.0)),
                cost=float(raw.get("cost", 0.0)),
            )
        )

    policy = data.get("policy", {})
    if not isinstance(policy, dict):
        raise ValueError("INVALID_TOOL_CONFIG:policy")
    return tools, policy
