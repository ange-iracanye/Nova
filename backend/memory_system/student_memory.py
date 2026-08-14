import json
import hashlib
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

            except Exception:

                self.memory = self.default()

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
    # SAVE
    # =====================================

    def save(self):

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
                self.memory,
                indent=4,
                ensure_ascii=False
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
                    confidence,

                "attempts":
                    1,

                "first_seen":
                    now,

                "last_seen":
                    now
            }

        else:

            concepts[concept][
                "confidence"
            ] = confidence

            concepts[concept][
                "attempts"
            ] += 1

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

        return self.memory