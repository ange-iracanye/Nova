from types import SimpleNamespace

from backend.core.nova_core import NovaCore
from backend.tools.registry import ToolRegistry


def test_nova_core_routes_explicit_calculation_to_local_tool():
    core = object.__new__(NovaCore)
    core.tool_registry = ToolRegistry()
    core.component_health = {}
    request = SimpleNamespace(
        original_message="What is 12 * 8?",
        tools_used=[],
        tool_result={},
        tool_context="",
        warnings=[],
        degraded_components=[],
        mark_degraded=lambda name: None,
        add_warning=lambda message: None,
    )

    NovaCore._stage_tool_execution(core, request)

    assert request.tool_result["tool"] == "calculator"
    assert request.tool_result["result"]["value"] == "96"
    assert request.tools_used[0]["read_only"] is True


def test_nova_core_formats_tool_results_without_calling_language_model():
    request = SimpleNamespace(
        tool_result={
            "tool": "unit_converter",
            "result": {
                "input": 5,
                "from_unit": "km",
                "value": 5000,
                "to_unit": "m",
            },
        },
        answer="",
    )

    NovaCore._stage_generation(object.__new__(NovaCore), request)

    assert "5 km = 5000 m" in request.answer
