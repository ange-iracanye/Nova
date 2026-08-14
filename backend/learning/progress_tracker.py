import json
import hashlib
from pathlib import Path
from datetime import datetime


class ProgressTracker:

    def __init__(self, user_email=None):

        self.base_path = Path(
            "data/memory/progress"
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

                self.progress = json.loads(
                    self.file.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception:

                self.progress = {}

        else:

            self.progress = {}

            self._save()


    # =====================================
    # FILE
    # =====================================

    def _get_file(self):

        if not self.user_email:

            return (
                self.base_path
                / "default.json"
            )

        user_id = hashlib.sha256(
            self.user_email.encode("utf-8")
        ).hexdigest()

        return (
            self.base_path
            / f"{user_id}.json"
        )


    # =====================================
    # SAVE
    # =====================================

    def _save(self):

        temporary = self.file.with_suffix(
            ".tmp"
        )

        temporary.write_text(

            json.dumps(
                self.progress,
                indent=4,
                ensure_ascii=False
            ),

            encoding="utf-8"
        )

        temporary.replace(
            self.file
        )


    # =====================================
    # UPDATE
    # =====================================

    def update(
        self,
        subject,
        topic,
        confidence
    ):

        if not subject or not topic:

            return

        if subject not in self.progress:

            self.progress[subject] = {}


        if topic not in self.progress[
            subject
        ]:

            self.progress[
                subject
            ][
                topic
            ] = {

                "attempts":
                    0,

                "confidence":
                    50,

                "mastered":
                    False,

                "first_seen":
                    datetime.now()
                    .isoformat(),

                "last_seen":
                    None
            }


        data = self.progress[
            subject
        ][
            topic
        ]


        data[
            "attempts"
        ] += 1


        data[
            "confidence"
        ] = confidence


        data[
            "mastered"
        ] = (
            confidence >= 90
        )


        data[
            "last_seen"
        ] = (
            datetime.now()
            .isoformat()
        )


        self._save()


    # =====================================
    # GET
    # =====================================

    def get(self):

        return self.progress