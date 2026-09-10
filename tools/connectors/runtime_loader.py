"""Resolve configured tool connectors into executable generators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from tools.connectors.local_openai_compatible import create_local_openai_compatible_generator


_CONNECTOR_FACTORIES: dict[str, Callable[[], Callable]] = {
    "local_openai_compatible": create_local_openai_compatible_generator,
}


def load_runtime_generators(path: str | Path) -> dict[str, Callable]:
    """Build generators for tools that declare a supported runtime connector."""
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    raw_tools = data.get("tools")
    if not isinstance(raw_tools, list):
        raise ValueError("INVALID_TOOL_CONFIG:tools")

    generators: dict[str, Callable] = {}
    for raw in raw_tools:
        if not isinstance(raw, dict) or not isinstance(raw.get("tool_id"), str):
            raise ValueError("INVALID_TOOL_CONFIG:tool")
        tool_id = raw["tool_id"]
        connector = raw.get("connector")
        if connector is None:
            continue
        if not isinstance(connector, str):
            raise ValueError(f"INVALID_TOOL_CONFIG:connector:{tool_id}")
        factory = _CONNECTOR_FACTORIES.get(connector)
        if factory is None:
            raise ValueError(f"UNSUPPORTED_CONNECTOR:{connector}")
        generators[tool_id] = factory()

    return generators
