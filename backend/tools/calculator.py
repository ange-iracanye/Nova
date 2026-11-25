"""Safe, bounded arithmetic expression evaluator for Nova."""

from __future__ import annotations

import ast
import math
import operator


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

MAX_EXPRESSION_LENGTH = 256
MAX_AST_NODES = 64
MAX_AST_DEPTH = 16
MAX_ABS_RESULT = 1e100
MAX_INTEGER_BITS = 512
MAX_EXPONENT = 100


class Calculator:
    """Evaluate simple arithmetic without executing arbitrary Python code."""

    def _evaluate(self, node: ast.AST, depth: int = 0):
        if depth > MAX_AST_DEPTH:
            raise ValueError("Expression is too deeply nested.")

        if isinstance(node, ast.Expression):
            return self._evaluate(node.body, depth + 1)

        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Only numeric literals are supported.")
            self._validate_number(value)
            return value

        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            result = _UNARY_OPERATORS[type(node.op)](
                self._evaluate(node.operand, depth + 1)
            )
            self._validate_number(result)
            return result

        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left = self._evaluate(node.left, depth + 1)
            right = self._evaluate(node.right, depth + 1)
            if isinstance(node.op, ast.Pow):
                if abs(right) > MAX_EXPONENT:
                    raise ValueError("Exponent is outside the supported range.")
                if left == 0 and right < 0:
                    raise ValueError("Zero cannot have a negative exponent.")
            result = _BINARY_OPERATORS[type(node.op)](left, right)
            self._validate_number(result)
            return result

        raise ValueError("Unsupported expression.")

    @staticmethod
    def _validate_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Invalid numeric result.")
        if isinstance(value, int):
            if value.bit_length() > MAX_INTEGER_BITS:
                raise ValueError("Integer result is too large.")
        elif not math.isfinite(value) or abs(value) > MAX_ABS_RESULT:
            raise ValueError("Numeric result is outside the supported range.")

    def solve(self, text):
        if not isinstance(text, str):
            return None
        expression = text.strip()
        if not expression or len(expression) > MAX_EXPRESSION_LENGTH:
            return None

        try:
            tree = ast.parse(expression, mode="eval")
            if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
                return None
            result = self._evaluate(tree)
            return str(result)
        except (
            ArithmeticError,
            OverflowError,
            SyntaxError,
            TypeError,
            ValueError,
        ):
            return None
