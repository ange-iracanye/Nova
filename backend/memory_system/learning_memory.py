import json
from pathlib import Path
from datetime import datetime


class LearningMemory:

    def __init__(self):

        self.file = Path(
            "data/memory/learning_memory.json"
        )

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

            except Exception:

                self.data = self.default()

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


    # =====================================
    # SAVE
    # =====================================

    def save(self):

        self.file.write_text(

            json.dumps(
                self.data,
                indent=4,
                ensure_ascii=False
            ),

            encoding="utf-8"
        )


    # =====================================
    # SUBJECT
    # =====================================

    def ensure_subject(
        self,
        subject
    ):

        if not subject:
            return


        if subject not in self.data[
            "subjects"
        ]:

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


        data[
            "attempts"
        ] += 1


        data[
            "confidence"
        ] = max(
            0,
            min(
                100,
                confidence
            )
        )


        data[
            "last_studied"
        ] = (
            datetime.now()
            .isoformat()
        )


        data[
            "study_count"
        ] += 1


        if correct is True:

            data[
                "correct"
            ] += 1


        elif correct is False:

            data[
                "incorrect"
            ] += 1


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


        if key not in self.data[
            "concepts"
        ]:

            self.data[
                "concepts"
            ][key] = {

                "subject":
                    subject,

                "concept":
                    concept,

                "confidence":
                    confidence,

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


            data[
                "confidence"
            ] = confidence


            data[
                "attempts"
            ] += 1


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

        return self.data