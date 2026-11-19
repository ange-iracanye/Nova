"""Safe, deterministic tools that extend Nova beyond text generation.

The registry deliberately exposes only bounded, read-only local operations.
External integrations must be registered separately with explicit user consent.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.tools.calculator import Calculator


class ToolError(ValueError):
    """A tool request is invalid or outside its supported limits."""


class ToolRegistry:
    VERSION = "1.0.0"
    MAX_TEXT_LENGTH = 20_000

    TOOL_CATALOG = (
        {
            "id": "calculator",
            "name": "Calculator",
            "category": "math",
            "description": "Safely evaluate arithmetic expressions and common mathematical functions.",
            "read_only": True,
            "requires_confirmation": False,
            "input_schema": {"expression": "string"},
        },
        {
            "id": "unit_converter",
            "name": "Unit converter",
            "category": "utilities",
            "description": "Convert common length, mass, time, volume, speed and temperature units.",
            "read_only": True,
            "requires_confirmation": False,
            "input_schema": {"value": "number", "from_unit": "string", "to_unit": "string"},
        },
        {
            "id": "world_clock",
            "name": "World clock",
            "category": "utilities",
            "description": "Get the current local date and time in a supported IANA timezone or city.",
            "read_only": True,
            "requires_confirmation": False,
            "input_schema": {"timezone": "string"},
        },
        {
            "id": "study_planner",
            "name": "Study planner",
            "category": "learning",
            "description": "Create a realistic study schedule with spaced review and active recall.",
            "read_only": True,
            "requires_confirmation": False,
            "input_schema": {"topic": "string", "days": "integer", "daily_minutes": "integer"},
        },
        {
            "id": "text_analyzer",
            "name": "Text analyzer",
            "category": "writing",
            "description": "Count words, characters, sentences, paragraphs and estimated reading time.",
            "read_only": True,
            "requires_confirmation": False,
            "input_schema": {"text": "string"},
        },
    )

    UNIT_GROUPS = {
        "length": {
            "m": 1.0, "meter": 1.0, "meters": 1.0, "metre": 1.0, "metres": 1.0,
            "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0, "kilometre": 1000.0, "kilometres": 1000.0,
            "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01, "mm": 0.001, "millimeter": 0.001,
            "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
            "ft": 0.3048, "foot": 0.3048, "feet": 0.3048, "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
        },
        "mass": {
            "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
            "g": 0.001, "gram": 0.001, "grams": 0.001,
            "mg": 0.000001, "milligram": 0.000001, "milligrams": 0.000001,
            "lb": 0.45359237, "lbs": 0.45359237, "pound": 0.45359237, "pounds": 0.45359237,
            "oz": 0.028349523125, "ounce": 0.028349523125, "ounces": 0.028349523125,
        },
        "time": {
            "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
            "min": 60.0, "minute": 60.0, "minutes": 60.0,
            "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0,
            "day": 86400.0, "days": 86400.0,
        },
        "volume": {
            "l": 1.0, "liter": 1.0, "litre": 1.0, "liters": 1.0, "litres": 1.0,
            "ml": 0.001, "milliliter": 0.001, "millilitre": 0.001,
            "m3": 1000.0, "gallon": 3.785411784, "gallons": 3.785411784, "gal": 3.785411784,
        },
        "speed": {
            "m/s": 1.0, "mps": 1.0, "km/h": 1 / 3.6, "kph": 1 / 3.6,
            "mph": 0.44704, "mi/h": 0.44704,
        },
    }
    TIMEZONES = {
        "utc": "UTC", "london": "Europe/London", "paris": "Europe/Paris",
        "berlin": "Europe/Berlin", "madrid": "Europe/Madrid", "rome": "Europe/Rome",
        "new york": "America/New_York", "los angeles": "America/Los_Angeles",
        "chicago": "America/Chicago", "toronto": "America/Toronto",
        "dubai": "Asia/Dubai", "nairobi": "Africa/Nairobi", "lagos": "Africa/Lagos",
        "tokyo": "Asia/Tokyo", "singapore": "Asia/Singapore", "kolkata": "Asia/Kolkata",
        "sydney": "Australia/Sydney", "auckland": "Pacific/Auckland",
    }

    def __init__(self) -> None:
        self.calculator = Calculator()
        self._handlers = {
            "calculator": self._calculator,
            "unit_converter": self._unit_converter,
            "world_clock": self._world_clock,
            "study_planner": self._study_planner,
            "text_analyzer": self._text_analyzer,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [dict(item, input_schema=dict(item["input_schema"])) for item in self.TOOL_CATALOG]

    def execute(self, tool_id: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if tool_id not in self._handlers:
            raise ToolError("This tool is not available.")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be an object.")
        started = datetime.now(timezone.utc)
        result = self._handlers[tool_id](arguments)
        return {
            "tool": tool_id,
            "result": result,
            "source": "nova_local_tool",
            "read_only": True,
            "requires_confirmation": False,
            "duration_ms": max(0, int((datetime.now(timezone.utc) - started).total_seconds() * 1000)),
        }

    def route_message(self, message: str) -> dict[str, Any] | None:
        """Run a deterministic tool only when the user's wording is explicit."""
        text = str(message or "").strip()
        if not text or len(text) > 2_000:
            return None

        unit_match = re.search(
            r"\b(?:convert|how many|what is)\s+([+-]?\d+(?:[.,]\d+)?)\s*([a-zA-Z°/]+)\s+(?:to|into|in)\s+([a-zA-Z°/]+)\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )
        if unit_match:
            value, source, target = unit_match.groups()
            try:
                return self.execute("unit_converter", {
                    "value": float(value.replace(",", ".")),
                    "from_unit": source,
                    "to_unit": target,
                })
            except ToolError:
                pass

        time_match = re.search(
            r"\b(?:what time is it|current time|time now)\s+(?:in|at)\s+([a-zA-Z_ /-]+?)\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )
        if time_match:
            try:
                return self.execute("world_clock", {"timezone": time_match.group(1).strip()})
            except ToolError:
                pass

        plan_match = re.search(
            r"\b(?:create|make|build|prepare)\s+(?:me\s+)?(?:a\s+)?study plan\s+(?:for|about)\s+(.+?)\s+(?:in|over|for)\s+(\d{1,3})\s+days?(?:\s+(?:at|with)\s+(\d{1,3})\s+minutes?(?:\s+per\s+day)?)?\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )
        if plan_match:
            topic, days, minutes = plan_match.groups()
            try:
                return self.execute("study_planner", {
                    "topic": topic.strip(),
                    "days": int(days),
                    "daily_minutes": int(minutes or 30),
                })
            except ToolError:
                pass

        candidate = text.rstrip("?.! ")
        candidate = re.sub(r"^(?:please\s+)?(?:calculate|compute|what is|what's|solve)\s+", "", candidate, flags=re.IGNORECASE)
        if re.fullmatch(r"[0-9\s+\-*/().%^,a-zA-Z_]+", candidate) and re.search(r"\d", candidate):
            result = self.execute("calculator", {"expression": candidate.replace("^", "**")})
            return result

        return None

    def _calculator(self, args: dict[str, Any]) -> dict[str, Any]:
        expression = str(args.get("expression") or "").strip()
        if not expression or len(expression) > 200:
            raise ToolError("Enter an arithmetic expression of at most 200 characters.")
        result = self.calculator.solve(expression)
        if result is None:
            raise ToolError("That expression is not supported. Use numbers, arithmetic operators and supported math functions.")
        return {"expression": expression, "value": result}

    def _unit_converter(self, args: dict[str, Any]) -> dict[str, Any]:
        if isinstance(args.get("value"), bool):
            raise ToolError("The value must be a number, not a boolean.")
        try:
            value = float(args.get("value"))
        except (TypeError, ValueError):
            raise ToolError("The value must be a number.")
        if not isfinite(value) or abs(value) > 1e15:
            raise ToolError("The value is outside the supported range.")
        source = self._normalize_unit(args.get("from_unit"))
        target = self._normalize_unit(args.get("to_unit"))
        temperature_units = {"c", "f", "k"}
        if source in temperature_units and target in temperature_units:
            if source == "c":
                kelvin = value + 273.15
            elif source == "f":
                kelvin = (value - 32) * 5 / 9 + 273.15
            else:
                kelvin = value
            if kelvin < 0:
                raise ToolError("Temperatures cannot be below absolute zero.")
            if target == "c":
                converted = kelvin - 273.15
            elif target == "f":
                converted = (kelvin - 273.15) * 9 / 5 + 32
            else:
                converted = kelvin
            group = "temperature"
        else:
            group, source_factor = self._find_unit(source)
            target_group, target_factor = self._find_unit(target)
            if group != target_group:
                raise ToolError("Those units belong to different measurement categories.")
            converted = value * source_factor / target_factor
        if not isfinite(converted):
            raise ToolError("The conversion result is outside the supported range.")
        return {"input": value, "from_unit": source, "to_unit": target, "value": round(converted, 10), "category": group}

    def _world_clock(self, args: dict[str, Any]) -> dict[str, Any]:
        requested = str(args.get("timezone") or "").strip()
        if not requested or len(requested) > 80:
            raise ToolError("Provide a city or IANA timezone.")
        zone_name = self.TIMEZONES.get(requested.lower(), requested)
        try:
            zone = ZoneInfo(zone_name)
        except (ZoneInfoNotFoundError, ValueError):
            raise ToolError("That timezone is not supported. Try Europe/Paris, America/New_York or Asia/Tokyo.")
        now = datetime.now(timezone.utc).astimezone(zone)
        return {"timezone": zone.key, "local_time": now.isoformat(), "formatted": now.strftime("%A %d %B %Y, %H:%M:%S %Z")}

    def _study_planner(self, args: dict[str, Any]) -> dict[str, Any]:
        topic = str(args.get("topic") or "").strip()
        if len(topic) < 2 or len(topic) > 180:
            raise ToolError("The topic must contain between 2 and 180 characters.")
        try:
            days = int(args.get("days", 7))
            minutes = int(args.get("daily_minutes", 30))
        except (TypeError, ValueError):
            raise ToolError("Days and daily minutes must be whole numbers.")
        if isinstance(args.get("days", 7), bool) or isinstance(args.get("daily_minutes", 30), bool):
            raise ToolError("Days and daily minutes must be whole numbers.")
        if not 1 <= days <= 90 or not 5 <= minutes <= 240:
            raise ToolError("Choose 1–90 days and 5–240 minutes per day.")
        today = datetime.now().date()
        sessions = []
        for index in range(days):
            day = today + timedelta(days=index)
            if index == 0:
                activity = "Map what you know, identify gaps, and learn the core ideas."
            elif index in {1, 3, 6, 13, 20}:
                activity = "Use active recall, then correct gaps without looking at your notes."
            elif index == days - 1:
                activity = "Complete a mixed self-test and review the remaining weak points."
            elif index % 4 == 0:
                activity = "Complete a short practice set and explain your reasoning."
            else:
                activity = "Study one subtopic, then solve a small example from memory."
            sessions.append({"day": index + 1, "date": day.isoformat(), "minutes": minutes, "activity": activity})
        return {"topic": topic, "duration_days": days, "daily_minutes": minutes, "total_minutes": days * minutes, "sessions": sessions}

    def _text_analyzer(self, args: dict[str, Any]) -> dict[str, Any]:
        text = str(args.get("text") or "")
        if len(text) > self.MAX_TEXT_LENGTH:
            raise ToolError(f"Text is limited to {self.MAX_TEXT_LENGTH} characters.")
        words = re.findall(r"\b[\wÀ-ÿ’'-]+\b", text, flags=re.UNICODE)
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part]
        paragraphs = [part for part in re.split(r"\n\s*\n", text.strip()) if part]
        return {
            "characters": len(text),
            "characters_without_spaces": len(re.sub(r"\s+", "", text)),
            "words": len(words),
            "sentences": len(sentences),
            "paragraphs": len(paragraphs),
            "estimated_reading_minutes": round(len(words) / 220, 1),
        }

    @staticmethod
    def _normalize_unit(value: Any) -> str:
        unit = str(value or "").strip().lower().replace(" ", "")
        aliases = {"°c": "c", "celsius": "c", "°f": "f", "fahrenheit": "f", "kelvin": "k"}
        return aliases.get(unit, unit)

    def _find_unit(self, unit: str) -> tuple[str, float]:
        for group, units in self.UNIT_GROUPS.items():
            if unit in units:
                return group, units[unit]
        raise ToolError(f"Unsupported unit: {unit}")
