from __future__ import annotations

import copy
import json
import os
import tempfile

from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional


class SettingsManager:

    """
    Central manager for Nova user settings.

    Responsibilities:

        - Provide safe default settings
        - Validate settings
        - Load settings from disk
        - Save settings safely
        - Merge partial updates
        - Reset settings
        - Prevent accidental mutation
        - Preserve backward compatibility
        - Support future migrations
        - Keep the existing Nova settings schema

    IMPORTANT:

        This class currently manages one settings object.

        Per-user settings should be implemented at the
        storage/API layer rather than silently changing
        the existing NovaCore contract.
    """

    VERSION = 1

    FILE_NAME = "settings.json"

    _lock = RLock()

    # ============================================================
    # VALID VALUES
    # ============================================================

    ALLOWED_LANGUAGES = {
        "English",
        "French",
    }

    ALLOWED_LEVELS = {
        "Middle School",
        "High School",
        "University",
    }

    ALLOWED_TEACHING_STYLES = {
        "adaptive",
        "step_by_step",
        "socratic",
        "direct",
    }

    ALLOWED_DIFFICULTIES = {
        "adaptive",
        "easy",
        "normal",
        "advanced",
    }

    ALLOWED_HINTS = {
        "when_needed",
        "always",
        "never",
    }

    ALLOWED_RESPONSE_LENGTHS = {
        "concise",
        "balanced",
        "detailed",
    }

    ALLOWED_TONES = {
        "friendly",
        "professional",
        "academic",
        "casual",
    }

    ALLOWED_CORRECTION_STYLES = {
        "explain",
        "gentle",
        "strict",
        "minimal",
    }

    ALLOWED_CREATIVITY = {
        "low",
        "medium",
        "high",
    }

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(
        self,
        file: Optional[str | Path] = None
    ):

        self.file = (
            Path(file)
            if file is not None
            else Path("data") / self.FILE_NAME
        )

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.data: Dict[str, Any] = {}

        self._load()

    # ============================================================
    # DEFAULT SETTINGS
    # ============================================================

    @classmethod
    def default_settings(cls) -> Dict[str, Any]:

        return {

            # ====================================================
            # SYSTEM
            # ====================================================

            "_version": cls.VERSION,


            # ====================================================
            # PROFILE
            # ====================================================

            "name": "",

            "language": "English",

            "level": "High School",


            # ====================================================
            # TEACHING
            # ====================================================

            "teaching_style": "adaptive",

            "difficulty": "adaptive",

            "hints": "when_needed",

            "step_by_step": True,

            "adaptive_learning": True,


            # ====================================================
            # RESPONSE
            # ====================================================

            "response_length": "balanced",

            "tone": "friendly",

            "use_examples": True,

            "use_analogies": True,

            "encouragement": True,


            # ====================================================
            # CORRECTIONS
            # ====================================================

            "correction_style": "explain",

            "show_correct_answer": True,


            # ====================================================
            # AI
            # ====================================================

            "creativity": "medium",


            # ====================================================
            # PERSONALIZATION
            # ====================================================

            "behavior": "",

            "custom_instructions": "",
        }

    # ============================================================
    # LOAD
    # ============================================================

    def _load(self) -> None:

        with self._lock:

            if not self.file.exists():

                self.data = self.default_settings()

                self._save_locked()

                return

            try:

                raw = self.file.read_text(
                    encoding="utf-8"
                )

                parsed = json.loads(raw)

            except (
                OSError,
                json.JSONDecodeError,
                UnicodeDecodeError
            ):

                # Never let a broken settings file
                # prevent Nova from starting.

                self.data = self.default_settings()

                self._save_locked()

                return

            if not isinstance(parsed, dict):

                self.data = self.default_settings()

                self._save_locked()

                return

            self.data = parsed

            changed = self.ensure_defaults(
                save=False
            )

            changed |= self.validate_all(
                save=False
            )

            changed |= self._migrate(
                save=False
            )

            if changed:

                self._save_locked()

    # ============================================================
    # MIGRATION
    # ============================================================

    def _migrate(
        self,
        save: bool = True
    ) -> bool:

        changed = False

        version = self.data.get(
            "_version",
            0
        )

        try:

            version = int(version)

        except (
            TypeError,
            ValueError
        ):

            version = 0

        # --------------------------------------------------------
        # Future migrations go here.
        #
        # Example:
        #
        # if version < 2:
        #
        #     ...
        #
        #     version = 2
        #     changed = True
        # --------------------------------------------------------

        if self.data.get("_version") != self.VERSION:

            self.data["_version"] = self.VERSION

            changed = True

        if changed and save:

            self.save()

        return changed

    # ============================================================
    # ENSURE DEFAULTS
    # ============================================================

    def ensure_defaults(
        self,
        save: bool = True
    ) -> bool:

        defaults = self.default_settings()

        changed = False

        for key, default_value in defaults.items():

            if key not in self.data:

                self.data[key] = copy.deepcopy(
                    default_value
                )

                changed = True

        if changed and save:

            self.save()

        return changed

    # ============================================================
    # VALIDATE ALL
    # ============================================================

    def validate_all(
        self,
        save: bool = True
    ) -> bool:

        changed = False

        defaults = self.default_settings()

        # --------------------------------------------------------
        # Strings
        # --------------------------------------------------------

        string_fields = {

            "name": "",

            "behavior": "",

            "custom_instructions": "",
        }

        for key, fallback in string_fields.items():

            value = self.data.get(key)

            if not isinstance(value, str):

                self.data[key] = fallback

                changed = True

        # --------------------------------------------------------
        # Languages
        # --------------------------------------------------------

        changed |= self._validate_choice(
            "language",
            self.ALLOWED_LANGUAGES,
            defaults["language"]
        )

        changed |= self._validate_choice(
            "level",
            self.ALLOWED_LEVELS,
            defaults["level"]
        )

        changed |= self._validate_choice(
            "teaching_style",
            self.ALLOWED_TEACHING_STYLES,
            defaults["teaching_style"]
        )

        changed |= self._validate_choice(
            "difficulty",
            self.ALLOWED_DIFFICULTIES,
            defaults["difficulty"]
        )

        changed |= self._validate_choice(
            "hints",
            self.ALLOWED_HINTS,
            defaults["hints"]
        )

        changed |= self._validate_choice(
            "response_length",
            self.ALLOWED_RESPONSE_LENGTHS,
            defaults["response_length"]
        )

        changed |= self._validate_choice(
            "tone",
            self.ALLOWED_TONES,
            defaults["tone"]
        )

        changed |= self._validate_choice(
            "correction_style",
            self.ALLOWED_CORRECTION_STYLES,
            defaults["correction_style"]
        )

        changed |= self._validate_choice(
            "creativity",
            self.ALLOWED_CREATIVITY,
            defaults["creativity"]
        )

        # --------------------------------------------------------
        # Booleans
        # --------------------------------------------------------

        boolean_fields = {

            "step_by_step":
                defaults["step_by_step"],

            "adaptive_learning":
                defaults["adaptive_learning"],

            "use_examples":
                defaults["use_examples"],

            "use_analogies":
                defaults["use_analogies"],

            "encouragement":
                defaults["encouragement"],

            "show_correct_answer":
                defaults["show_correct_answer"],
        }

        for key, fallback in boolean_fields.items():

            value = self.data.get(key)

            if not isinstance(value, bool):

                self.data[key] = fallback

                changed = True

        if save and changed:

            self.save()

        return changed

    # ============================================================
    # VALIDATE CHOICE
    # ============================================================

    def _validate_choice(
        self,
        key: str,
        allowed: set[str],
        fallback: str
    ) -> bool:

        value = self.data.get(key)

        if value not in allowed:

            self.data[key] = fallback

            return True

        return False

    # ============================================================
    # SAVE
    # ============================================================

    def save(self) -> None:

        with self._lock:

            self._save_locked()

    # ============================================================
    # INTERNAL SAVE
    # ============================================================

    def _save_locked(self) -> None:

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        payload = json.dumps(
            self.data,
            indent=4,
            ensure_ascii=False
        )

        # --------------------------------------------------------
        # Atomic write.
        #
        # We write to a temporary file first, then replace the
        # original. This greatly reduces the risk of leaving
        # settings.json half-written after a crash.
        # --------------------------------------------------------

        temporary_path = None

        try:

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.file.parent,
                prefix=".settings_",
                suffix=".tmp",
                delete=False
            ) as temporary:

                temporary.write(payload)

                temporary.flush()

                os.fsync(
                    temporary.fileno()
                )

                temporary_path = Path(
                    temporary.name
                )

            os.replace(
                temporary_path,
                self.file
            )

            temporary_path = None

        finally:

            if (
                temporary_path is not None
                and temporary_path.exists()
            ):

                try:

                    temporary_path.unlink()

                except OSError:

                    pass

    # ============================================================
    # GET
    # ============================================================

    def get(self) -> Dict[str, Any]:

        with self._lock:

            self.ensure_defaults(
                save=False
            )

            self.validate_all(
                save=False
            )

            return copy.deepcopy(
                self.data
            )

    # ============================================================
    # GET ONE
    # ============================================================

    def get_value(
        self,
        key: str,
        default: Any = None
    ) -> Any:

        with self._lock:

            if key not in self.data:

                return default

            return copy.deepcopy(
                self.data[key]
            )

    # ============================================================
    # HAS
    # ============================================================

    def has(
        self,
        key: str
    ) -> bool:

        with self._lock:

            return key in self.data

    # ============================================================
    # UPDATE
    # ============================================================

    def update(
        self,
        name=None,
        language=None,
        level=None,
        teaching_style=None,
        difficulty=None,
        hints=None,
        step_by_step=None,
        adaptive_learning=None,
        response_length=None,
        tone=None,
        use_examples=None,
        use_analogies=None,
        encouragement=None,
        correction_style=None,
        show_correct_answer=None,
        creativity=None,
        behavior=None,
        custom_instructions=None
    ) -> Dict[str, Any]:

        values = {

            "name": name,

            "language": language,

            "level": level,

            "teaching_style":
                teaching_style,

            "difficulty":
                difficulty,

            "hints":
                hints,

            "step_by_step":
                step_by_step,

            "adaptive_learning":
                adaptive_learning,

            "response_length":
                response_length,

            "tone":
                tone,

            "use_examples":
                use_examples,

            "use_analogies":
                use_analogies,

            "encouragement":
                encouragement,

            "correction_style":
                correction_style,

            "show_correct_answer":
                show_correct_answer,

            "creativity":
                creativity,

            "behavior":
                behavior,

            "custom_instructions":
                custom_instructions,
        }

        return self.update_dict(
            values
        )

    # ============================================================
    # UPDATE DICTIONARY
    # ============================================================

    def update_dict(
        self,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not isinstance(values, dict):

            raise TypeError(
                "Settings update must be a dictionary."
            )

        with self._lock:

            changed = False

            defaults = self.default_settings()

            for key, value in values.items():

                # ------------------------------------------------
                # Ignore unknown internal metadata.
                # ------------------------------------------------

                if key.startswith("_"):

                    continue

                # ------------------------------------------------
                # Ignore completely unknown settings.
                #
                # This prevents arbitrary JSON from silently
                # becoming part of Nova's settings schema.
                # ------------------------------------------------

                if key not in defaults:

                    continue

                if key == "_version":

                    continue

                # ------------------------------------------------
                # Validate before storing.
                # ------------------------------------------------

                validated = self._validate_value(
                    key,
                    value,
                    defaults[key]
                )

                if self.data.get(key) != validated:

                    self.data[key] = validated

                    changed = True

            if changed:

                self.data["_version"] = self.VERSION

                self._save_locked()

            return copy.deepcopy(
                self.data
            )

    # ============================================================
    # VALIDATE VALUE
    # ============================================================

    def _validate_value(
        self,
        key: str,
        value: Any,
        fallback: Any
    ) -> Any:

        # --------------------------------------------------------
        # String settings
        # --------------------------------------------------------

        if key in {
            "name",
            "behavior",
            "custom_instructions"
        }:

            if not isinstance(value, str):

                return fallback

            return value.strip()

        # --------------------------------------------------------
        # Boolean settings
        # --------------------------------------------------------

        if key in {
            "step_by_step",
            "adaptive_learning",
            "use_examples",
            "use_analogies",
            "encouragement",
            "show_correct_answer"
        }:

            if not isinstance(value, bool):

                return fallback

            return value

        # --------------------------------------------------------
        # Choice settings
        # --------------------------------------------------------

        choices = {

            "language":
                self.ALLOWED_LANGUAGES,

            "level":
                self.ALLOWED_LEVELS,

            "teaching_style":
                self.ALLOWED_TEACHING_STYLES,

            "difficulty":
                self.ALLOWED_DIFFICULTIES,

            "hints":
                self.ALLOWED_HINTS,

            "response_length":
                self.ALLOWED_RESPONSE_LENGTHS,

            "tone":
                self.ALLOWED_TONES,

            "correction_style":
                self.ALLOWED_CORRECTION_STYLES,

            "creativity":
                self.ALLOWED_CREATIVITY,
        }

        allowed = choices.get(key)

        if allowed is not None:

            if value not in allowed:

                return fallback

            return value

        return fallback

    # ============================================================
    # SET ONE VALUE
    # ============================================================

    def set(
        self,
        key: str,
        value: Any
    ) -> Dict[str, Any]:

        return self.update_dict({

            key: value

        })

    # ============================================================
    # RESET
    # ============================================================

    def reset(self) -> Dict[str, Any]:

        with self._lock:

            self.data = self.default_settings()

            self._save_locked()

            return copy.deepcopy(
                self.data
            )

    # ============================================================
    # RESET ONE
    # ============================================================

    def reset_key(
        self,
        key: str
    ) -> Dict[str, Any]:

        defaults = self.default_settings()

        if key not in defaults:

            raise KeyError(
                f"Unknown setting: {key}"
            )

        with self._lock:

            self.data[key] = copy.deepcopy(
                defaults[key]
            )

            self._save_locked()

            return copy.deepcopy(
                self.data
            )

    # ============================================================
    # VALIDATE CURRENT SETTINGS
    # ============================================================

    def validate(self) -> Dict[str, Any]:

        with self._lock:

            self.ensure_defaults(
                save=False
            )

            self.validate_all(
                save=False
            )

            return copy.deepcopy(
                self.data
            )

    # ============================================================
    # EXPORT
    # ============================================================

    def export(self) -> Dict[str, Any]:

        return self.get()

    # ============================================================
    # IMPORT
    # ============================================================

    def import_settings(
        self,
        values: Dict[str, Any],
        replace: bool = False
    ) -> Dict[str, Any]:

        if not isinstance(values, dict):

            raise TypeError(
                "Imported settings must be a dictionary."
            )

        if replace:

            defaults = self.default_settings()

            cleaned = {}

            for key, default in defaults.items():

                if key in values:

                    cleaned[key] = self._validate_value(
                        key,
                        values[key],
                        default
                    )

                else:

                    cleaned[key] = copy.deepcopy(
                        default
                    )

            cleaned["_version"] = self.VERSION

            with self._lock:

                self.data = cleaned

                self._save_locked()

                return copy.deepcopy(
                    self.data
                )

        return self.update_dict(
            values
        )

    # ============================================================
    # FILE INFO
    # ============================================================

    def exists(self) -> bool:

        return self.file.exists()

    # ============================================================
    # PATH
    # ============================================================

    def get_path(self) -> str:

        return str(
            self.file
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self) -> Dict[str, Any]:

        settings = self.get()

        return {

            "version":
                settings.get(
                    "_version",
                    self.VERSION
                ),

            "name":
                settings.get(
                    "name",
                    ""
                ),

            "language":
                settings.get(
                    "language",
                    "English"
                ),

            "level":
                settings.get(
                    "level",
                    "High School"
                ),

            "teaching_style":
                settings.get(
                    "teaching_style",
                    "adaptive"
                ),

            "difficulty":
                settings.get(
                    "difficulty",
                    "adaptive"
                ),

            "response_length":
                settings.get(
                    "response_length",
                    "balanced"
                ),

            "tone":
                settings.get(
                    "tone",
                    "friendly"
                ),

            "adaptive_learning":
                settings.get(
                    "adaptive_learning",
                    True
                ),

            "creativity":
                settings.get(
                    "creativity",
                    "medium"
                ),
        }