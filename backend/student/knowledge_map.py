import json
import hashlib
from pathlib import Path
from datetime import datetime


class KnowledgeMap:
    """
    Persistent per-user knowledge map.

    The knowledge map stores Nova's understanding of the student's
    progress across subjects and topics.

    Structure:

        {
            "physics": {
                "newtons second law": {
                    "topic": "newtons second law",
                    "confidence": 72,
                    "attempts": 4,
                    "first_seen": "...",
                    "last_seen": "...",
                    "confidence_history": [
                        50,
                        60,
                        65,
                        72
                    ]
                }
            }
        }

    Confidence is stored from 0 to 100.

    Topic categories:

        0 - 29
            weak

        30 - 59
            developing

        60 - 79
            strong

        80 - 100
            mastery

    The class keeps the existing public methods:

        update()
        get_topic()
        get()

    Additional helper methods are provided for the adaptive
    learning system.
    """

    # =====================================
    # PATH
    # =====================================

    DEFAULT_BASE_PATH = (
        "data/memory/knowledge_maps"
    )

    # =====================================
    # CONFIDENCE LIMITS
    # =====================================

    MIN_CONFIDENCE = 0

    MAX_CONFIDENCE = 100

    # =====================================
    # HISTORY LIMIT
    # =====================================

    MAX_CONFIDENCE_HISTORY = 20

    # =====================================
    # CATEGORY THRESHOLDS
    # =====================================

    WEAK_THRESHOLD = 30

    DEVELOPING_THRESHOLD = 60

    STRONG_THRESHOLD = 80

    def __init__(
        self,
        user_email=None
    ):

        self.base_path = Path(
            self.DEFAULT_BASE_PATH
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

        self.map = {}

        self._load()

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
            self.user_email.encode(
                "utf-8"
            )
        ).hexdigest()

        return (
            self.base_path
            / f"{user_id}.json"
        )

    # =====================================
    # LOAD
    # =====================================

    def _load(self):

        if not self.file.exists():

            self.map = {}

            self._save()

            return

        try:

            raw = self.file.read_text(
                encoding="utf-8"
            )

            loaded = json.loads(
                raw
            )

            if isinstance(
                loaded,
                dict
            ):

                self.map = loaded

            else:

                self.map = {}

        except (
            json.JSONDecodeError,
            OSError,
            TypeError
        ):

            self.map = {}

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
    # NORMALIZE TEXT
    # =====================================

    def _normalize_text(
        self,
        value
    ):

        if not isinstance(
            value,
            str
        ):

            return ""

        return " ".join(
            value.strip().lower().split()
        )

    # =====================================
    # NORMALIZE CONFIDENCE
    # =====================================

    def _normalize_confidence(
        self,
        confidence
    ):

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 50.0

        confidence = max(
            self.MIN_CONFIDENCE,
            min(
                self.MAX_CONFIDENCE,
                confidence
            )
        )

        # Store whole numbers when possible.
        if confidence.is_integer():

            return int(
                confidence
            )

        return confidence

    # =====================================
    # CATEGORY
    # =====================================

    def _get_category(
        self,
        confidence
    ):

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        if confidence < self.WEAK_THRESHOLD:

            return "weak"

        if confidence < self.DEVELOPING_THRESHOLD:

            return "developing"

        if confidence < self.STRONG_THRESHOLD:

            return "strong"

        return "mastery"

    # =====================================
    # UPDATE
    # =====================================

    def update(
        self,
        subject,
        topic,
        confidence
    ):

        subject = self._normalize_text(
            subject
        )

        topic = self._normalize_text(
            topic
        )

        if not subject or not topic:

            return

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        now = datetime.now().isoformat()

        if subject not in self.map:

            self.map[subject] = {}

        existing = self.map[
            subject
        ].get(
            topic,
            {}
        )

        # =====================================
        # EXISTING VALUES
        # =====================================

        attempts = existing.get(
            "attempts",
            0
        )

        try:

            attempts = int(
                attempts
            )

        except (
            TypeError,
            ValueError
        ):

            attempts = 0

        attempts += 1

        first_seen = existing.get(
            "first_seen"
        )

        if not first_seen:

            first_seen = now

        # =====================================
        # CONFIDENCE HISTORY
        # =====================================

        confidence_history = (
            existing.get(
                "confidence_history",
                []
            )
        )

        if not isinstance(
            confidence_history,
            list
        ):

            confidence_history = []

        confidence_history.append(
            confidence
        )

        if len(
            confidence_history
        ) > self.MAX_CONFIDENCE_HISTORY:

            confidence_history = (
                confidence_history[
                    -self.MAX_CONFIDENCE_HISTORY:
                ]
            )

        # =====================================
        # UPDATE TOPIC
        # =====================================

        self.map[
            subject
        ][
            topic
        ] = {

            "topic":
                topic,

            "confidence":
                confidence,

            "category":
                self._get_category(
                    confidence
                ),

            "attempts":
                attempts,

            "first_seen":
                first_seen,

            "last_seen":
                now,

            "confidence_history":
                confidence_history
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

        subject = self._normalize_text(
            subject
        )

        topic = self._normalize_text(
            topic
        )

        if not subject or not topic:

            return None

        return (

            self.map
            .get(
                subject,
                {}
            )
            .get(
                topic
            )

        )

    # =====================================
    # GET SUBJECT
    # =====================================

    def get_subject(
        self,
        subject
    ):

        subject = self._normalize_text(
            subject
        )

        if not subject:

            return {}

        return dict(
            self.map.get(
                subject,
                {}
            )
        )

    # =====================================
    # GET SUBJECT CONFIDENCE
    # =====================================

    def get_subject_confidence(
        self,
        subject
    ):

        topics = self.get_subject(
            subject
        )

        if not topics:

            return 50

        confidences = []

        for data in topics.values():

            if not isinstance(
                data,
                dict
            ):

                continue

            confidence = data.get(
                "confidence"
            )

            if confidence is None:

                continue

            try:

                confidence = float(
                    confidence
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            confidences.append(
                confidence
            )

        if not confidences:

            return 50

        average = (
            sum(confidences)
            / len(confidences)
        )

        return round(
            average,
            2
        )

    # =====================================
    # GET CATEGORY
    # =====================================

    def get_category(
        self,
        subject,
        topic
    ):

        data = self.get_topic(
            subject,
            topic
        )

        if not data:

            return "unknown"

        category = data.get(
            "category"
        )

        if category:

            return category

        return self._get_category(
            data.get(
                "confidence",
                50
            )
        )

    # =====================================
    # GET WEAK TOPICS
    # =====================================

    def get_weak_topics(
        self,
        subject=None
    ):

        topics = []

        if subject:

            subjects = {

                self._normalize_text(
                    subject
                ):
                    self.get_subject(
                        subject
                    )
            }

        else:

            subjects = self.map

        for current_subject, data in (
            subjects.items()
        ):

            if not isinstance(
                data,
                dict
            ):

                continue

            for topic, topic_data in (
                data.items()
            ):

                if not isinstance(
                    topic_data,
                    dict
                ):

                    continue

                confidence = (
                    topic_data.get(
                        "confidence",
                        50
                    )
                )

                try:

                    confidence = float(
                        confidence
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if confidence < (
                    self.DEVELOPING_THRESHOLD
                ):

                    topics.append({

                        "subject":
                            current_subject,

                        "topic":
                            topic,

                        "confidence":
                            confidence,

                        "category":
                            self._get_category(
                                confidence
                            ),

                        "attempts":
                            topic_data.get(
                                "attempts",
                                0
                            )
                    })

        topics.sort(
            key=lambda item:
                item["confidence"]
        )

        return topics

    # =====================================
    # GET STRONG TOPICS
    # =====================================

    def get_strong_topics(
        self,
        subject=None
    ):

        topics = []

        if subject:

            subjects = {

                self._normalize_text(
                    subject
                ):
                    self.get_subject(
                        subject
                    )
            }

        else:

            subjects = self.map

        for current_subject, data in (
            subjects.items()
        ):

            if not isinstance(
                data,
                dict
            ):

                continue

            for topic, topic_data in (
                data.items()
            ):

                if not isinstance(
                    topic_data,
                    dict
                ):

                    continue

                confidence = (
                    topic_data.get(
                        "confidence",
                        50
                    )
                )

                try:

                    confidence = float(
                        confidence
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if confidence >= (
                    self.STRONG_THRESHOLD
                ):

                    topics.append({

                        "subject":
                            current_subject,

                        "topic":
                            topic,

                        "confidence":
                            confidence,

                        "category":
                            self._get_category(
                                confidence
                            ),

                        "attempts":
                            topic_data.get(
                                "attempts",
                                0
                            )
                    })

        topics.sort(
            key=lambda item:
                item["confidence"],
            reverse=True
        )

        return topics

    # =====================================
    # GET TOPICS BY CATEGORY
    # =====================================

    def get_topics_by_category(
        self,
        category,
        subject=None
    ):

        valid_categories = {

            "weak",
            "developing",
            "strong",
            "mastery"
        }

        if category not in valid_categories:

            return []

        results = []

        if subject:

            subjects = {

                self._normalize_text(
                    subject
                ):
                    self.get_subject(
                        subject
                    )
            }

        else:

            subjects = self.map

        for current_subject, data in (
            subjects.items()
        ):

            if not isinstance(
                data,
                dict
            ):

                continue

            for topic, topic_data in (
                data.items()
            ):

                if not isinstance(
                    topic_data,
                    dict
                ):

                    continue

                topic_category = (
                    topic_data.get(
                        "category"
                    )
                )

                if not topic_category:

                    topic_category = (
                        self._get_category(
                            topic_data.get(
                                "confidence",
                                50
                            )
                        )
                    )

                if topic_category != category:

                    continue

                results.append({

                    "subject":
                        current_subject,

                    "topic":
                        topic,

                    "confidence":
                        topic_data.get(
                            "confidence",
                            50
                        ),

                    "category":
                        topic_category,

                    "attempts":
                        topic_data.get(
                            "attempts",
                            0
                        ),

                    "first_seen":
                        topic_data.get(
                            "first_seen"
                        ),

                    "last_seen":
                        topic_data.get(
                            "last_seen"
                        )
                })

        results.sort(
            key=lambda item:
                item.get(
                    "confidence",
                    0
                ),
            reverse=(
                category
                in {
                    "strong",
                    "mastery"
                }
            )
        )

        return results

    # =====================================
    # GET ALL
    # =====================================

    def get(self):

        return self.map

    # =====================================
    # GET SUMMARY
    # =====================================

    def get_summary(
        self,
        subject=None
    ):

        if subject:

            subjects = {

                self._normalize_text(
                    subject
                ):
                    self.get_subject(
                        subject
                    )
            }

        else:

            subjects = self.map

        total_topics = 0
        total_attempts = 0

        weak = 0
        developing = 0
        strong = 0
        mastery = 0

        for data in subjects.values():

            if not isinstance(
                data,
                dict
            ):

                continue

            for topic_data in data.values():

                if not isinstance(
                    topic_data,
                    dict
                ):

                    continue

                total_topics += 1

                attempts = topic_data.get(
                    "attempts",
                    0
                )

                try:

                    total_attempts += int(
                        attempts
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    pass

                confidence = (
                    topic_data.get(
                        "confidence",
                        50
                    )
                )

                category = (
                    topic_data.get(
                        "category"
                    )
                )

                if not category:

                    category = (
                        self._get_category(
                            confidence
                        )
                    )

                if category == "weak":

                    weak += 1

                elif category == "developing":

                    developing += 1

                elif category == "strong":

                    strong += 1

                elif category == "mastery":

                    mastery += 1

        return {

            "total_topics":
                total_topics,

            "total_attempts":
                total_attempts,

            "weak":
                weak,

            "developing":
                developing,

            "strong":
                strong,

            "mastery":
                mastery
        }

    # =====================================
    # RESET TOPIC
    # =====================================

    def remove_topic(
        self,
        subject,
        topic
    ):

        subject = self._normalize_text(
            subject
        )

        topic = self._normalize_text(
            topic
        )

        if not subject or not topic:

            return False

        if subject not in self.map:

            return False

        if topic not in self.map[
            subject
        ]:

            return False

        del self.map[
            subject
        ][
            topic
        ]

        if not self.map[
            subject
        ]:

            del self.map[
                subject
            ]

        self._save()

        return True

    # =====================================
    # RESET SUBJECT
    # =====================================

    def remove_subject(
        self,
        subject
    ):

        subject = self._normalize_text(
            subject
        )

        if not subject:

            return False

        if subject not in self.map:

            return False

        del self.map[
            subject
        ]

        self._save()

        return True

    # =====================================
    # CLEAR MAP
    # =====================================

    def clear(self):

        self.map = {}

        self._save()
