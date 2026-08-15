import json
import os
import re
from datetime import datetime


class UnderstandingAnalyzer:
    """
    Analyse l'évolution de la compréhension d'un étudiant.

    Cette classe ne prétend pas connaître exactement ce que
    l'étudiant comprend. Elle construit une estimation à partir
    de plusieurs signaux observables.

    Elle peut notamment détecter :

        - confusion
        - compréhension explicite
        - demande de clarification
        - demande d'exemple
        - demande de simplification
        - difficulté
        - frustration
        - progression
        - régression
        - répétition d'une question
        - demandes d'explication supplémentaires

    Le système utilise plusieurs métriques :

        confidence
            Estimation générale de confiance.

        understanding
            Estimation de compréhension.

        engagement
            Niveau d'implication dans l'apprentissage.

        difficulty
            Difficulté perçue du sujet.

        attempts
            Nombre d'interactions analysées.

    Important :
        Ces valeurs sont des estimations heuristiques.
        Elles ne doivent jamais être considérées comme une
        mesure psychologique exacte.
    """

    # =========================================
    # INITIALIZATION
    # =========================================

    def __init__(
        self,
        history_limit=50,
        signal_limit=50,
        initial_confidence=50,
        initial_understanding=50
    ):
        self.history = {}

        self.history_limit = max(
            5,
            int(history_limit)
        )

        self.signal_limit = max(
            5,
            int(signal_limit)
        )

        self.initial_confidence = self._clamp(
            initial_confidence
        )

        self.initial_understanding = self._clamp(
            initial_understanding
        )

        # =====================================
        # SIGNAL DEFINITIONS
        # =====================================

        self.confusion_signals = [
            "i don't understand",
            "i do not understand",
            "i don't get it",
            "i do not get it",
            "i'm confused",
            "i am confused",
            "i'm lost",
            "i am lost",
            "too difficult",
            "too hard",
            "this is difficult",
            "this is hard",
            "i still don't understand",
            "i still do not understand",
            "i still don't get it",
            "i still do not get it",
            "i'm still confused",
            "i am still confused",
            "nothing makes sense",
            "i don't know what this means",
            "i have no idea"
        ]

        self.understanding_signals = [
            "i understand",
            "i do understand",
            "i get it",
            "i get it now",
            "i understand now",
            "that makes sense",
            "this makes sense",
            "now i understand",
            "now i get it",
            "i see",
            "i see now",
            "that is clear",
            "it's clear now",
            "it is clear now",
            "i figured it out"
        ]

        self.clarification_signals = [
            "can you explain",
            "can you clarify",
            "what does that mean",
            "what do you mean",
            "why is that",
            "why does that happen",
            "how does that work",
            "can you explain that",
            "can you explain this"
        ]

        self.example_signals = [
            "give me an example",
            "can you give an example",
            "show me an example",
            "real life example",
            "real-life example",
            "example please",
            "another example",
            "give another example"
        ]

        self.simplification_signals = [
            "explain simply",
            "explain it simply",
            "simplify",
            "make it simpler",
            "use simple words",
            "easy words",
            "explain like i'm new",
            "explain it easier",
            "make this easier",
            "in simple terms"
        ]

        self.frustration_signals = [
            "this is annoying",
            "i'm frustrated",
            "i am frustrated",
            "i don't understand anything",
            "this makes no sense",
            "why is this so hard",
            "i hate this",
            "i can't do this",
            "i cannot do this"
        ]

        self.repeat_signals = [
            "again",
            "once again",
            "explain again",
            "say that again",
            "repeat",
            "another explanation",
            "different explanation"
        ]

        self.positive_learning_signals = [
            "i solved it",
            "i got the answer",
            "i figured it out",
            "i know how",
            "i can do it",
            "i can solve it",
            "that was easy",
            "i understand how"
        ]

        # =====================================
        # SIGNAL WEIGHTS
        # =====================================

        self.signal_weights = {
            "confusion": -10,
            "understanding": 10,
            "clarification": -3,
            "example_request": -2,
            "simplification_request": -6,
            "frustration": -8,
            "repeat_request": -4,
            "positive_learning": 8,
            "neutral": 0
        }

    # =========================================
    # MAIN ANALYSIS
    # =========================================

    def analyze(
        self,
        subject,
        question,
        answer
    ):
        """
        Analyze a new student interaction.

        Returns a dictionary compatible with the older
        NovaCore implementation.
        """

        subject = self._normalize_subject(
            subject
        )

        question = self._normalize_text(
            question
        )

        answer = self._normalize_text(
            answer
        )

        if not subject:
            subject = "general"

        data = self._get_or_create_subject(
            subject
        )

        previous_confidence = data[
            "confidence"
        ]

        previous_understanding = data[
            "understanding"
        ]

        data["attempts"] += 1

        # =====================================
        # SIGNAL DETECTION
        # =====================================

        signals = self.detect_signals(
            question
        )

        data["last_signals"] = list(
            signals
        )

        for signal in signals:

            self._record_signal(
                data,
                signal
            )

        # =====================================
        # QUESTION ANALYSIS
        # =====================================

        question_analysis = (
            self.analyze_question(
                question
            )
        )

        data["question_types"] = (
            self._increment_categories(
                data.get(
                    "question_types",
                    {}
                ),
                question_analysis[
                    "types"
                ]
            )
        )

        # =====================================
        # ANSWER ANALYSIS
        # =====================================

        answer_analysis = (
            self.analyze_answer(
                answer
            )
        )

        # =====================================
        # CALCULATE SIGNAL EFFECT
        # =====================================

        signal_effect = (
            self.calculate_signal_effect(
                signals
            )
        )

        # =====================================
        # UNDERSTANDING UPDATE
        # =====================================

        understanding_change = (
            self.calculate_understanding_change(
                signals,
                question_analysis
            )
        )

        data["understanding"] = self._clamp(
            data["understanding"]
            + understanding_change
        )

        # =====================================
        # CONFIDENCE UPDATE
        # =====================================

        confidence_change = (
            self.calculate_confidence_change(
                signal_effect,
                question_analysis
            )
        )

        data["confidence"] = self._clamp(
            data["confidence"]
            + confidence_change
        )

        # =====================================
        # ENGAGEMENT
        # =====================================

        engagement_change = (
            self.calculate_engagement_change(
                signals,
                question_analysis
            )
        )

        data["engagement"] = self._clamp(
            data["engagement"]
            + engagement_change
        )

        # =====================================
        # DIFFICULTY ESTIMATION
        # =====================================

        data["difficulty"] = (
            self.estimate_difficulty(
                signals,
                question_analysis,
                data
            )
        )

        # =====================================
        # DETECT TREND
        # =====================================

        trend = self.detect_trend(
            previous_confidence,
            data["confidence"],
            previous_understanding,
            data["understanding"]
        )

        data["trend"] = trend

        # =====================================
        # RESPONSE QUALITY
        # =====================================

        data["last_answer_analysis"] = (
            answer_analysis
        )

        # =====================================
        # LEARNING STATE
        # =====================================

        data["learning_state"] = (
            self.determine_learning_state(
                data
            )
        )

        # =====================================
        # RECOMMENDATION
        # =====================================

        data["recommended_action"] = (
            self.recommend_teaching_action(
                data
            )
        )

        # =====================================
        # HISTORY
        # =====================================

        event = {
            "timestamp":
                self._timestamp(),

            "question":
                question,

            "signals":
                list(signals),

            "confidence":
                data["confidence"],

            "understanding":
                data["understanding"],

            "engagement":
                data["engagement"],

            "difficulty":
                data["difficulty"],

            "trend":
                trend
        }

        data["history"].append(
            event
        )

        if len(
            data["history"]
        ) > self.history_limit:

            data["history"] = (
                data["history"][
                    -self.history_limit:
                ]
            )

        # =====================================
        # GLOBAL STATISTICS
        # =====================================

        self._update_global_statistics(
            subject,
            data
        )

        return self._public_result(
            subject,
            data
        )

    # =========================================
    # SIGNAL DETECTION
    # =========================================

    def detect_signals(
        self,
        text
    ):
        """
        Detect learning signals in the student's
        current message.

        Multiple signals may be returned.
        """

        text = self._normalize_text(
            text
        ).lower()

        if not text:
            return ["neutral"]

        detected = []

        if self._contains_any(
            text,
            self.confusion_signals
        ):
            detected.append(
                "confusion"
            )

        if self._contains_any(
            text,
            self.understanding_signals
        ):
            detected.append(
                "understanding"
            )

        if self._contains_any(
            text,
            self.clarification_signals
        ):
            detected.append(
                "clarification"
            )

        if self._contains_any(
            text,
            self.example_signals
        ):
            detected.append(
                "example_request"
            )

        if self._contains_any(
            text,
            self.simplification_signals
        ):
            detected.append(
                "simplification_request"
            )

        if self._contains_any(
            text,
            self.frustration_signals
        ):
            detected.append(
                "frustration"
            )

        if self._contains_any(
            text,
            self.repeat_signals
        ):
            detected.append(
                "repeat_request"
            )

        if self._contains_any(
            text,
            self.positive_learning_signals
        ):
            detected.append(
                "positive_learning"
            )

        # =====================================
        # CONTRADICTIONS
        # =====================================

        if (
            "understanding" in detected
            and "confusion" in detected
        ):

            detected.append(
                "mixed_signal"
            )

        if not detected:

            detected.append(
                "neutral"
            )

        return detected

    # =========================================
    # QUESTION ANALYSIS
    # =========================================

    def analyze_question(
        self,
        question
    ):
        """
        Determine what kind of learning request
        the student is making.
        """

        text = self._normalize_text(
            question
        ).lower()

        types = []

        if not text:
            types.append(
                "empty"
            )

        if "why" in text:
            types.append(
                "why"
            )

        if (
            "how"
            in text
        ):
            types.append(
                "how"
            )

        if (
            "what"
            in text
        ):
            types.append(
                "definition"
            )

        if (
            "example"
            in text
        ):
            types.append(
                "example"
            )

        if any(
            word in text
            for word in [
                "solve",
                "calculate",
                "work out",
                "find"
            ]
        ):
            types.append(
                "problem_solving"
            )

        if any(
            word in text
            for word in [
                "explain",
                "clarify",
                "understand"
            ]
        ):
            types.append(
                "explanation"
            )

        if not types:

            types.append(
                "general"
            )

        complexity = self.estimate_question_complexity(
            text
        )

        return {
            "types": types,
            "complexity": complexity,
            "word_count": len(
                text.split()
            ),
            "question_length": len(text)
        }

    # =========================================
    # QUESTION COMPLEXITY
    # =========================================

    def estimate_question_complexity(
        self,
        text
    ):
        """
        Estimate question complexity using simple
        observable characteristics.

        This is intentionally conservative.
        """

        words = text.split()

        score = 0

        if len(words) > 15:
            score += 1

        if len(words) > 30:
            score += 1

        if "why" in text:
            score += 1

        if "compare" in text:
            score += 1

        if "difference" in text:
            score += 1

        if "calculate" in text:
            score += 1

        if "prove" in text:
            score += 2

        if "derive" in text:
            score += 2

        if score >= 4:
            return "high"

        if score >= 2:
            return "medium"

        return "low"

    # =========================================
    # ANSWER ANALYSIS
    # =========================================

    def analyze_answer(
        self,
        answer
    ):
        """
        Analyze the generated tutor answer.

        This does NOT verify factual correctness.
        That belongs to AnswerVerifier.

        It only checks basic structural properties.
        """

        answer = self._normalize_text(
            answer
        )

        words = answer.split()

        return {
            "word_count":
                len(words),

            "has_example":
                "example" in answer.lower(),

            "has_question":
                "?" in answer,

            "has_steps":
                bool(
                    re.search(
                        r"\b(step|first|second|third)\b",
                        answer.lower()
                    )
                ),

            "is_empty":
                not bool(answer),

            "length_category":
                self._answer_length_category(
                    len(words)
                )
        }

    # =========================================
    # SIGNAL EFFECT
    # =========================================

    def calculate_signal_effect(
        self,
        signals
    ):
        """
        Calculate the combined impact of detected
        learning signals.
        """

        if not signals:
            return 0

        total = 0

        for signal in signals:

            total += self.signal_weights.get(
                signal,
                0
            )

        # =====================================
        # MIXED SIGNAL PROTECTION
        # =====================================

        if "mixed_signal" in signals:

            # Conflicting evidence should have a
            # smaller effect than a strong single signal.
            total = int(
                total * 0.5
            )

        return self._clamp_change(
            total,
            maximum=15
        )

    # =========================================
    # UNDERSTANDING CHANGE
    # =========================================

    def calculate_understanding_change(
        self,
        signals,
        question_analysis
    ):
        """
        Estimate how the student's understanding
        should change from the current message.
        """

        change = 0

        if "confusion" in signals:
            change -= 8

        if "simplification_request" in signals:
            change -= 5

        if "clarification" in signals:
            change -= 2

        if "understanding" in signals:
            change += 8

        if "positive_learning" in signals:
            change += 7

        # Asking deep questions is not automatically
        # a sign of poor understanding.
        if (
            question_analysis["complexity"]
            == "high"
        ):

            if (
                "confusion"
                not in signals
            ):

                change += 1

        return self._clamp_change(
            change,
            maximum=12
        )

    # =========================================
    # CONFIDENCE CHANGE
    # =========================================

    def calculate_confidence_change(
        self,
        signal_effect,
        question_analysis
    ):
        change = signal_effect

        if (
            question_analysis["complexity"]
            == "high"
        ):

            # Complex questions should not cause a
            # confidence penalty by themselves.
            if change < 0:
                change = int(
                    change * 0.75
                )

        return self._clamp_change(
            change,
            maximum=12
        )

    # =========================================
    # ENGAGEMENT CHANGE
    # =========================================

    def calculate_engagement_change(
        self,
        signals,
        question_analysis
    ):
        change = 0

        if "clarification" in signals:
            change += 3

        if "example_request" in signals:
            change += 4

        if "understanding" in signals:
            change += 3

        if "positive_learning" in signals:
            change += 5

        if "frustration" in signals:
            change -= 5

        return self._clamp_change(
            change,
            maximum=8
        )

    # =========================================
    # DIFFICULTY ESTIMATION
    # =========================================

    def estimate_difficulty(
        self,
        signals,
        question_analysis,
        data
    ):
        """
        Estimate the perceived difficulty of the
        current interaction.
        """

        score = 0

        if "confusion" in signals:
            score += 3

        if "simplification_request" in signals:
            score += 2

        if "frustration" in signals:
            score += 2

        if "clarification" in signals:
            score += 1

        if question_analysis[
            "complexity"
        ] == "high":

            score += 2

        elif question_analysis[
            "complexity"
        ] == "medium":

            score += 1

        if score >= 5:
            return "hard"

        if score >= 2:
            return "medium"

        return "easy"

    # =========================================
    # TREND
    # =========================================

    def detect_trend(
        self,
        previous_confidence,
        current_confidence,
        previous_understanding,
        current_understanding
    ):
        confidence_delta = (
            current_confidence
            - previous_confidence
        )

        understanding_delta = (
            current_understanding
            - previous_understanding
        )

        total_delta = (
            confidence_delta
            + understanding_delta
        )

        if total_delta >= 8:
            return "improving"

        if total_delta <= -8:
            return "declining"

        return "stable"

    # =========================================
    # LEARNING STATE
    # =========================================

    def determine_learning_state(
        self,
        data
    ):
        understanding = data.get(
            "understanding",
            50
        )

        confidence = data.get(
            "confidence",
            50
        )

        difficulty = data.get(
            "difficulty",
            "medium"
        )

        if understanding < 30:
            return "struggling"

        if understanding < 50:
            return "developing"

        if (
            understanding >= 70
            and confidence >= 70
        ):

            return "understood"

        if (
            understanding >= 85
            and confidence >= 80
        ):

            return "strong"

        if difficulty == "hard":
            return "challenged"

        return "developing"

    # =========================================
    # TEACHING RECOMMENDATION
    # =========================================

    def recommend_teaching_action(
        self,
        data
    ):
        state = data.get(
            "learning_state",
            "developing"
        )

        trend = data.get(
            "trend",
            "stable"
        )

        if state == "struggling":

            return (
                "Return to the fundamentals, "
                "simplify the explanation, "
                "and use a concrete example."
            )

        if state == "challenged":

            return (
                "Break the problem into smaller "
                "steps and reinforce the key concept."
            )

        if (
            state == "understood"
            and trend == "improving"
        ):

            return (
                "Gradually increase difficulty and "
                "offer a small reasoning challenge."
            )

        if state == "strong":

            return (
                "Use deeper explanations, "
                "advanced applications and "
                "independent reasoning."
            )

        return (
            "Continue with a clear explanation "
            "and monitor the student's next response."
        )

    # =========================================
    # GET OR CREATE
    # =========================================

    def _get_or_create_subject(
        self,
        subject
    ):
        if subject not in self.history:

            self.history[subject] = {
                "attempts": 0,

                "confidence":
                    self.initial_confidence,

                "understanding":
                    self.initial_understanding,

                "engagement":
                    50,

                "difficulty":
                    "medium",

                "learning_state":
                    "developing",

                "trend":
                    "stable",

                "mistakes":
                    [],

                "signals":
                    [],

                "last_signals":
                    [],

                "question_types":
                    {},

                "history":
                    [],

                "recommended_action":
                    "Continue monitoring."
            }

        return self.history[subject]

    # =========================================
    # RECORD SIGNAL
    # =========================================

    def _record_signal(
        self,
        data,
        signal
    ):
        signals = data.setdefault(
            "signals",
            []
        )

        signals.append(
            signal
        )

        if len(signals) > self.signal_limit:

            del signals[
                :-self.signal_limit
            ]

    # =========================================
    # GLOBAL STATISTICS
    # =========================================

    def _update_global_statistics(
        self,
        subject,
        data
    ):
        """
        Keep a small global summary.

        This information is derived from subject
        histories and can be used by higher-level
        systems.
        """

        global_data = self.history.setdefault(
            "__global__",
            {
                "attempts": 0,
                "subjects": set()
            }
        )

        if not isinstance(
            global_data.get("subjects"),
            set
        ):

            global_data["subjects"] = set(
                global_data.get(
                    "subjects",
                    []
                )
            )

        global_data["attempts"] += 1

        global_data["subjects"].add(
            subject
        )

    # =========================================
    # RESULT
    # =========================================

    def _public_result(
        self,
        subject,
        data
    ):
        """
        Return a safe dictionary without exposing
        unnecessary internal references.
        """

        result = dict(
            data
        )

        result["subject"] = (
            subject
        )

        result["history"] = list(
            data.get(
                "history",
                []
            )
        )

        result["signals"] = list(
            data.get(
                "signals",
                []
            )
        )

        result["last_signals"] = list(
            data.get(
                "last_signals",
                []
            )
        )

        return result

    # =========================================
    # GET
    # =========================================

    def get(
        self,
        subject=None
    ):
        """
        Return all history or one subject.
        """

        if subject is None:

            return self._serialize(
                self.history
            )

        subject = self._normalize_subject(
            subject
        )

        if subject not in self.history:

            return None

        return self._serialize(
            self.history[subject]
        )

    # =========================================
    # GET CONFIDENCE
    # =========================================

    def get_confidence(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:
            return self.initial_confidence

        return data.get(
            "confidence",
            self.initial_confidence
        )

    # =========================================
    # GET UNDERSTANDING
    # =========================================

    def get_understanding(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:
            return self.initial_understanding

        return data.get(
            "understanding",
            self.initial_understanding
        )

    # =========================================
    # GET STATE
    # =========================================

    def get_learning_state(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:

            return "unknown"

        return data.get(
            "learning_state",
            "developing"
        )

    # =========================================
    # GET TREND
    # =========================================

    def get_trend(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:

            return "unknown"

        return data.get(
            "trend",
            "stable"
        )

    # =========================================
    # GET RECOMMENDATION
    # =========================================

    def get_recommendation(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:

            return (
                "Start with a clear explanation "
                "and monitor understanding."
            )

        return data.get(
            "recommended_action",
            "Continue monitoring."
        )

    # =========================================
    # SUBJECT SUMMARY
    # =========================================

    def summarize_subject(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:

            return {
                "subject":
                    self._normalize_subject(
                        subject
                    ),

                "attempts":
                    0,

                "confidence":
                    self.initial_confidence,

                "understanding":
                    self.initial_understanding,

                "state":
                    "unknown",

                "trend":
                    "unknown"
            }

        return {
            "subject":
                self._normalize_subject(
                    subject
                ),

            "attempts":
                data.get(
                    "attempts",
                    0
                ),

            "confidence":
                data.get(
                    "confidence",
                    50
                ),

            "understanding":
                data.get(
                    "understanding",
                    50
                ),

            "engagement":
                data.get(
                    "engagement",
                    50
                ),

            "difficulty":
                data.get(
                    "difficulty",
                    "medium"
                ),

            "state":
                data.get(
                    "learning_state",
                    "developing"
                ),

            "trend":
                data.get(
                    "trend",
                    "stable"
                ),

            "recommended_action":
                data.get(
                    "recommended_action",
                    ""
                )
        }

    # =========================================
    # RECENT HISTORY
    # =========================================

    def get_recent_history(
        self,
        subject,
        limit=10
    ):
        data = self.get(
            subject
        )

        if not data:

            return []

        history = data.get(
            "history",
            []
        )

        try:

            limit = max(
                1,
                int(limit)
            )

        except (
            TypeError,
            ValueError
        ):

            limit = 10

        return history[-limit:]

    # =========================================
    # RESET SUBJECT
    # =========================================

    def reset_subject(
        self,
        subject
    ):
        subject = self._normalize_subject(
            subject
        )

        if subject in self.history:

            del self.history[
                subject
            ]

            return True

        return False

    # =========================================
    # RESET EVERYTHING
    # =========================================

    def reset(
        self
    ):
        self.history = {}

    # =========================================
    # EXPORT
    # =========================================

    def export(
        self,
        filepath
    ):
        """
        Save analyzer history to JSON.
        """

        directory = os.path.dirname(
            filepath
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        data = self._serialize(
            self.history
        )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # =========================================
    # IMPORT
    # =========================================

    def import_data(
        self,
        filepath
    ):
        """
        Load analyzer history from JSON.
        """

        if not os.path.exists(
            filepath
        ):

            return False

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            if not isinstance(
                data,
                dict
            ):

                return False

            self.history = data

            return True

        except (
            OSError,
            json.JSONDecodeError
        ):

            return False

    # =========================================
    # HELPERS
    # =========================================

    def _normalize_subject(
        self,
        subject
    ):
        if subject is None:
            return ""

        subject = str(
            subject
        ).strip().lower()

        return subject

    def _normalize_text(
        self,
        text
    ):
        if text is None:
            return ""

        return str(
            text
        ).strip()

    def _contains_any(
        self,
        text,
        signals
    ):
        return any(
            signal in text
            for signal in signals
        )

    def _clamp(
        self,
        value,
        minimum=0,
        maximum=100
    ):
        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            value = minimum

        value = max(
            minimum,
            min(
                maximum,
                value
            )
        )

        return int(
            value
        )

    def _clamp_change(
        self,
        value,
        maximum=15
    ):
        return max(
            -maximum,
            min(
                maximum,
                int(value)
            )
        )

    def _timestamp(
        self
    ):
        return datetime.utcnow().isoformat()

    def _answer_length_category(
        self,
        word_count
    ):
        if word_count < 20:
            return "short"

        if word_count < 100:
            return "medium"

        return "long"

    def _increment_categories(
        self,
        dictionary,
        categories
    ):
        if not isinstance(
            dictionary,
            dict
        ):

            dictionary = {}

        for category in categories:

            dictionary[category] = (
                dictionary.get(
                    category,
                    0
                )
                + 1
            )

        return dictionary

    def _serialize(
        self,
        value
    ):
        """
        Convert internal Python structures into
        JSON-safe structures.
        """

        if isinstance(
            value,
            dict
        ):

            return {
                key:
                    self._serialize(
                        item
                    )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            (list, tuple)
        ):

            return [
                self._serialize(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            set
        ):

            return [
                self._serialize(
                    item
                )
                for item in value
            ]

        return value


# ============================================================
# UNDERSTANDING TRACKER
# ============================================================


class UnderstandingTracker:
    """
    Tracks the difficulty distribution encountered by
    the student.

    Example:

        physics:
            easy: 4
            medium: 7
            hard: 2

    The tracker is deliberately independent from
    UnderstandingAnalyzer.

    Analyzer:
        estimates understanding.

    Tracker:
        records difficulty exposure.

    This separation keeps Nova's architecture cleaner.
    """

    VALID_DIFFICULTIES = {
        "easy",
        "medium",
        "hard"
    }

    def __init__(
        self,
        history_limit=100
    ):
        self.data = {}

        self.history_limit = max(
            10,
            int(history_limit)
        )

    # =========================================
    # UPDATE
    # =========================================

    def update(
        self,
        subject,
        difficulty
    ):
        """
        Record one difficulty occurrence.
        """

        subject = self._normalize_subject(
            subject
        )

        difficulty = self._normalize_difficulty(
            difficulty
        )

        if not subject:
            return False

        if not difficulty:
            return False

        data = self._get_or_create(
            subject
        )

        data[difficulty] += 1

        data["total"] += 1

        data["history"].append(
            {
                "difficulty":
                    difficulty,

                "timestamp":
                    datetime.utcnow().isoformat()
            }
        )

        if len(
            data["history"]
        ) > self.history_limit:

            data["history"] = (
                data["history"][
                    -self.history_limit:
                ]
            )

        return True

    # =========================================
    # RECORD MULTIPLE
    # =========================================

    def record_many(
        self,
        subject,
        difficulties
    ):
        if not isinstance(
            difficulties,
            (list, tuple)
        ):

            return 0

        count = 0

        for difficulty in difficulties:

            if self.update(
                subject,
                difficulty
            ):

                count += 1

        return count

    # =========================================
    # GET
    # =========================================

    def get(
        self,
        subject=None
    ):
        if subject is None:

            return self._copy(
                self.data
            )

        subject = self._normalize_subject(
            subject
        )

        if subject not in self.data:

            return None

        return self._copy(
            self.data[subject]
        )

    # =========================================
    # TOTAL
    # =========================================

    def total_attempts(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:
            return 0

        return data.get(
            "total",
            0
        )

    # =========================================
    # DISTRIBUTION
    # =========================================

    def distribution(
        self,
        subject
    ):
        data = self.get(
            subject
        )

        if not data:

            return {
                "easy": 0,
                "medium": 0,
                "hard": 0
            }

        return {
            "easy":
                data.get(
                    "easy",
                    0
                ),

            "medium":
                data.get(
                    "medium",
                    0
                ),

            "hard":
                data.get(
                    "hard",
                    0
                )
        }

    # =========================================
    # PERCENTAGES
    # =========================================

    def percentages(
        self,
        subject
    ):
        distribution = self.distribution(
            subject
        )

        total = sum(
            distribution.values()
        )

        if total == 0:

            return {
                "easy": 0.0,
                "medium": 0.0,
                "hard": 0.0
            }

        return {
            difficulty:
                round(
                    (
                        count
                        / total
                    ) * 100,
                    2
                )
            for difficulty, count
            in distribution.items()
        }

    # =========================================
    # MOST COMMON
    # =========================================

    def most_common(
        self,
        subject
    ):
        distribution = self.distribution(
            subject
        )

        return max(
            distribution,
            key=distribution.get
        )

    # =========================================
    # DIFFICULTY SCORE
    # =========================================

    def difficulty_score(
        self,
        subject
    ):
        """
        Convert difficulty exposure into a rough
        numeric score from 0 to 100.

        easy   = 25
        medium = 50
        hard   = 100
        """

        distribution = self.distribution(
            subject
        )

        total = sum(
            distribution.values()
        )

        if total == 0:
            return 0

        score = (
            distribution["easy"] * 25
            + distribution["medium"] * 50
            + distribution["hard"] * 100
        )

        return round(
            score / total,
            2
        )

    # =========================================
    # RECENT
    # =========================================

    def recent(
        self,
        subject,
        limit=10
    ):
        data = self.get(
            subject
        )

        if not data:
            return []

        try:

            limit = max(
                1,
                int(limit)
            )

        except (
            TypeError,
            ValueError
        ):

            limit = 10

        return data.get(
            "history",
            []
        )[-limit:]

    # =========================================
    # RESET SUBJECT
    # =========================================

    def reset_subject(
        self,
        subject
    ):
        subject = self._normalize_subject(
            subject
        )

        if subject in self.data:

            del self.data[
                subject
            ]

            return True

        return False

    # =========================================
    # RESET
    # =========================================

    def reset(
        self
    ):
        self.data = {}

    # =========================================
    # EXPORT
    # =========================================

    def export(
        self,
        filepath
    ):
        directory = os.path.dirname(
            filepath
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # =========================================
    # IMPORT
    # =========================================

    def import_data(
        self,
        filepath
    ):
        if not os.path.exists(
            filepath
        ):

            return False

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                loaded = json.load(
                    file
                )

            if not isinstance(
                loaded,
                dict
            ):

                return False

            self.data = loaded

            return True

        except (
            OSError,
            json.JSONDecodeError
        ):

            return False

    # =========================================
    # INTERNAL
    # =========================================

    def _get_or_create(
        self,
        subject
    ):
        if subject not in self.data:

            self.data[subject] = {
                "easy": 0,
                "medium": 0,
                "hard": 0,
                "total": 0,
                "history": []
            }

        return self.data[subject]

    def _normalize_subject(
        self,
        subject
    ):
        if subject is None:
            return ""

        return str(
            subject
        ).strip().lower()

    def _normalize_difficulty(
        self,
        difficulty
    ):
        if difficulty is None:
            return ""

        if isinstance(
            difficulty,
            dict
        ):

            difficulty = difficulty.get(
                "level"
            )

        if difficulty is None:
            return ""

        difficulty = str(
            difficulty
        ).strip().lower()

        aliases = {
            "beginner": "easy",
            "basic": "easy",
            "low": "easy",

            "normal": "medium",
            "moderate": "medium",
            "intermediate": "medium",

            "advanced": "hard",
            "high": "hard",
            "difficult": "hard"
        }

        difficulty = aliases.get(
            difficulty,
            difficulty
        )

        if difficulty not in self.VALID_DIFFICULTIES:

            return ""

        return difficulty

    def _copy(
        self,
        value
    ):
        if isinstance(
            value,
            dict
        ):

            return {
                key:
                    self._copy(
                        item
                    )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            list
        ):

            return [
                self._copy(
                    item
                )
                for item in value
            ]

        return value