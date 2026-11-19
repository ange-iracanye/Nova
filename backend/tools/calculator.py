"""A small, safe arithmetic evaluator for Nova.

Only numeric constants, arithmetic operators and an explicit allowlist of
math functions are accepted. Python code execution is never used.
"""
from __future__ import annotations

import ast
import math
import operator
import re


class Calculator:
    MAX_EXPRESSION_LENGTH = 200
    MAX_AST_NODES = 60
    MAX_DEPTH = 12
    MAX_ABS_RESULT = 1e100

    _BINARY = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    _FUNCTIONS = {
        "abs": abs,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "floor": math.floor,
        "ceil": math.ceil,
        "round": round,
    }
    _CONSTANTS = {"pi": math.pi, "e": math.e}

    def solve(self, text):
        if not isinstance(text, str):
            return None
        expression = text.strip().replace("^", "**")
        if not expression or len(expression) > self.MAX_EXPRESSION_LENGTH:
            return None
        if not re.fullmatch(r"[0-9a-zA-Z_\s+\-*/().,%*]+", expression):
            return None
        try:
            tree = ast.parse(expression, mode="eval")
            nodes = list(ast.walk(tree))
            if len(nodes) > self.MAX_AST_NODES:
                return None
            result = self._evaluate(tree.body, 0)
            if isinstance(result, bool) or not isinstance(result, (int, float)):
                return None
            if not math.isfinite(float(result)) or abs(float(result)) > self.MAX_ABS_RESULT:
                return None
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            if isinstance(result, float):
                return format(result, ".12g")
            return str(result)
        except (ArithmeticError, SyntaxError, TypeError, ValueError, OverflowError, RecursionError):
            return None

    def _evaluate(self, node, depth):
        if depth > self.MAX_DEPTH:
            raise ValueError("Expression is too deeply nested.")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > self.MAX_ABS_RESULT:
                raise ValueError("Number is too large.")
            return node.value
        if isinstance(node, ast.Name) and node.id in self._CONSTANTS:
            return self._CONSTANTS[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._UNARY:
            return self._UNARY[type(node.op)](self._evaluate(node.operand, depth + 1))
        if isinstance(node, ast.BinOp) and type(node.op) in self._BINARY:
            left = self._evaluate(node.left, depth + 1)
            right = self._evaluate(node.right, depth + 1)
            if isinstance(node.op, ast.Pow) and abs(float(right)) > 100:
                raise ValueError("Exponent is too large.")
            return self._BINARY[type(node.op)](left, right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function = self._FUNCTIONS.get(node.func.id)
            if function is None or node.keywords or len(node.args) > 2:
                raise ValueError("Unsupported function.")
            arguments = [self._evaluate(arg, depth + 1) for arg in node.args]
            return function(*arguments)
        raise ValueError("Unsupported expression.")
