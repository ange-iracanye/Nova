import pytest

from backend.tools.calculator import Calculator
from backend.tools.registry import ToolError, ToolRegistry


def test_calculator_supports_arithmetic_and_safe_math_functions():
    calculator = Calculator()
    assert calculator.solve("2 + 3 * 4") == "14"
    assert calculator.solve("sqrt(81)") == "9"
    assert calculator.solve("round(pi, 2)") == "3.14"


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo unsafe')",
        "open('/etc/passwd').read()",
        "2 ** 1000",
        "1 / 0",
        "sqrt(-1)",
        "2 +",
        "True",
    ],
)
def test_calculator_rejects_unsafe_or_invalid_expressions(expression):
    assert Calculator().solve(expression) is None


def test_tool_catalog_only_exposes_read_only_tools():
    tools = ToolRegistry().list_tools()
    assert {tool["id"] for tool in tools} == {
        "calculator",
        "unit_converter",
        "world_clock",
        "study_planner",
        "text_analyzer",
    }
    assert all(tool["read_only"] is True for tool in tools)
    assert all(tool["requires_confirmation"] is False for tool in tools)


def test_registry_converts_units_and_temperature():
    registry = ToolRegistry()
    km = registry.execute("unit_converter", {"value": 5, "from_unit": "km", "to_unit": "m"})
    assert km["result"]["value"] == 5000
    celsius = registry.execute("unit_converter", {"value": 0, "from_unit": "c", "to_unit": "f"})
    assert celsius["result"]["value"] == 32


def test_registry_rejects_incompatible_units():
    with pytest.raises(ToolError):
        ToolRegistry().execute("unit_converter", {"value": 2, "from_unit": "km", "to_unit": "kg"})


def test_temperature_conversion_handles_same_unit_and_absolute_zero():
    registry = ToolRegistry()
    same = registry.execute("unit_converter", {"value": 20, "from_unit": "c", "to_unit": "c"})
    assert same["result"]["value"] == 20
    with pytest.raises(ToolError):
        registry.execute("unit_converter", {"value": -300, "from_unit": "c", "to_unit": "f"})


def test_registry_supports_data_and_energy_units():
    registry = ToolRegistry()
    data = registry.execute("unit_converter", {"value": 1, "from_unit": "gib", "to_unit": "gb"})
    assert data["result"]["value"] == 1.073741824
    energy = registry.execute("unit_converter", {"value": 1, "from_unit": "kwh", "to_unit": "j"})
    assert energy["result"]["value"] == 3600000
    electron_volt = registry.execute("unit_converter", {"value": 1, "from_unit": "ev", "to_unit": "j"})
    assert electron_volt["result"]["value"] == 1.602176634e-19


def test_world_clock_returns_timezone_aware_time():
    result = ToolRegistry().execute("world_clock", {"timezone": "Paris"})
    assert result["result"]["timezone"] == "Europe/Paris"
    assert "+01:00" in result["result"]["local_time"] or "+02:00" in result["result"]["local_time"]


def test_study_planner_creates_bounded_active_recall_schedule():
    result = ToolRegistry().execute(
        "study_planner",
        {"topic": "Algebra", "days": 5, "daily_minutes": 25},
    )["result"]
    assert len(result["sessions"]) == 5
    assert result["total_minutes"] == 125
    assert result["sessions"][0]["activity"]
    assert result["sessions"][-1]["activity"]


def test_text_analyzer_counts_content():
    result = ToolRegistry().execute("text_analyzer", {"text": "One short sentence. Another sentence!"})["result"]
    assert result["words"] == 5
    assert result["sentences"] == 2


def test_study_planner_rejects_boolean_and_fractional_limits():
    registry = ToolRegistry()
    with pytest.raises(ToolError):
        registry.execute("study_planner", {"topic": "Algebra", "days": True, "daily_minutes": 30})
    with pytest.raises(ToolError):
        registry.execute("study_planner", {"topic": "Algebra", "days": 3.5, "daily_minutes": 30})


def test_chat_router_only_runs_explicit_deterministic_requests():
    registry = ToolRegistry()
    calculation = registry.route_message("What is 12 * 8?")
    assert calculation["tool"] == "calculator"
    assert calculation["result"]["value"] == "96"
    conversion = registry.route_message("Convert 2 km to m")
    assert conversion["tool"] == "unit_converter"
    assert conversion["result"]["value"] == 2000
    assert registry.route_message("Explain photosynthesis in simple words.") is None
    text_analysis = registry.route_message("Analyze this text: Nova helps students learn. It adapts.")
    assert text_analysis["tool"] == "text_analyzer"
    assert text_analysis["result"]["words"] == 6


def test_unknown_tool_is_never_executed():
    with pytest.raises(ToolError):
        ToolRegistry().execute("shell", {"command": "echo unsafe"})
