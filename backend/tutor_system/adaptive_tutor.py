"""
Nova Adaptive Tutor
===================

This module decides how Nova should teach a student.

The goal is not simply to choose:

    beginner / intermediate / advanced

A real adaptive tutor needs to consider several signals at once:

- Student profile level
- Current message
- Subject
- Explicit requests for simpler/deeper explanations
- Confusion signals
- Understanding signals
- Previous confidence
- Strengths and weaknesses
- Repeated attempts
- Requested detail
- Whether the student is asking for an exercise
- Whether the student is asking for a definition
- Whether the student needs a step-by-step explanation
- Whether the student appears ready for a challenge

The class produces a teaching instruction that can be passed
to the PromptBuilder and ultimately to the local LLM.

This file does NOT generate the final answer.
It decides HOW Nova should teach.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class AdaptiveTutor:

    # ============================================================
    # LEVEL DEFINITIONS
    # ============================================================

    LEVELS = {
        "beginner": 0,
        "intermediate": 1,
        "advanced": 2,
        "mastery": 3
    }

    REVERSE_LEVELS = {
        0: "beginner",
        1: "intermediate",
        2: "advanced",
        3: "mastery"
    }

    # ============================================================
    # EXPLICIT BEGINNER SIGNALS
    # ============================================================

    BEGINNER_SIGNALS = [

        "explain simply",
        "explain simple",
        "simplify",
        "simple explanation",
        "easy words",
        "in simple words",
        "use simple words",
        "explain like i'm new",
        "explain like i am new",
        "i'm a beginner",
        "i am a beginner",
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
        "this is too difficult",
        "make it easier",
        "make this easier",
        "break it down",
        "break this down",
        "start from the beginning",
        "start from basics",
        "explain the basics",
        "teach me the basics"
    ]

    # ============================================================
    # EXPLICIT INTERMEDIATE SIGNALS
    # ============================================================

    INTERMEDIATE_SIGNALS = [

        "explain clearly",
        "moderate detail",
        "give me more detail",
        "more detail",
        "explain a little more",
        "explain further",
        "can you elaborate",
        "elaborate",
        "give me an example",
        "show me an example",
        "connect the ideas",
        "how does this work",
        "how does it work",
        "why does this work",
        "explain the reasoning"
    ]

    # ============================================================
    # EXPLICIT ADVANCED SIGNALS
    # ============================================================

    ADVANCED_SIGNALS = [

        "explain deeply",
        "more advanced",
        "go deeper",
        "technical details",
        "technical vocabulary",
        "advanced explanation",
        "advanced details",
        "deep explanation",
        "in depth",
        "in-depth",
        "give me the theory",
        "explain the theory",
        "mathematical derivation",
        "formal explanation",
        "rigorous explanation",
        "more rigorous",
        "don't simplify",
        "do not simplify",
        "assume i know the basics"
    ]

    # ============================================================
    # MASTERY SIGNALS
    # ============================================================

    MASTERY_SIGNALS = [

        "challenge me",
        "give me a difficult question",
        "give me a hard question",
        "test my understanding",
        "test me",
        "advanced problem",
        "harder problem",
        "harder question",
        "olympiad",
        "competition level",
        "expert level",
        "mastery",
        "push me"
    ]

    # ============================================================
    # CONFUSION SIGNALS
    # ============================================================

    CONFUSION_SIGNALS = [

        "i don't understand",
        "i do not understand",
        "i don't get it",
        "i do not get it",
        "i'm confused",
        "i am confused",
        "i'm lost",
        "i am lost",
        "i have no idea",
        "this makes no sense",
        "i still don't understand",
        "i still do not understand",
        "i'm struggling",
        "i am struggling",
        "i can't understand",
        "i cannot understand",
        "too hard",
        "too difficult",
        "confusing"
    ]

    # ============================================================
    # UNDERSTANDING SIGNALS
    # ============================================================

    UNDERSTANDING_SIGNALS = [

        "i understand",
        "i understand now",
        "i get it",
        "i get it now",
        "that makes sense",
        "makes sense",
        "i see",
        "i see now",
        "got it",
        "got it now",
        "that is clear",
        "that's clear",
        "it's clear now",
        "it is clear now"
    ]

    # ============================================================
    # STEP-BY-STEP SIGNALS
    # ============================================================

    STEP_SIGNALS = [

        "step by step",
        "step-by-step",
        "show every step",
        "show the steps",
        "walk me through",
        "walk me through it",
        "how do i solve",
        "how can i solve",
        "show me how",
        "show the method",
        "show your work",
        "show the working"
    ]

    # ============================================================
    # SHORT ANSWER SIGNALS
    # ============================================================

    CONCISE_SIGNALS = [

        "short answer",
        "briefly",
        "in short",
        "keep it short",
        "keep this short",
        "quick explanation",
        "quick answer",
        "just the answer",
        "only the answer",
        "summarize",
        "summary"
    ]

    # ============================================================
    # DETAIL SIGNALS
    # ============================================================

    DETAIL_SIGNALS = [

        "detailed",
        "in detail",
        "explain everything",
        "full explanation",
        "complete explanation",
        "thorough explanation",
        "deep explanation",
        "go into detail",
        "more detail",
        "all the details"
    ]

    # ============================================================
    # EXERCISE SIGNALS
    # ============================================================

    EXERCISE_SIGNALS = [

        "exercise",
        "problem",
        "question",
        "quiz",
        "test me",
        "practice",
        "practice question",
        "practice problem",
        "give me a question",
        "give me an exercise",
        "solve this",
        "how do i solve"
    ]

    # ============================================================
    # DEFINITION SIGNALS
    # ============================================================

    DEFINITION_SIGNALS = [

        "what is",
        "what are",
        "define",
        "definition of",
        "meaning of",
        "what does",
        "what do"
    ]

    # ============================================================
    # SUBJECT-SPECIFIC STRATEGIES
    # ============================================================

    SUBJECT_STRATEGIES = {

        "physics": [
            "Use real-world physical examples.",
            "Connect formulas to physical meaning.",
            "Explain what each variable represents.",
            "Avoid giving formulas without explaining why they work."
        ],

        "math": [
            "Show the solving method clearly.",
            "Explain why each mathematical step is valid.",
            "Check calculations before giving the final result.",
            "Use a worked example when useful."
        ],

        "biology": [
            "Explain biological processes in logical stages.",
            "Connect structures to their functions.",
            "Use concrete biological examples.",
            "Clearly distinguish related biological terms."
        ],

        "chemistry": [
            "Explain what happens at the particle level.",
            "Connect chemical equations to the actual process.",
            "Define important chemical vocabulary.",
            "Use examples when they clarify the reaction."
        ],

        "history": [
            "Explain events in chronological order when useful.",
            "Connect causes, events and consequences.",
            "Distinguish facts from interpretation.",
            "Use dates only when they help understanding."
        ],

        "geography": [
            "Connect geographic concepts to real locations.",
            "Explain relationships between environment and society.",
            "Use spatial examples when useful.",
            "Distinguish physical and human geography."
        ],

        "computer science": [
            "Explain the underlying logic before unnecessary details.",
            "Use small examples.",
            "Explain code separately from the concept.",
            "Check syntax and logic carefully."
        ],

        "programming": [
            "Explain the programming concept before the implementation.",
            "Use small examples.",
            "Explain code outside code blocks.",
            "Verify syntax and logic."
        ]
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        default_level: str = "beginner"
    ):
        """
        Initialize the adaptive tutor.

        default_level is used when the student profile does not
        contain a valid level.
        """

        self.default_level = (
            self._normalize_level(
                default_level
            )
        )

    # ============================================================
    # LEVEL NORMALIZATION
    # ============================================================

    def _normalize_level(
        self,
        level: Any
    ) -> str:
        """
        Convert arbitrary level input into a supported level.
        """

        if level is None:

            return self.default_level

        if not isinstance(
            level,
            str
        ):

            return self.default_level

        level = (
            level
            .strip()
            .lower()
        )

        aliases = {

            "basic": "beginner",

            "novice": "beginner",

            "starter": "beginner",

            "elementary": "beginner",

            "medium": "intermediate",

            "normal": "intermediate",

            "expert": "advanced",

            "high": "advanced",

            "master": "mastery",

            "expertise": "mastery"
        }

        level = aliases.get(
            level,
            level
        )

        if level not in self.LEVELS:

            return self.default_level

        return level

    # ============================================================
    # CHOOSE PROFILE LEVEL
    # ============================================================

    def choose_level(
        self,
        student: Optional[Dict[str, Any]]
    ) -> str:
        """
        Determine the student's baseline level from the profile.
        """

        if not isinstance(
            student,
            dict
        ):

            return self.default_level

        return self._normalize_level(
            student.get(
                "level",
                self.default_level
            )
        )

    # ============================================================
    # NORMALIZE TEXT
    # ============================================================

    def _normalize_text(
        self,
        text: Any
    ) -> str:
        """
        Normalize text for signal detection.
        """

        if not isinstance(
            text,
            str
        ):

            return ""

        text = (
            text
            .strip()
            .lower()
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # ============================================================
    # SIGNAL DETECTION
    # ============================================================

    def _contains_signal(
        self,
        text: str,
        signals: List[str]
    ) -> bool:
        """
        Check whether text contains one of the configured signals.

        Phrase matching is intentionally simple and deterministic.
        """

        if not text:

            return False

        return any(
            signal in text
            for signal in signals
        )

    # ============================================================
    # SIGNAL SCORE
    # ============================================================

    def _score_signals(
        self,
        text: str,
        signals: List[str]
    ) -> int:
        """
        Count matching signals.

        Multiple signals increase confidence that the student is
        explicitly asking for a particular teaching approach.
        """

        if not text:

            return 0

        return sum(
            1
            for signal in signals
            if signal in text
        )

    # ============================================================
    # EXPLICIT LEVEL REQUEST
    # ============================================================

    def detect_requested_level(
        self,
        message: Optional[str]
    ) -> Optional[str]:
        """
        Detect whether the student's current message explicitly
        requests a particular difficulty level.

        Explicit requests have higher priority than the profile.
        """

        text = self._normalize_text(
            message
        )

        if not text:

            return None

        # Mastery first because it is the most specific.
        if self._contains_signal(
            text,
            self.MASTERY_SIGNALS
        ):

            return "mastery"

        if self._contains_signal(
            text,
            self.ADVANCED_SIGNALS
        ):

            return "advanced"

        if self._contains_signal(
            text,
            self.BEGINNER_SIGNALS
        ):

            return "beginner"

        if self._contains_signal(
            text,
            self.INTERMEDIATE_SIGNALS
        ):

            return "intermediate"

        return None

    # ============================================================
    # CONFUSION DETECTION
    # ============================================================

    def detect_confusion(
        self,
        message: Optional[str]
    ) -> bool:
        """
        Detect explicit evidence that the student is struggling.
        """

        text = self._normalize_text(
            message
        )

        return self._contains_signal(
            text,
            self.CONFUSION_SIGNALS
        )

    # ============================================================
    # UNDERSTANDING DETECTION
    # ============================================================

    def detect_understanding(
        self,
        message: Optional[str]
    ) -> bool:
        """
        Detect explicit evidence that the student understands.
        """

        text = self._normalize_text(
            message
        )

        return self._contains_signal(
            text,
            self.UNDERSTANDING_SIGNALS
        )

    # ============================================================
    # RESPONSE LENGTH
    # ============================================================

    def detect_response_style(
        self,
        message: Optional[str]
    ) -> str:
        """
        Detect whether the student is asking for a concise,
        balanced or detailed response.
        """

        text = self._normalize_text(
            message
        )

        if self._contains_signal(
            text,
            self.CONCISE_SIGNALS
        ):

            return "concise"

        if self._contains_signal(
            text,
            self.DETAIL_SIGNALS
        ):

            return "detailed"

        return "balanced"

    # ============================================================
    # STEP-BY-STEP DETECTION
    # ============================================================

    def needs_step_by_step(
        self,
        message: Optional[str]
    ) -> bool:
        """
        Determine whether the student explicitly wants a
        step-by-step explanation.
        """

        text = self._normalize_text(
            message
        )

        return self._contains_signal(
            text,
            self.STEP_SIGNALS
        )

    # ============================================================
    # EXERCISE DETECTION
    # ============================================================

    def is_practice_request(
        self,
        message: Optional[str]
    ) -> bool:
        """
        Determine whether the student appears to be requesting
        practice or problem-solving help.
        """

        text = self._normalize_text(
            message
        )

        return self._contains_signal(
            text,
            self.EXERCISE_SIGNALS
        )

    # ============================================================
    # DEFINITION DETECTION
    # ============================================================

    def is_definition_request(
        self,
        message: Optional[str]
    ) -> bool:
        """
        Detect simple definition-style questions.
        """

        text = self._normalize_text(
            message
        )

        return self._contains_signal(
            text,
            self.DEFINITION_SIGNALS
        )

    # ============================================================
    # PROFILE CONFIDENCE
    # ============================================================

    def get_subject_confidence(
        self,
        student: Optional[Dict[str, Any]],
        subject: Optional[str]
    ) -> Optional[float]:
        """
        Try to retrieve a subject-specific confidence value from
        the student profile.

        This method is intentionally defensive because different
        versions of Nova may store profile information differently.
        """

        if not isinstance(
            student,
            dict
        ):

            return None

        if not subject:

            return None

        # -------------------------------------
        # Possible direct confidence map
        # -------------------------------------

        confidence_map = student.get(
            "confidence"
        )

        if isinstance(
            confidence_map,
            dict
        ):

            value = confidence_map.get(
                subject
            )

            if isinstance(
                value,
                (int, float)
            ):

                return float(value)

        # -------------------------------------
        # Possible subject progress map
        # -------------------------------------

        progress = student.get(
            "progress"
        )

        if isinstance(
            progress,
            dict
        ):

            subject_data = progress.get(
                subject
            )

            if isinstance(
                subject_data,
                dict
            ):

                value = subject_data.get(
                    "confidence"
                )

                if isinstance(
                    value,
                    (int, float)
                ):

                    return float(value)

        return None

    # ============================================================
    # CLAMP CONFIDENCE
    # ============================================================

    def _normalize_confidence(
        self,
        confidence: Any
    ) -> Optional[float]:
        """
        Normalize confidence to a 0-100 scale.

        Supports both:

            0.0 - 1.0

        and:

            0 - 100
        """

        if confidence is None:

            return None

        if not isinstance(
            confidence,
            (int, float)
        ):

            return None

        confidence = float(
            confidence
        )

        if 0 <= confidence <= 1:

            confidence *= 100

        return max(
            0.0,
            min(
                100.0,
                confidence
            )
        )

    # ============================================================
    # CONFIDENCE ADJUSTMENT
    # ============================================================

    def adjust_level_from_confidence(
        self,
        level: str,
        confidence: Optional[float]
    ) -> str:
        """
        Adjust a baseline level according to demonstrated confidence.

        This does not make massive jumps. A student should not go
        from beginner to mastery because of one lucky answer.
        """

        level = self._normalize_level(
            level
        )

        confidence = self._normalize_confidence(
            confidence
        )

        if confidence is None:

            return level

        current = self.LEVELS[
            level
        ]

        # -------------------------------------
        # Strong evidence of difficulty
        # -------------------------------------

        if confidence < 30:

            current -= 1

        elif confidence < 45:

            current -= 1

        # -------------------------------------
        # Strong evidence of understanding
        # -------------------------------------

        elif confidence >= 90:

            current += 1

        elif confidence >= 75:

            current += 1

        current = max(
            0,
            min(
                3,
                current
            )
        )

        return self.REVERSE_LEVELS[
            current
        ]

    # ============================================================
    # APPLY EXPLICIT OVERRIDE
    # ============================================================

    def apply_explicit_override(
        self,
        base_level: str,
        requested_level: Optional[str]
    ) -> str:
        """
        Apply an explicit request from the student.

        The student's direct request has priority over inferred
        profile information.
        """

        if requested_level is None:

            return base_level

        return self._normalize_level(
            requested_level
        )

    # ============================================================
    # SUBJECT STRATEGY
    # ============================================================

    def get_subject_strategy(
        self,
        subject: Optional[str]
    ) -> List[str]:
        """
        Return teaching strategies for a particular subject.
        """

        if not subject:

            return []

        subject_key = (
            str(subject)
            .strip()
            .lower()
        )

        strategies = (
            self.SUBJECT_STRATEGIES.get(
                subject_key,
                []
            )
        )

        return list(
            strategies
        )

    # ============================================================
    # BUILD LEVEL INSTRUCTION
    # ============================================================

    def _build_level_instruction(
        self,
        level: str
    ) -> str:
        """
        Convert a difficulty level into concrete teaching behavior.
        """

        if level == "beginner":

            return (
                "Start from the basics. "
                "Use simple vocabulary. "
                "Introduce one important idea at a time. "
                "Use concrete examples. "
                "Avoid unnecessary technical terminology."
            )

        if level == "intermediate":

            return (
                "Explain the concept clearly with moderate detail. "
                "Connect related ideas. "
                "Use examples and explain important reasoning. "
                "Introduce technical vocabulary when useful."
            )

        if level == "advanced":

            return (
                "Give a deeper explanation. "
                "Use appropriate technical vocabulary. "
                "Explain theory and important nuances. "
                "Connect the concept to related advanced ideas."
            )

        return (
            "Treat the student as highly competent. "
            "Focus on deeper reasoning, difficult applications, "
            "subtle distinctions and challenging problems. "
            "Avoid unnecessarily reteaching basic material."
        )

    # ============================================================
    # BUILD CONFUSION INSTRUCTION
    # ============================================================

    def _build_confusion_instruction(
        self,
        confused: bool
    ) -> str:
        """
        Return additional instructions when the student is confused.
        """

        if not confused:

            return ""

        return (
            "The student appears confused or is struggling. "
            "Do not simply repeat the previous explanation. "
            "Use a different explanation strategy, simplify "
            "the concept, isolate the difficult part, and "
            "use a concrete example or analogy if useful."
        )

    # ============================================================
    # BUILD UNDERSTANDING INSTRUCTION
    # ============================================================

    def _build_understanding_instruction(
        self,
        understands: bool
    ) -> str:
        """
        Return instructions when the student demonstrates
        understanding.
        """

        if not understands:

            return ""

        return (
            "The student indicates that the concept is understood. "
            "Avoid unnecessarily reteaching the basics. "
            "If appropriate, add a slightly deeper connection "
            "or a small challenge."
        )

    # ============================================================
    # BUILD RESPONSE INSTRUCTION
    # ============================================================

    def _build_response_instruction(
        self,
        response_style: str
    ) -> str:
        """
        Build response-length guidance.
        """

        if response_style == "concise":

            return (
                "Keep the response concise and focused. "
                "Do not add unnecessary teaching material."
            )

        if response_style == "detailed":

            return (
                "Provide a detailed explanation with enough "
                "reasoning and examples to teach the concept properly."
            )

        return (
            "Use a balanced response length appropriate to "
            "the complexity of the question."
        )

    # ============================================================
    # BUILD PRACTICE INSTRUCTION
    # ============================================================

    def _build_practice_instruction(
        self,
        practice: bool
    ) -> str:
        """
        Build instructions for practice requests.
        """

        if not practice:

            return ""

        return (
            "The student appears to be working on a problem "
            "or practice task. Focus on the solving process. "
            "Do not skip important reasoning."
        )

    # ============================================================
    # BUILD STEP INSTRUCTION
    # ============================================================

    def _build_step_instruction(
        self,
        step_by_step: bool
    ) -> str:
        """
        Build step-by-step instructions.
        """

        if not step_by_step:

            return ""

        return (
            "The student requested a step-by-step approach. "
            "Present the reasoning in a clear logical sequence "
            "and do not skip essential steps."
        )

    # ============================================================
    # MAIN DECISION
    # ============================================================

    def decide(
        self,
        student: Optional[Dict[str, Any]],
        subject: Optional[str] = None,
        message: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Produce a complete adaptive teaching decision.

        This is the main intelligence layer of AdaptiveTutor.

        Returns a structured dictionary so future Nova components
        can use individual decisions rather than parsing one giant
        string.
        """

        if not isinstance(
            student,
            dict
        ):

            student = {}

        text = self._normalize_text(
            message
        )

        # -------------------------------------
        # Baseline
        # -------------------------------------

        profile_level = self.choose_level(
            student
        )

        # -------------------------------------
        # Confidence
        # -------------------------------------

        if confidence is None:

            confidence = (
                self.get_subject_confidence(
                    student,
                    subject
                )
            )

        confidence = self._normalize_confidence(
            confidence
        )

        # -------------------------------------
        # Profile-based adjustment
        # -------------------------------------

        inferred_level = (
            self.adjust_level_from_confidence(
                profile_level,
                confidence
            )
        )

        # -------------------------------------
        # Message signals
        # -------------------------------------

        requested_level = (
            self.detect_requested_level(
                text
            )
        )

        confused = (
            self.detect_confusion(
                text
            )
        )

        understands = (
            self.detect_understanding(
                text
            )
        )

        response_style = (
            self.detect_response_style(
                text
            )
        )

        step_by_step = (
            self.needs_step_by_step(
                text
            )
        )

        practice = (
            self.is_practice_request(
                text
            )
        )

        definition = (
            self.is_definition_request(
                text
            )
        )

        # -------------------------------------
        # Final level
        # -------------------------------------

        final_level = self.apply_explicit_override(
            inferred_level,
            requested_level
        )

        # -------------------------------------
        # Confusion gets strong priority
        # -------------------------------------

        if confused and requested_level is None:

            current_level = self.LEVELS[
                final_level
            ]

            final_level = self.REVERSE_LEVELS[
                max(
                    0,
                    current_level - 1
                )
            ]

        # -------------------------------------
        # Understanding can justify challenge
        # -------------------------------------

        if (
            understands
            and
            requested_level is None
            and
            confidence is not None
            and
            confidence >= 80
        ):

            current_level = self.LEVELS[
                final_level
            ]

            final_level = self.REVERSE_LEVELS[
                min(
                    3,
                    current_level + 1
                )
            ]

        # -------------------------------------
        # Build instructions
        # -------------------------------------

        instructions = []

        instructions.append(
            self._build_level_instruction(
                final_level
            )
        )

        confusion_instruction = (
            self._build_confusion_instruction(
                confused
            )
        )

        if confusion_instruction:

            instructions.append(
                confusion_instruction
            )

        understanding_instruction = (
            self._build_understanding_instruction(
                understands
            )
        )

        if understanding_instruction:

            instructions.append(
                understanding_instruction
            )

        response_instruction = (
            self._build_response_instruction(
                response_style
            )
        )

        instructions.append(
            response_instruction
        )

        practice_instruction = (
            self._build_practice_instruction(
                practice
            )
        )

        if practice_instruction:

            instructions.append(
                practice_instruction
            )

        step_instruction = (
            self._build_step_instruction(
                step_by_step
            )
        )

        if step_instruction:

            instructions.append(
                step_instruction
            )

        # -------------------------------------
        # Definition requests
        # -------------------------------------

        if definition:

            instructions.append(
                "The student appears to want a definition. "
                "Start with a direct definition before expanding."
            )

        # -------------------------------------
        # Subject-specific behavior
        # -------------------------------------

        subject_strategy = (
            self.get_subject_strategy(
                subject
            )
        )

        instructions.extend(
            subject_strategy
        )

        # -------------------------------------
        # Mastery
        # -------------------------------------

        if final_level == "mastery":

            instructions.append(
                "If appropriate, challenge the student with "
                "a difficult application or reasoning question."
            )

        # -------------------------------------
        # Deduplicate instructions
        # -------------------------------------

        cleaned_instructions = []

        seen = set()

        for instruction in instructions:

            instruction = (
                instruction
                .strip()
            )

            if not instruction:

                continue

            key = instruction.lower()

            if key in seen:

                continue

            seen.add(
                key
            )

            cleaned_instructions.append(
                instruction
            )

        # -------------------------------------
        # Final strategy text
        # -------------------------------------

        instruction_text = " ".join(
            cleaned_instructions
        )

        return {

            "level":
                final_level,

            "profile_level":
                profile_level,

            "inferred_level":
                inferred_level,

            "requested_level":
                requested_level,

            "confidence":
                confidence,

            "confused":
                confused,

            "understands":
                understands,

            "response_style":
                response_style,

            "step_by_step":
                step_by_step,

            "practice":
                practice,

            "definition":
                definition,

            "subject":
                subject,

            "subject_strategy":
                subject_strategy,

            "instructions":
                cleaned_instructions,

            "instruction":
                instruction_text
        }

    # ============================================================
    # COMPATIBILITY METHOD
    # ============================================================

    def build_instruction(
        self,
        student: Optional[Dict[str, Any]],
        subject: Optional[str],
        message: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> str:
        """
        Backwards-compatible public method.

        Existing TutorEngine code can continue calling:

            build_instruction(...)

        while internally using the more advanced decision engine.
        """

        decision = self.decide(

            student=student,

            subject=subject,

            message=message,

            confidence=confidence
        )

        return decision[
            "instruction"
        ]

    # ============================================================
    # SIMPLE LEVEL API
    # ============================================================

    def get_level(
        self,
        student: Optional[Dict[str, Any]],
        message: Optional[str] = None,
        subject: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> str:
        """
        Convenience method returning only the final teaching level.
        """

        decision = self.decide(

            student=student,

            subject=subject,

            message=message,

            confidence=confidence
        )

        return decision[
            "level"
        ]

    # ============================================================
    # DEBUG INFORMATION
    # ============================================================

    def explain_decision(
        self,
        student: Optional[Dict[str, Any]],
        subject: Optional[str] = None,
        message: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Return the complete adaptive decision.

        Useful when testing Nova from the terminal.
        """

        return self.decide(

            student=student,

            subject=subject,

            message=message,

            confidence=confidence
        )

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(
        self
    ) -> str:

        return (
            "AdaptiveTutor("
            f"default_level='{self.default_level}'"
            ")"
        )