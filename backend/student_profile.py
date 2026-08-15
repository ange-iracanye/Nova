import json
import os
import shutil
import tempfile

from copy import deepcopy
from datetime import datetime
from pathlib import Path


class StudentProfile:
    """
    Central manager for Nova's student profile.

    Responsibilities
    ----------------
    - Store persistent student information.
    - Load the profile safely from disk.
    - Repair incomplete or corrupted profiles.
    - Save changes atomically.
    - Track questions and topics.
    - Track subjects.
    - Track learning progress.
    - Track strengths and weaknesses.
    - Track confidence.
    - Track attempts.
    - Track mistakes.
    - Track successful interactions.
    - Store preferences.
    - Provide statistics.
    - Provide safe snapshots for Nova's other systems.

    This class is intentionally independent from the LLM.

    It does NOT:
    - generate answers
    - detect subjects
    - generate quizzes
    - decide difficulty
    - build prompts
    - communicate with Ollama

    Those responsibilities belong to other Nova systems.

    StudentProfile is the persistent student-state layer.
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    DEFAULT_FILE = Path(
        "data/student_profile.json"
    )

    BACKUP_FILE = Path(
        "data/student_profile.backup.json"
    )

    CURRENT_VERSION = 2

    DEFAULT_LEVEL = "beginner"

    VALID_LEVELS = {
        "beginner",
        "intermediate",
        "advanced",
        "expert"
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        file_path=None,
        name="Student",
        level="beginner",
        auto_save=True
    ):
        """
        Create or load a student profile.

        Parameters
        ----------
        file_path:
            Optional custom profile location.

        name:
            Default student name when creating a new profile.

        level:
            Default academic level.

        auto_save:
            Automatically save modifications.
        """

        self.file = Path(
            file_path
            if file_path
            else self.DEFAULT_FILE
        )

        self.auto_save = bool(
            auto_save
        )

        self.profile = {}

        self._ensure_directory()

        loaded = self._load()

        if not loaded:

            self.profile = (
                self._create_default_profile(
                    name=name,
                    level=level
                )
            )

            self._save()

        else:

            changed = (
                self._normalize_profile()
            )

            if changed:

                self._save()

    # ============================================================
    # DEFAULT PROFILE
    # ============================================================

    def _create_default_profile(
        self,
        name="Student",
        level="beginner"
    ):
        """
        Create a complete default profile.

        The original Nova profile only stored a handful
        of values. This version creates a richer structure
        that can grow with the student.
        """

        normalized_level = (
            self._normalize_level(
                level
            )
        )

        normalized_name = (
            self._normalize_string(
                name,
                "Student"
            )
        )

        now = self._now()

        return {

            # ----------------------------------------------------
            # VERSION
            # ----------------------------------------------------

            "profile_version":
                self.CURRENT_VERSION,

            # ----------------------------------------------------
            # BASIC IDENTITY
            # ----------------------------------------------------

            "name":
                normalized_name,

            "level":
                normalized_level,

            # ----------------------------------------------------
            # LEARNING SUMMARY
            # ----------------------------------------------------

            "strengths": [],

            "weaknesses": [],

            "topics_seen": [],

            "subjects_seen": [],

            # ----------------------------------------------------
            # ACTIVITY
            # ----------------------------------------------------

            "questions_asked": 0,

            "questions_answered": 0,

            "successful_answers": 0,

            "incorrect_answers": 0,

            "sessions_count": 0,

            # ----------------------------------------------------
            # LEARNING PROGRESS
            # ----------------------------------------------------

            "topics": {},

            "subjects": {},

            # ----------------------------------------------------
            # CONFIDENCE
            # ----------------------------------------------------

            "confidence": {},

            # ----------------------------------------------------
            # MISTAKES
            # ----------------------------------------------------

            "mistakes": {},

            # ----------------------------------------------------
            # PREFERENCES
            # ----------------------------------------------------

            "preferences": {

                "language":
                    "English",

                "teaching_style":
                    "adaptive",

                "difficulty":
                    "adaptive",

                "response_length":
                    "balanced",

                "tone":
                    "friendly",

                "hints":
                    "when_needed",

                "step_by_step":
                    True,

                "use_examples":
                    True,

                "use_analogies":
                    True,

                "encouragement":
                    True

            },

            # ----------------------------------------------------
            # METADATA
            # ----------------------------------------------------

            "created_at":
                now,

            "updated_at":
                now,

            "last_active":
                None,

            "last_subject":
                None,

            "last_topic":
                None
        }

    # ============================================================
    # FILE MANAGEMENT
    # ============================================================

    def _ensure_directory(self):
        """
        Make sure the profile directory exists.
        """

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    # ============================================================
    # LOAD
    # ============================================================

    def _load(self):
        """
        Load the profile from disk.

        Returns
        -------
        bool
            True if loading succeeded.
        """

        if not self.file.exists():

            return False

        try:

            with self.file.open(
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(
                    f
                )

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
            ValueError
        ):

            return self._recover_from_backup()

        if not isinstance(
            data,
            dict
        ):

            return self._recover_from_backup()

        self.profile = data

        return True

    # ============================================================
    # BACKUP RECOVERY
    # ============================================================

    def _recover_from_backup(self):
        """
        Try to recover the profile from the backup file.

        This protects Nova from losing the entire student
        profile because of a malformed JSON file.
        """

        if not self.BACKUP_FILE.exists():

            return False

        try:

            with self.BACKUP_FILE.open(
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(
                    f
                )

        except Exception:

            return False

        if not isinstance(
            data,
            dict
        ):

            return False

        self.profile = data

        return True

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def _normalize_profile(self):
        """
        Repair missing or malformed profile fields.

        Returns
        -------
        bool
            True if the profile was modified.
        """

        changed = False

        if not isinstance(
            self.profile,
            dict
        ):

            self.profile = (
                self._create_default_profile()
            )

            return True

        # --------------------------------------------------------
        # VERSION
        # --------------------------------------------------------

        if self.profile.get(
            "profile_version"
        ) != self.CURRENT_VERSION:

            self.profile[
                "profile_version"
            ] = self.CURRENT_VERSION

            changed = True

        # --------------------------------------------------------
        # BASIC FIELDS
        # --------------------------------------------------------

        if not isinstance(
            self.profile.get("name"),
            str
        ):

            self.profile["name"] = "Student"

            changed = True

        if not self.profile.get(
            "name"
        ):

            self.profile["name"] = "Student"

            changed = True

        normalized_level = (
            self._normalize_level(
                self.profile.get(
                    "level"
                )
            )
        )

        if self.profile.get(
            "level"
        ) != normalized_level:

            self.profile["level"] = (
                normalized_level
            )

            changed = True

        # --------------------------------------------------------
        # LIST FIELDS
        # --------------------------------------------------------

        list_fields = [

            "strengths",
            "weaknesses",
            "topics_seen",
            "subjects_seen"

        ]

        for field in list_fields:

            value = self.profile.get(
                field
            )

            if not isinstance(
                value,
                list
            ):

                self.profile[field] = []

                changed = True

        # --------------------------------------------------------
        # INTEGER FIELDS
        # --------------------------------------------------------

        integer_fields = [

            "questions_asked",
            "questions_answered",
            "successful_answers",
            "incorrect_answers",
            "sessions_count"

        ]

        for field in integer_fields:

            value = self.profile.get(
                field
            )

            if not isinstance(
                value,
                int
            ) or value < 0:

                self.profile[field] = 0

                changed = True

        # --------------------------------------------------------
        # DICTIONARY FIELDS
        # --------------------------------------------------------

        dictionary_fields = [

            "topics",
            "subjects",
            "confidence",
            "mistakes"

        ]

        for field in dictionary_fields:

            value = self.profile.get(
                field
            )

            if not isinstance(
                value,
                dict
            ):

                self.profile[field] = {}

                changed = True

        # --------------------------------------------------------
        # PREFERENCES
        # --------------------------------------------------------

        if not isinstance(
            self.profile.get(
                "preferences"
            ),
            dict
        ):

            self.profile[
                "preferences"
            ] = {}

            changed = True

        preference_defaults = {

            "language":
                "English",

            "teaching_style":
                "adaptive",

            "difficulty":
                "adaptive",

            "response_length":
                "balanced",

            "tone":
                "friendly",

            "hints":
                "when_needed",

            "step_by_step":
                True,

            "use_examples":
                True,

            "use_analogies":
                True,

            "encouragement":
                True

        }

        for key, value in (
            preference_defaults.items()
        ):

            if key not in self.profile[
                "preferences"
            ]:

                self.profile[
                    "preferences"
                ][key] = value

                changed = True

        # --------------------------------------------------------
        # METADATA
        # --------------------------------------------------------

        now = self._now()

        if not self.profile.get(
            "created_at"
        ):

            self.profile[
                "created_at"
            ] = now

            changed = True

        if not self.profile.get(
            "updated_at"
        ):

            self.profile[
                "updated_at"
            ] = now

            changed = True

        if "last_active" not in self.profile:

            self.profile[
                "last_active"
            ] = None

            changed = True

        if "last_subject" not in self.profile:

            self.profile[
                "last_subject"
            ] = None

            changed = True

        if "last_topic" not in self.profile:

            self.profile[
                "last_topic"
            ] = None

            changed = True

        return changed

    # ============================================================
    # SAVE
    # ============================================================

    def save(self):
        """
        Public save method.

        Uses an atomic temporary-file replacement so Nova
        does not normally leave behind half-written JSON.
        """

        return self._save()

    # ============================================================
    # INTERNAL SAVE
    # ============================================================

    def _save(self):
        """
        Save profile safely.

        A backup is created before replacing the current
        profile.
        """

        self._ensure_directory()

        self.profile[
            "updated_at"
        ] = self._now()

        try:

            # ----------------------------------------------------
            # BACKUP CURRENT FILE
            # ----------------------------------------------------

            if self.file.exists():

                try:

                    shutil.copy2(
                        self.file,
                        self.BACKUP_FILE
                    )

                except OSError:

                    pass

            # ----------------------------------------------------
            # TEMPORARY FILE
            # ----------------------------------------------------

            fd, temporary_path = (
                tempfile.mkstemp(
                    prefix="student_profile_",
                    suffix=".tmp",
                    dir=str(
                        self.file.parent
                    )
                )
            )

            try:

                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        self.profile,
                        f,
                        indent=4,
                        ensure_ascii=False
                    )

                    f.write(
                        "\n"
                    )

                    f.flush()

                    os.fsync(
                        f.fileno()
                    )

                os.replace(
                    temporary_path,
                    self.file
                )

            except Exception:

                try:

                    os.remove(
                        temporary_path
                    )

                except OSError:

                    pass

                raise

            return True

        except Exception as error:

            print(
                "[StudentProfile] Save error:",
                error
            )

            return False

    # ============================================================
    # AUTO SAVE
    # ============================================================

    def _commit(self):
        """
        Save automatically when auto_save is enabled.
        """

        if self.auto_save:

            return self._save()

        return True

    # ============================================================
    # GET PROFILE
    # ============================================================

    def get(self):
        """
        Return a copy of the current profile.

        Returning a deep copy prevents another Nova system
        from accidentally modifying the profile without
        going through StudentProfile.
        """

        return deepcopy(
            self.profile
        )

    # ============================================================
    # GET RAW PROFILE
    # ============================================================

    def get_raw(self):
        """
        Internal-style accessor.

        Unlike get(), this returns the actual dictionary.

        Use carefully.
        """

        return self.profile

    # ============================================================
    # UPDATE PROFILE
    # ============================================================

    def update(
        self,
        updates
    ):
        """
        Update multiple profile fields.

        Only dictionary updates are accepted.
        """

        if not isinstance(
            updates,
            dict
        ):

            return False

        self.profile.update(
            deepcopy(
                updates
            )
        )

        self._normalize_profile()

        return self._commit()

    # ============================================================
    # SET FIELD
    # ============================================================

    def set(
        self,
        key,
        value
    ):
        """
        Set one profile field.
        """

        if not key:

            return False

        self.profile[
            str(key)
        ] = deepcopy(
            value
        )

        self._normalize_profile()

        return self._commit()

    # ============================================================
    # GET FIELD
    # ============================================================

    def get_field(
        self,
        key,
        default=None
    ):
        """
        Safely retrieve one field.
        """

        if not key:

            return default

        return deepcopy(
            self.profile.get(
                key,
                default
            )
        )

    # ============================================================
    # NAME
    # ============================================================

    def set_name(
        self,
        name
    ):
        """
        Change the student's name.
        """

        name = self._normalize_string(
            name,
            "Student"
        )

        self.profile[
            "name"
        ] = name

        return self._commit()

    def get_name(self):

        return self.profile.get(
            "name",
            "Student"
        )

    # ============================================================
    # LEVEL
    # ============================================================

    def set_level(
        self,
        level
    ):
        """
        Change the student's general academic level.
        """

        normalized = (
            self._normalize_level(
                level
            )
        )

        self.profile[
            "level"
        ] = normalized

        return self._commit()

    def get_level(self):

        return self.profile.get(
            "level",
            self.DEFAULT_LEVEL
        )

    # ============================================================
    # QUESTIONS
    # ============================================================

    def add_question(
        self,
        topic=None,
        subject=None
    ):
        """
        Register a new student question.

        This keeps compatibility with the original API while
        also updating topic and subject statistics.
        """

        self.profile[
            "questions_asked"
        ] += 1

        self.profile[
            "last_active"
        ] = self._now()

        if subject:

            subject = (
                self._normalize_string(
                    subject
                )
            )

            self._add_unique(
                "subjects_seen",
                subject
            )

            self._register_subject_activity(
                subject
            )

            self.profile[
                "last_subject"
            ] = subject

        if topic:

            topic = (
                self._normalize_string(
                    topic
                )
            )

            self._add_unique(
                "topics_seen",
                topic
            )

            self._register_topic_activity(
                topic
            )

            self.profile[
                "last_topic"
            ] = topic

        return self._commit()

    # ============================================================
    # ANSWER TRACKING
    # ============================================================

    def record_answer(
        self,
        correct,
        topic=None,
        subject=None,
        confidence=None
    ):
        """
        Record the result of a learning interaction.

        Parameters
        ----------
        correct:
            Whether the student's answer was correct.

        topic:
            Optional learning topic.

        subject:
            Optional academic subject.

        confidence:
            Optional confidence score from 0 to 100.
        """

        correct = bool(
            correct
        )

        self.profile[
            "questions_answered"
        ] += 1

        self.profile[
            "last_active"
        ] = self._now()

        if correct:

            self.profile[
                "successful_answers"
            ] += 1

        else:

            self.profile[
                "incorrect_answers"
            ] += 1

        if subject:

            subject = (
                self._normalize_string(
                    subject
                )
            )

            self._add_unique(
                "subjects_seen",
                subject
            )

            self._register_subject_activity(
                subject,
                correct=correct
            )

            self.profile[
                "last_subject"
            ] = subject

        if topic:

            topic = (
                self._normalize_string(
                    topic
                )
            )

            self._add_unique(
                "topics_seen",
                topic
            )

            self._register_topic_activity(
                topic,
                correct=correct,
                confidence=confidence
            )

            self.profile[
                "last_topic"
            ] = topic

        if confidence is not None:

            self.set_confidence(
                topic=topic,
                confidence=confidence
            )

        return self._commit()

    # ============================================================
    # TOPIC ACTIVITY
    # ============================================================

    def _register_topic_activity(
        self,
        topic,
        correct=None,
        confidence=None
    ):
        """
        Internal topic statistics updater.
        """

        if not topic:

            return

        topics = self.profile[
            "topics"
        ]

        if topic not in topics:

            topics[topic] = {

                "attempts": 0,

                "correct": 0,

                "incorrect": 0,

                "confidence": 50,

                "first_seen":
                    self._now(),

                "last_seen":
                    self._now()

            }

        data = topics[
            topic
        ]

        data[
            "attempts"
        ] += 1

        if correct is True:

            data[
                "correct"
            ] += 1

        elif correct is False:

            data[
                "incorrect"
            ] += 1

        if confidence is not None:

            data[
                "confidence"
            ] = self._clamp_confidence(
                confidence
            )

        data[
            "last_seen"
        ] = self._now()

    # ============================================================
    # SUBJECT ACTIVITY
    # ============================================================

    def _register_subject_activity(
        self,
        subject,
        correct=None
    ):
        """
        Internal subject statistics updater.
        """

        if not subject:

            return

        subjects = self.profile[
            "subjects"
        ]

        if subject not in subjects:

            subjects[subject] = {

                "attempts": 0,

                "correct": 0,

                "incorrect": 0,

                "first_seen":
                    self._now(),

                "last_seen":
                    self._now()

            }

        data = subjects[
            subject
        ]

        data[
            "attempts"
        ] += 1

        if correct is True:

            data[
                "correct"
            ] += 1

        elif correct is False:

            data[
                "incorrect"
            ] += 1

        data[
            "last_seen"
        ] = self._now()

    # ============================================================
    # TOPIC LOOKUP
    # ============================================================

    def get_topic(
        self,
        topic
    ):
        """
        Return statistics for one topic.
        """

        if not topic:

            return None

        data = self.profile[
            "topics"
        ].get(
            str(topic)
        )

        if data is None:

            return None

        return deepcopy(
            data
        )

    # ============================================================
    # SUBJECT LOOKUP
    # ============================================================

    def get_subject(
        self,
        subject
    ):
        """
        Return statistics for one subject.
        """

        if not subject:

            return None

        data = self.profile[
            "subjects"
        ].get(
            str(subject)
        )

        if data is None:

            return None

        return deepcopy(
            data
        )

    # ============================================================
    # CONFIDENCE
    # ============================================================

    def set_confidence(
        self,
        topic,
        confidence
    ):
        """
        Store confidence for a topic.

        Confidence is clamped to 0-100.
        """

        if not topic:

            return False

        confidence = (
            self._clamp_confidence(
                confidence
            )
        )

        self.profile[
            "confidence"
        ][
            str(topic)
        ] = confidence

        if str(topic) in self.profile[
            "topics"
        ]:

            self.profile[
                "topics"
            ][
                str(topic)
            ][
                "confidence"
            ] = confidence

        return self._commit()

    # ============================================================
    # GET CONFIDENCE
    # ============================================================

    def get_confidence(
        self,
        topic,
        default=50
    ):
        """
        Return topic confidence.
        """

        if not topic:

            return default

        return self.profile[
            "confidence"
        ].get(
            str(topic),
            default
        )

    # ============================================================
    # MISTAKES
    # ============================================================

    def record_mistake(
        self,
        topic,
        mistake=None
    ):
        """
        Record a recurring mistake for a topic.
        """

        if not topic:

            return False

        topic = str(
            topic
        )

        mistakes = self.profile[
            "mistakes"
        ]

        if topic not in mistakes:

            mistakes[
                topic
            ] = []

        if mistake:

            mistake = (
                self._normalize_string(
                    mistake
                )
            )

            if mistake:

                mistakes[
                    topic
                ].append(
                    {
                        "description":
                            mistake,

                        "timestamp":
                            self._now()
                    }
                )

                # Keep the profile from growing forever.
                mistakes[
                    topic
                ] = mistakes[
                    topic
                ][-20:]

        return self._commit()

    # ============================================================
    # GET MISTAKES
    # ============================================================

    def get_mistakes(
        self,
        topic=None
    ):
        """
        Return mistakes globally or for one topic.
        """

        if topic:

            return deepcopy(
                self.profile[
                    "mistakes"
                ].get(
                    str(topic),
                    []
                )
            )

        return deepcopy(
            self.profile[
                "mistakes"
            ]
        )

    # ============================================================
    # STRENGTHS
    # ============================================================

    def add_strength(
        self,
        topic
    ):
        """
        Mark a topic as a strength.
        """

        if not topic:

            return False

        self._add_unique(
            "strengths",
            str(topic)
        )

        # If a topic becomes a strength, it should
        # not simultaneously remain a weakness.
        self._remove_value(
            "weaknesses",
            str(topic)
        )

        return self._commit()

    # ============================================================
    # WEAKNESSES
    # ============================================================

    def add_weakness(
        self,
        topic
    ):
        """
        Mark a topic as a weakness.
        """

        if not topic:

            return False

        self._add_unique(
            "weaknesses",
            str(topic)
        )

        self._remove_value(
            "strengths",
            str(topic)
        )

        return self._commit()

    # ============================================================
    # REMOVE STRENGTH
    # ============================================================

    def remove_strength(
        self,
        topic
    ):

        self._remove_value(
            "strengths",
            topic
        )

        return self._commit()

    # ============================================================
    # REMOVE WEAKNESS
    # ============================================================

    def remove_weakness(
        self,
        topic
    ):

        self._remove_value(
            "weaknesses",
            topic
        )

        return self._commit()

    # ============================================================
    # AUTO ANALYZE STRENGTHS / WEAKNESSES
    # ============================================================

    def refresh_learning_state(self):
        """
        Recalculate strengths and weaknesses from topic
        performance.

        Rules are intentionally conservative.

        Strength:
            at least 3 attempts
            and >= 75% success

        Weakness:
            at least 2 attempts
            and <= 40% success
        """

        strengths = []

        weaknesses = []

        for topic, data in self.profile[
            "topics"
        ].items():

            attempts = data.get(
                "attempts",
                0
            )

            correct = data.get(
                "correct",
                0
            )

            if attempts <= 0:

                continue

            success_rate = (
                correct / attempts
            ) * 100

            if (
                attempts >= 3
                and success_rate >= 75
            ):

                strengths.append(
                    topic
                )

            elif (
                attempts >= 2
                and success_rate <= 40
            ):

                weaknesses.append(
                    topic
                )

        self.profile[
            "strengths"
        ] = sorted(
            set(strengths)
        )

        self.profile[
            "weaknesses"
        ] = sorted(
            set(weaknesses)
        )

        return self._commit()

    # ============================================================
    # PREFERENCES
    # ============================================================

    def set_preference(
        self,
        key,
        value
    ):
        """
        Set one tutoring preference.
        """

        if not key:

            return False

        self.profile[
            "preferences"
        ][
            str(key)
        ] = deepcopy(
            value
        )

        return self._commit()

    # ============================================================
    # GET PREFERENCE
    # ============================================================

    def get_preference(
        self,
        key,
        default=None
    ):
        """
        Retrieve one tutoring preference.
        """

        return deepcopy(
            self.profile[
                "preferences"
            ].get(
                key,
                default
            )
        )

    # ============================================================
    # ALL PREFERENCES
    # ============================================================

    def get_preferences(self):

        return deepcopy(
            self.profile[
                "preferences"
            ]
        )

    # ============================================================
    # SESSION
    # ============================================================

    def start_session(self):
        """
        Register a new Nova learning session.
        """

        self.profile[
            "sessions_count"
        ] += 1

        self.profile[
            "last_active"
        ] = self._now()

        return self._commit()

    # ============================================================
    # ACTIVITY
    # ============================================================

    def touch(
        self,
        subject=None,
        topic=None
    ):
        """
        Update the student's latest activity without
        counting a new question.
        """

        self.profile[
            "last_active"
        ] = self._now()

        if subject:

            self.profile[
                "last_subject"
            ] = str(
                subject
            )

        if topic:

            self.profile[
                "last_topic"
            ] = str(
                topic
            )

        return self._commit()

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_statistics(self):
        """
        Return useful high-level learning statistics.
        """

        asked = self.profile.get(
            "questions_asked",
            0
        )

        answered = self.profile.get(
            "questions_answered",
            0
        )

        correct = self.profile.get(
            "successful_answers",
            0
        )

        incorrect = self.profile.get(
            "incorrect_answers",
            0
        )

        if answered > 0:

            accuracy = (
                correct / answered
            ) * 100

        else:

            accuracy = 0

        return {

            "questions_asked":
                asked,

            "questions_answered":
                answered,

            "successful_answers":
                correct,

            "incorrect_answers":
                incorrect,

            "accuracy":
                round(
                    accuracy,
                    2
                ),

            "topics_count":
                len(
                    self.profile.get(
                        "topics_seen",
                        []
                    )
                ),

            "subjects_count":
                len(
                    self.profile.get(
                        "subjects_seen",
                        []
                    )
                ),

            "strengths_count":
                len(
                    self.profile.get(
                        "strengths",
                        []
                    )
                ),

            "weaknesses_count":
                len(
                    self.profile.get(
                        "weaknesses",
                        []
                    )
                ),

            "sessions_count":
                self.profile.get(
                    "sessions_count",
                    0
                )
        }

    # ============================================================
    # LEARNING SUMMARY
    # ============================================================

    def get_learning_summary(self):
        """
        Return a compact summary suitable for NovaBrain
        or PromptBuilder.
        """

        return {

            "level":
                self.get_level(),

            "strengths":
                deepcopy(
                    self.profile[
                        "strengths"
                    ]
                ),

            "weaknesses":
                deepcopy(
                    self.profile[
                        "weaknesses"
                    ]
                ),

            "topics_seen":
                deepcopy(
                    self.profile[
                        "topics_seen"
                    ]
                ),

            "subjects_seen":
                deepcopy(
                    self.profile[
                        "subjects_seen"
                    ]
                ),

            "confidence":
                deepcopy(
                    self.profile[
                        "confidence"
                    ]
                ),

            "statistics":
                self.get_statistics(),

            "last_subject":
                self.profile.get(
                    "last_subject"
                ),

            "last_topic":
                self.profile.get(
                    "last_topic"
                )
        }

    # ============================================================
    # TOPIC LIST
    # ============================================================

    def get_topics(self):

        return list(
            self.profile.get(
                "topics_seen",
                []
            )
        )

    # ============================================================
    # SUBJECT LIST
    # ============================================================

    def get_subjects(self):

        return list(
            self.profile.get(
                "subjects_seen",
                []
            )
        )

    # ============================================================
    # STRENGTH LIST
    # ============================================================

    def get_strengths(self):

        return list(
            self.profile.get(
                "strengths",
                []
            )
        )

    # ============================================================
    # WEAKNESS LIST
    # ============================================================

    def get_weaknesses(self):

        return list(
            self.profile.get(
                "weaknesses",
                []
            )
        )

    # ============================================================
    # RESET
    # ============================================================

    def reset(
        self,
        keep_identity=True
    ):
        """
        Reset learning data.

        By default, the student's name and level are preserved.

        This is useful if Nova eventually gets a
        "Reset learning progress" setting.
        """

        name = self.get_name()

        level = self.get_level()

        self.profile = (
            self._create_default_profile(
                name=name
                if keep_identity
                else "Student",

                level=level
                if keep_identity
                else "beginner"
            )
        )

        return self._commit()

    # ============================================================
    # EXPORT
    # ============================================================

    def export(self):
        """
        Return a complete safe copy of the profile.
        """

        return deepcopy(
            self.profile
        )

    # ============================================================
    # IMPORT
    # ============================================================

    def import_profile(
        self,
        data
    ):
        """
        Replace the current profile with another
        dictionary after validation.
        """

        if not isinstance(
            data,
            dict
        ):

            return False

        self.profile = deepcopy(
            data
        )

        self._normalize_profile()

        return self._commit()

    # ============================================================
    # UTILITY: UNIQUE VALUE
    # ============================================================

    def _add_unique(
        self,
        field,
        value
    ):

        if not value:

            return

        values = self.profile.get(
            field
        )

        if not isinstance(
            values,
            list
        ):

            values = []

            self.profile[
                field
            ] = values

        if value not in values:

            values.append(
                value
            )

    # ============================================================
    # UTILITY: REMOVE VALUE
    # ============================================================

    def _remove_value(
        self,
        field,
        value
    ):

        if not value:

            return

        values = self.profile.get(
            field
        )

        if not isinstance(
            values,
            list
        ):

            return

        while value in values:

            values.remove(
                value
            )

    # ============================================================
    # UTILITY: STRING
    # ============================================================

    def _normalize_string(
        self,
        value,
        default=""
    ):

        if value is None:

            return default

        if not isinstance(
            value,
            str
        ):

            value = str(
                value
            )

        value = value.strip()

        if not value:

            return default

        return value

    # ============================================================
    # UTILITY: LEVEL
    # ============================================================

    def _normalize_level(
        self,
        level
    ):

        if not isinstance(
            level,
            str
        ):

            return self.DEFAULT_LEVEL

        level = (
            level.strip()
            .lower()
        )

        if level not in self.VALID_LEVELS:

            return self.DEFAULT_LEVEL

        return level

    # ============================================================
    # UTILITY: CONFIDENCE
    # ============================================================

    def _clamp_confidence(
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

            return 50

        confidence = max(
            0,
            min(
                100,
                confidence
            )
        )

        if confidence.is_integer():

            return int(
                confidence
            )

        return round(
            confidence,
            2
        )

    # ============================================================
    # UTILITY: CURRENT TIME
    # ============================================================

    def _now(self):

        return datetime.now().isoformat()

    # ============================================================
    # DEBUG INFORMATION
    # ============================================================

    def debug(self):
        """
        Return useful diagnostic information.

        This does not expose anything beyond the profile
        itself and basic storage information.
        """

        return {

            "file":
                str(
                    self.file
                ),

            "exists":
                self.file.exists(),

            "profile_version":
                self.profile.get(
                    "profile_version"
                ),

            "auto_save":
                self.auto_save,

            "statistics":
                self.get_statistics()
        }


# ================================================================
# OPTIONAL TEST
# ================================================================

if __name__ == "__main__":

    print(
        "Testing StudentProfile..."
    )

    profile = StudentProfile()

    print(
        "\nCurrent profile:"
    )

    print(
        json.dumps(
            profile.get(),
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\nAdding test activity..."
    )

    profile.add_question(
        topic="Newton's Second Law",
        subject="physics"
    )

    profile.record_answer(
        correct=True,
        topic="Newton's Second Law",
        subject="physics",
        confidence=78
    )

    profile.add_strength(
        "Newton's Second Law"
    )

    print(
        "\nLearning summary:"
    )

    print(
        json.dumps(
            profile.get_learning_summary(),
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\nStatistics:"
    )

    print(
        json.dumps(
            profile.get_statistics(),
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\nStudentProfile test complete."
    )