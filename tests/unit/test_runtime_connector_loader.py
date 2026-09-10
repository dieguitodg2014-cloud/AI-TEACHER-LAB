import json

import pytest

from tools.connectors import runtime_loader


def write_config(tmp_path, connector="local_openai_compatible"):
    path = tmp_path / "tools.json"
    path.write_text(
        json.dumps(
            {
                "tools": [
                    {"tool_id": "lesson-tool", "connector": connector},
                    {"tool_id": "planning-only"},
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_load_runtime_generators_resolves_configured_connector(tmp_path, monkeypatch):
    sentinel = object()
    monkeypatch.setitem(
        runtime_loader._CONNECTOR_FACTORIES,
        "local_openai_compatible",
        lambda: sentinel,
    )

    generators = runtime_loader.load_runtime_generators(write_config(tmp_path))

    assert generators == {"lesson-tool": sentinel}


def test_load_runtime_generators_rejects_unknown_connector(tmp_path):
    with pytest.raises(ValueError, match="UNSUPPORTED_CONNECTOR:unknown"):
        runtime_loader.load_runtime_generators(write_config(tmp_path, "unknown"))


def test_load_runtime_generators_ignores_tools_without_connector(tmp_path, monkeypatch):
    sentinel = object()
    monkeypatch.setitem(
        runtime_loader._CONNECTOR_FACTORIES,
        "local_openai_compatible",
        lambda: sentinel,
    )

    generators = runtime_loader.load_runtime_generators(write_config(tmp_path))

    assert "planning-only" not in generators
