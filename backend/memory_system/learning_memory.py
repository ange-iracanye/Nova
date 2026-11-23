import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from datetime import datetime

from backend.user_context import get_active_user


class LearningMemory:

    def __init__(self):

        base_path = Path("data/memory")
        email = get_active_user()
        if email:
            user_id = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
            self.file = base_path / "learning" / f"{user_id}.json"
        else:
            # Preserve the legacy anonymous store without ever migrating it
            # into a signed-in student's private file.
            self.file = base_path / "learning_memory.json"

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        if self.file.exists():

            try:

                self.data = json.loads(
                    self.file.read_text(
                        encoding="utf-8"
                    )
                )

            except (OSError, ValueError, TypeError, UnicodeError):

                self.data = self.default()

            self.data = self._normalize_data(self.data)

        else:

            self.data = self.default()

            self.save()


    # =====================================
    # DEFAULT
    # =====================================

    def default(self):

        return {

            "subjects": {},

            "concepts": {},

            "mistakes": [],

            "successful_strategies": [],

            "failed_strategies": []
        }


    @staticmethod
    def _safe_count(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError, OverflowError):
            return 0

    @staticmethod
    def _safe_confidence(value):
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return 50.0
        if not math.isfinite(number):
            return 50.0
        return max(0.0, min(100.0, number))

    @staticmethod
    def _json_safe(value):
        if isinstance(value, dict):
            return {str(key): LearningMemory._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [LearningMemory._json_safe(item) for item in value]
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return None

    def _normalize_data(self, value):
        result = self.default()
        if not isinstance(value, dict):
            return result

        subjects = value.get("subjects")
        if isinstance(subjects, dict):
            for subject, record in subjects.items():
                if isinstance(record, dict):
                    result["subjects"][str(subject)] = {
                        "confidence": self._safe_confidence(record.get("confidence", 50)),
                        "attempts": self._safe_count(record.get("attempts")),
                        "correct": self._safe_count(record.get("correct")),
                        "incorrect": self._safe_count(record.get("incorrect")),
                        "last_studied": record.get("last_studied") if isinstance(record.get("last_studied"), str) else None,
                        "study_count": self._safe_count(record.get("study_count")),
                    }

        concepts = value.get("concepts")
        if isinstance(concepts, dict):
            for key, record in concepts.items():
                if not isinstance(record, dict):
                    continue
                result["concepts"][str(key)] = {
                    "subject": record.get("subject") if isinstance(record.get("subject"), str) else "",
                    "concept": record.get("concept") if isinstance(record.get("concept"), str) else "",
                    "confidence": self._safe_confidence(record.get("confidence", 50)),
                    "attempts": self._safe_count(record.get("attempts")),
                    "difficulty": record.get("difficulty") if isinstance(record.get("difficulty"), str) else None,
                    "first_seen": record.get("first_seen") if isinstance(record.get("first_seen"), str) else None,
                    "last_seen": record.get("last_seen") if isinstance(record.get("last_seen"), str) else None,
                }

        for key in ("mistakes", "successful_strategies", "failed_strategies"):
            items = value.get(key)
            result[key] = [self._json_safe(item) for item in items if isinstance(item, dict)][-500:] if isinstance(items, list) else []

        return result

    # =====================================
    # SAVE
    # =====================================

    def save(self):
        self.data = self._normalize_data(self.data)
        temporary = self.file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                self._json_safe(self.data),
                indent=4,
                ensure_ascii=False,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.file)


    # =====================================
    # SUBJECT
    # =====================================

    def ensure_subject(
        self,
        subject
    ):

        if not subject:
            return


        if not isinstance(self.data.get("subjects"), dict):
            self.data["subjects"] = {}

        if subject not in self.data["subjects"] or not isinstance(self.data["subjects"].get(subject), dict):

            self.data[
                "subjects"
            ][subject] = {

                "confidence": 50,

                "attempts": 0,

                "correct": 0,

                "incorrect": 0,

                "last_studied": None,

                "study_count": 0
            }


    # =====================================
    # RECORD ATTEMPT
    # =====================================

    def record_attempt(
        self,
        subject,
        confidence,
        correct=None
    ):

        if not subject:
            return


        self.ensure_subject(
            subject
        )


        data = self.data[
            "subjects"
        ][subject]


        data["attempts"] = self._safe_count(data.get("attempts")) + 1


        data["confidence"] = self._safe_confidence(confidence)


        data[
            "last_studied"
        ] = (
            datetime.now()
            .isoformat()
        )


        data["study_count"] = self._safe_count(data.get("study_count")) + 1


        if correct is True:

            data["correct"] = self._safe_count(data.get("correct")) + 1


        elif correct is False:

            data["incorrect"] = self._safe_count(data.get("incorrect")) + 1


        self.save()


    # =====================================
    # CONCEPT
    # =====================================

    def update_concept(
        self,
        subject,
        concept,
        confidence,
        difficulty=None
    ):

        if not subject or not concept:
            return


        key = (
            f"{subject}::{concept}"
        )


        if not isinstance(self.data.get("concepts"), dict):
            self.data["concepts"] = {}

        if key not in self.data["concepts"] or not isinstance(self.data["concepts"].get(key), dict):

            self.data[
                "concepts"
            ][key] = {

                "subject":
                    subject,

                "concept":
                    concept,

                "confidence":
                    self._safe_confidence(confidence),

                "attempts":
                    1,

                "difficulty":
                    difficulty,

                "first_seen":
                    datetime.now()
                    .isoformat(),

                "last_seen":
                    datetime.now()
                    .isoformat()
            }

        else:

            data = self.data[
                "concepts"
            ][key]


            data["confidence"] = self._safe_confidence(confidence)


            data["attempts"] = self._safe_count(data.get("attempts")) + 1


            data[
                "last_seen"
            ] = (
                datetime.now()
                .isoformat()
            )


            if difficulty:

                data[
                    "difficulty"
                ] = difficulty


        self.save()


    # =====================================
    # MISTAKE
    # =====================================

    def record_mistake(
        self,
        subject,
        concept,
        description
    ):

        self.data[
            "mistakes"
        ].append({

            "subject":
                subject,

            "concept":
                concept,

            "description":
                description,

            "timestamp":
                datetime.now()
                .isoformat()
        })


        # Keep the full history reasonably sized.

        if len(
            self.data["mistakes"]
        ) > 500:

            self.data[
                "mistakes"
            ] = self.data[
                "mistakes"
            ][-500:]


        self.save()


    # =====================================
    # TEACHING STRATEGY
    # =====================================

    def record_strategy(
        self,
        strategy,
        successful=True,
        subject=None
    ):

        target = (

            "successful_strategies"

            if successful

            else

            "failed_strategies"
        )


        self.data[
            target
        ].append({

            "strategy":
                strategy,

            "subject":
                subject,

            "timestamp":
                datetime.now()
                .isoformat()
        })


        self.save()


    # =====================================
    # GET SUBJECT
    # =====================================

    def get_subject(
        self,
        subject
    ):

        return self.data[
            "subjects"
        ].get(
            subject
        )


    # =====================================
    # GET CONCEPT
    # =====================================

    def get_concept(
        self,
        subject,
        concept
    ):

        key = (
            f"{subject}::{concept}"
        )


        return self.data[
            "concepts"
        ].get(
            key
        )


    # =====================================
    # GET ALL
    # =====================================

    def get(self):

        return deepcopy(self.data)