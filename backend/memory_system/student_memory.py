import json
import hashlib
import math
from copy import deepcopy
from pathlib import Path
from datetime import datetime


class StudentMemory:

    def __init__(self, user_email=None):

        self.base_path = Path(
            "data/memory/students"
        )

        self.base_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.user_email = (
            user_email.strip().lower()
            if user_email
            else None
        )

        self.file = self._get_file()

        if self.file.exists():

            try:

                self.memory = json.loads(
                    self.file.read_text(
                        encoding="utf-8"
                    )
                )

            except (OSError, ValueError, TypeError, UnicodeError):

                self.memory = self.default()

            self.memory = self._normalize_memory(self.memory)

        else:

            self.memory = self.default()

            self.save()


    # =====================================
    # USER FILE
    # =====================================

    def _get_file(self):

        if not self.user_email:

            return (
                self.base_path
                / "default_student.json"
            )

        user_id = hashlib.sha256(
            self.user_email.encode("utf-8")
        ).hexdigest()

        return (
            self.base_path
            / f"{user_id}.json"
        )


    # =====================================
    # DEFAULT
    # =====================================

    def default(self):

        return {

            "version": 1,

            "concepts_learned": {},

            "mistakes": [],

            "preferences": {},

            "goals": [],

            "strengths": [],

            "weaknesses": [],

            "progress": {},

            "facts": [],

            "explicit_memories": [],

            "statistics": {

                "total_concepts": 0,

                "total_mistakes": 0,

                "total_facts": 0,

                "total_goals": 0,

                "last_updated": None
            }
        }


    # =====================================
    # NORMALIZE PERSISTED DATA
    # =====================================

    def _normalize_memory(self, value):
        result = self.default()
        if not isinstance(value, dict):
            return result

        for key in ("concepts_learned", "preferences", "progress"):
            item = value.get(key)
            result[key] = item if isinstance(item, dict) else {}

        concepts = {}
        for subject, records in result["concepts_learned"].items():
            if isinstance(records, dict):
                concepts[str(subject)] = {
                    str(name): {
                        "confidence": self._safe_confidence(record.get("confidence", 50)),
                        "attempts": self._safe_count(record.get("attempts")),
                        "first_seen": record.get("first_seen") if isinstance(record.get("first_seen"), str) else None,
                        "last_seen": record.get("last_seen") if isinstance(record.get("last_seen"), str) else None,
                    }
                    for name, record in records.items()
                    if isinstance(record, dict)
                }
        result["concepts_learned"] = concepts

        for key in ("mistakes", "goals", "strengths", "weaknesses", "facts", "explicit_memories"):
            item = value.get(key)
            result[key] = item if isinstance(item, list) else []

        stats = value.get("statistics")
        result["statistics"] = {
            **result["statistics"],
            **(stats if isinstance(stats, dict) else {}),
        }
        result["version"] = 1
        return result

    @staticmethod
    def _safe_count(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError, OverflowError):
            return 0

    @staticmethod
    def _safe_confidence(value):
        try:
            confidence = float(value)
        except (TypeError, ValueError, OverflowError):
            return 50.0
        if not math.isfinite(confidence):
            return 50.0
        return max(0.0, min(100.0, confidence))

    @staticmethod
    def _json_safe(value):
        if isinstance(value, dict):
            return {str(key): StudentMemory._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [StudentMemory._json_safe(item) for item in value]
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return None

    # =====================================
    # SAVE
    # =====================================

    def save(self):

        self.memory = self._normalize_memory(self.memory)

        self.memory[
            "statistics"
        ][
            "total_concepts"
        ] = sum(

            len(subject)

            for subject
            in self.memory[
                "concepts_learned"
            ].values()
        )

        self.memory[
            "statistics"
        ][
            "total_mistakes"
        ] = len(
            self.memory[
                "mistakes"
            ]
        )

        self.memory[
            "statistics"
        ][
            "total_facts"
        ] = len(
            self.memory[
                "facts"
            ]
        )

        self.memory[
            "statistics"
        ][
            "total_goals"
        ] = len(
            self.memory[
                "goals"
            ]
        )

        self.memory[
            "statistics"
        ][
            "last_updated"
        ] = (
            datetime.now()
            .isoformat()
        )

        temporary = self.file.with_suffix(
            ".tmp"
        )

        temporary.write_text(

            json.dumps(
                self._json_safe(self.memory),
                indent=4,
                ensure_ascii=False,
                allow_nan=False,
            ),

            encoding="utf-8"
        )

        temporary.replace(
            self.file
        )


    # =====================================
    # LEARN CONCEPT
    # =====================================

    def learn_concept(
        self,
        subject,
        concept,
        confidence
    ):

        if not subject or not concept:

            return

        if subject not in self.memory[
            "concepts_learned"
        ]:

            self.memory[
                "concepts_learned"
            ][subject] = {}


        concepts = self.memory[
            "concepts_learned"
        ][subject]


        now = (
            datetime.now()
            .isoformat()
        )


        if concept not in concepts:

            concepts[concept] = {

                "confidence":
                    self._safe_confidence(confidence),

                "attempts":
                    1,

                "first_seen":
                    now,

                "last_seen":
                    now
            }

        else:

            concepts[concept]["confidence"] = self._safe_confidence(confidence)

            concepts[concept]["attempts"] = self._safe_count(concepts[concept].get("attempts")) + 1

            concepts[concept][
                "last_seen"
            ] = now


        self.save()


    # =====================================
    # MISTAKE
    # =====================================

    def add_mistake(
        self,
        mistake,
        subject=None
    ):

        if not mistake:

            return

        self.memory[
            "mistakes"
        ].append({

            "text":
                mistake,

            "subject":
                subject,

            "timestamp":
                datetime.now()
                .isoformat()
        })

        self.save()


    # =====================================
    # ADD FACT
    # =====================================

    def add_fact(
        self,
        text,
        subject=None,
        confidence=0.8
    ):

        if not text:

            return

        self.memory[
            "facts"
        ].append({

            "text":
                text,

            "subject":
                subject,

            "confidence":
                confidence,

            "timestamp":
                datetime.now()
                .isoformat()
        })

        self.save()


    # =====================================
    # ADD EXPLICIT MEMORY
    # =====================================

    def add_explicit_memory(
        self,
        text,
        subject=None
    ):

        if not text:

            return

        self.memory[
            "explicit_memories"
        ].append({

            "text":
                text,

            "subject":
                subject,

            "confidence":
                1.0,

            "timestamp":
                datetime.now()
                .isoformat()
        })

        self.save()


    # =====================================
    # PREFERENCES
    # =====================================

    def set_preference(
        self,
        key,
        value
    ):

        if not key:

            return

        self.memory[
            "preferences"
        ][key] = {

            "value":
                value,

            "updated_at":
                datetime.now()
                .isoformat()
        }

        self.save()


    # =====================================
    # GET
    # =====================================

    def get(self):

        return deepcopy(self.memory)