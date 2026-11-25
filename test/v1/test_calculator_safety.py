import pytest

from backend.tools.calculator import Calculator


@pytest.fixture
def calculator():
    return Calculator()


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", "14"),
        ("(2 + 3) * 4", "20"),
        ("-5 + +2", "-3"),
        ("7 / 2", "3.5"),
        ("2 ** 10", "1024"),
        ("17 // 5", "3"),
        ("17 % 5", "2"),
    ],
)
def test_calculator_evaluates_supported_arithmetic(calculator, expression, expected):
    assert calculator.solve(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "   ",
        "print(1)",
        "__import__('os').system('echo unsafe')",
        "open('/tmp/nova').read()",
        "2 ** 1000000000",
        "2 ** -1000000000",
        "1 / 0",
        "0 / 0",
        "1e999",
        "True + 1",
        "[1, 2, 3]",
        "1 < 2",
        "1; 2",
        "x + 1",
    ],
)
def test_calculator_rejects_unsupported_or_unsafe_expressions(calculator, expression):
    assert calculator.solve(expression) is None


@pytest.mark.parametrize("value", [None, 123, 2.5, [], {}])
def test_calculator_rejects_non_string_input(calculator, value):
    assert calculator.solve(value) is None


def test_calculator_rejects_oversized_expressions(calculator):
    assert calculator.solve("1+" + ("1" * 300)) is None


def test_calculator_rejects_excessively_nested_expressions(calculator):
    expression = "(" * 30 + "1" + ")" * 30
    assert calculator.solve(expression) is None


def test_calculator_rejects_expressions_with_too_many_ast_nodes(calculator):
    expression = "+".join(["1"] * 80)
    assert calculator.solve(expression) is None
