import json
import hashlib
from pathlib import Path
from datetime import datetime


class KnowledgeMap:

    def __init__(self, user_email=None):

        self.base_path = Path(
            "data/memory/knowledge_maps"
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

                self.map = json.loads(
                    self.file.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception:

                self.map = {}

        else:

            self.map = {}

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
                self.map,
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

        if subject not in self.map:

            self.map[subject] = {}


        existing = self.map[
            subject
        ].get(
            topic,
            {}
        )


        self.map[
            subject
        ][
            topic
        ] = {

            "confidence":
                confidence,

            "attempts":
                existing.get(
                    "attempts",
                    0
                ) + 1,

            "first_seen":
                existing.get(
                    "first_seen",
                    datetime.now()
                    .isoformat()
                ),

            "last_seen":
                datetime.now()
                .isoformat()
        }


        self._save()


    # =====================================
    # GET TOPIC
    # =====================================

    def get_topic(
        self,
        subject,
        topic
    ):

        return (

            self.map
            .get(subject, {})
            .get(topic)

        )


    # =====================================
    # GET ALL
    # =====================================

    def get(self):

        return self.map