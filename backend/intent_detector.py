"""
Nova AI - Intent Detector
=========================

Fast, deterministic request classification for Nova.

Design goals:
    - No LLM calls
    - No embeddings
    - No memory access
    - Very low latency
    - Regex/token based matching
    - Conservative classification
    - Rich analysis for NovaPipeline
    - Backward compatibility with detect()
    - Explicit command support
    - Confidence scoring
    - Routing hints for expensive components

The IntentDetector is a classifier, not an orchestrator.

NovaPipeline decides what to do with the classification.
IntentDetector decides what the user is asking for.
"""

from __future__ import annotations

import re

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


# ============================================================
# VERSION
# ============================================================

INTENT_DETECTOR_VERSION = "2.0.0"


# ============================================================
# INTENTS
# ============================================================

INTENT_GREETING = "greeting"
INTENT_THANKS = "thanks"
INTENT_FAREWELL = "farewell"

INTENT_QUIZ = "quiz"
INTENT_SUMMARY = "summary"
INTENT_EXPLANATION = "explanation"
INTENT_TRANSLATION = "translation"

INTENT_HOMEWORK = "homework"
INTENT_CORRECTION = "correction"
INTENT_PRACTICE = "practice"
INTENT_PROBLEM_SOLVING = "problem_solving"
INTENT_DEFINITION = "definition"
INTENT_STUDY = "study"

INTENT_CONVERSATION = "conversation"
INTENT_GENERAL = "general"
INTENT_INVALID = "invalid"


# ============================================================
# INTENT GROUPS
# ============================================================

LEARNING_INTENTS = {
    INTENT_QUIZ,
    INTENT_SUMMARY,
    INTENT_EXPLANATION,
    INTENT_TRANSLATION,
    INTENT_HOMEWORK,
    INTENT_CORRECTION,
    INTENT_PRACTICE,
    INTENT_PROBLEM_SOLVING,
    INTENT_DEFINITION,
    INTENT_STUDY,
}

LIGHTWEIGHT_INTENTS = {
    INTENT_GREETING,
    INTENT_THANKS,
    INTENT_FAREWELL,
}

MEMORY_RELEVANT_INTENTS = {
    INTENT_EXPLANATION,
    INTENT_HOMEWORK,
    INTENT_CORRECTION,
    INTENT_PRACTICE,
    INTENT_PROBLEM_SOLVING,
    INTENT_STUDY,
    INTENT_QUIZ,
}

LLM_REQUIRED_INTENTS = {
    INTENT_EXPLANATION,
    INTENT_TRANSLATION,
    INTENT_HOMEWORK,
    INTENT_CORRECTION,
    INTENT_PRACTICE,
    INTENT_PROBLEM_SOLVING,
    INTENT_DEFINITION,
    INTENT_STUDY,
    INTENT_SUMMARY,
    INTENT_QUIZ,
}


# ============================================================
# REGEX HELPERS
# ============================================================

def _compile_patterns(
    patterns: Iterable[str],
) -> Tuple[re.Pattern[str], ...]:

    return tuple(
        re.compile(
            pattern,
            re.IGNORECASE,
        )
        for pattern in patterns
    )


def _matches_any(
    text: str,
    patterns: Iterable[re.Pattern[str]],
) -> bool:

    return any(
        pattern.search(text)
        for pattern in patterns
    )


# ============================================================
# COMPILED PATTERNS
# ============================================================

GREETING_PATTERNS = _compile_patterns(
    (
        r"^\s*(?:hi|hello|hey|hiya|howdy|yo)\s*[!.?,]*\s*$",
        r"^\s*(?:hi|hello|hey)\s+(?:nova|there)\s*[!.?,]*\s*$",
        r"^\s*good\s+(?:morning|afternoon|evening)\s*[!.?,]*\s*$",
        r"^\s*salut\s*[!.?,]*\s*$",
        r"^\s*bonjour\s*[!.?,]*\s*$",
        r"^\s*coucou\s*[!.?,]*\s*$",
    )
)


THANKS_PATTERNS = _compile_patterns(
    (
        r"^\s*(?:thanks|thank\s+you|thx|ty)\s*[!.?,]*\s*$",
        r"^\s*(?:thanks|thank\s+you)\s+(?:nova|so much)\s*[!.?,]*\s*$",
        r"^\s*(?:merci|merci\s+beaucoup)\s*[!.?,]*\s*$",
    )
)


FAREWELL_PATTERNS = _compile_patterns(
    (
        r"^\s*(?:bye|goodbye|see\s+you|see\s+ya)\s*[!.?,]*\s*$",
        r"^\s*good\s+night\s*[!.?,]*\s*$",
        r"^\s*(?:au\s+revoir|bonne\s+nuit)\s*[!.?,]*\s*$",
    )
)


QUIZ_PATTERNS = _compile_patterns(
    (
        r"\bquiz\b",
        r"\btest\s+me\b",
        r"\bquestion\s+me\b",
        r"\bmultiple[\s-]?choice\b",
        r"\bmcq\b",
        r"\bqcm\b",
        r"\bmake\s+me\s+a\s+test\b",
        r"\bgive\s+me\s+(?:a\s+)?quiz\b",
        r"\bask\s+me\s+questions\b",
    )
)


SUMMARY_PATTERNS = _compile_patterns(
    (
        r"\bsummar(?:y|ize|ise|izing|ising)\b",
        r"\bshorten\s+(?:this|it|the)\b",
        r"\bkey\s+points?\b",
        r"\bmain\s+(?:ideas|points)\b",
        r"\bin\s+short\b",
        r"\bgive\s+me\s+the\s+essentials\b",
    )
)


EXPLANATION_PATTERNS = _compile_patterns(
    (
        r"\bexplain\b",
        r"\bteach\s+me\b",
        r"\bhow\s+does\b",
        r"\bhow\s+do\b",
        r"\bwhy\s+does\b",
        r"\bwhy\s+do\b",
        r"\bcan\s+you\s+explain\b",
        r"\bi\s+don'?t\s+understand\b",
        r"\bi\s+do\s+not\s+understand\b",
        r"\bhelp\s+me\s+understand\b",
        r"\bwalk\s+me\s+through\b",
    )
)


TRANSLATION_PATTERNS = _compile_patterns(
    (
        r"\btranslate\b",
        r"\btranslation\b",
        r"\bin\s+(?:english|french|spanish|german|italian)\b",
        r"\bhow\s+do\s+you\s+say\b",
        r"\bhow\s+do\s+i\s+say\b",
        r"\bwhat\s+does\s+.+\s+mean\s+in\b",
    )
)


HOMEWORK_PATTERNS = _compile_patterns(
    (
        r"\bhomework\b",
        r"\bhome\s+work\b",
        r"\bhomework\s+assignment\b",
        r"\bassignment\b",
        r"\bexercise\s+(?:number|n°|no\.?)?\s*\d+\b",
        r"\bexercise\b",
        r"\bexercice\b",
        r"\bdevoir\b",
        r"\bdevoirs\b",
        r"\bworksheet\b",
    )
)


CORRECTION_PATTERNS = _compile_patterns(
    (
        r"\bcorrect\s+(?:this|my|the)\b",
        r"\bcorrect(?:ion)?\b",
        r"\bcheck\s+(?:this|my|the)\b",
        r"\bcheck\s+my\s+answer\b",
        r"\bwhat\s+did\s+i\s+do\s+wrong\b",
        r"\bwhere\s+did\s+i\s+go\s+wrong\b",
        r"\bmy\s+mistake\b",
        r"\bmistakes?\b",
        r"\berror\b",
        r"\berreurs?\b",
        r"\bcorrige\b",
        r"\bcorriger\b",
    )
)


PRACTICE_PATTERNS = _compile_patterns(
    (
        r"\bpractice\b",
        r"\bpractise\b",
        r"\bpractice\s+problems?\b",
        r"\bpractice\s+exercises?\b",
        r"\bgive\s+me\s+exercises?\b",
        r"\bgive\s+me\s+problems?\b",
        r"\bmore\s+exercises?\b",
        r"\btrain\s+me\b",
        r"\bentrain(?:e|ement)\b",
    )
)


PROBLEM_SOLVING_PATTERNS = _compile_patterns(
    (
        r"\bsolve\b",
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\bfind\s+(?:the|x|y)\b",
        r"\bwork\s+out\b",
        r"\bhow\s+much\s+is\b",
        r"\bwhat\s+is\s+the\s+value\b",
        r"\bresolve\b",
        r"\brésous\b",
        r"\bcalcul(?:e|er)\b",
    )
)


DEFINITION_PATTERNS = _compile_patterns(
    (
        r"\bwhat\s+is\b",
        r"\bwhat\s+are\b",
        r"\bwhat\s+does\b",
        r"\bdefine\b",
        r"\bdefinition\b",
        r"\bmeaning\s+of\b",
        r"\bdefinition\s+de\b",
        r"\bqu'?est[-\s]ce\s+que\b",
        r"\bque\s+signifie\b",
    )
)


STUDY_PATTERNS = _compile_patterns(
    (
        r"\bstudy\b",
        r"\brevise\b",
        r"\brevision\b",
        r"\breview\b",
        r"\bprepare\s+for\b",
        r"\bprepare\s+me\s+for\b",
        r"\bexam\b",
        r"\btest\b",
        r"\bbac\b",
        r"\brevis(?:e|ing|ion)\b",
        r"\brévis(?:e|er|ion)\b",
    )
)


QUESTION_PATTERNS = _compile_patterns(
    (
        r"\?$",
        r"^\s*(?:what|why|how|when|where|who|which|can|could|would|is|are|do|does|did|should|will)\b",
        r"^\s*(?:est|sont|pourquoi|comment|quand|où|qui|quel|quelle|peux|puis)\b",
    )
)


EXPLICIT_COMMAND_PATTERN = re.compile(
    r"^\s*/([a-zA-Z][a-zA-Z0-9_-]*)"
    r"(?:\s+(.*))?$",
    re.IGNORECASE,
)


# ============================================================
# COMMAND MAP
# ============================================================

COMMAND_MAP = {
    "quiz": INTENT_QUIZ,
    "test": INTENT_QUIZ,
    "qcm": INTENT_QUIZ,

    "summary": INTENT_SUMMARY,
    "summarize": INTENT_SUMMARY,
    "summarise": INTENT_SUMMARY,
    "resume": INTENT_SUMMARY,

    "explain": INTENT_EXPLANATION,
    "teach": INTENT_EXPLANATION,

    "translate": INTENT_TRANSLATION,

    "homework": INTENT_HOMEWORK,
    "exercise": INTENT_HOMEWORK,

    "correct": INTENT_CORRECTION,
    "correction": INTENT_CORRECTION,

    "practice": INTENT_PRACTICE,

    "solve": INTENT_PROBLEM_SOLVING,

    "study": INTENT_STUDY,
}


# ============================================================
# INTENT RESULT
# ============================================================

@dataclass
class IntentResult:
    """
    Structured classification result.

    This object can be converted into a dictionary and is designed
    to be consumed directly by NovaPipeline.
    """

    intent: str

    confidence: float

    signals: List[str] = field(
        default_factory=list
    )

    lightweight: bool = False

    needs_memory: bool = False

    needs_learning_context: bool = False

    needs_llm: bool = True

    kind: str = "general"

    explicit_command: Optional[str] = None

    normalized_message: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:

        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "signals": list(self.signals),
            "lightweight": self.lightweight,
            "needs_memory": self.needs_memory,
            "needs_learning_context": (
                self.needs_learning_context
            ),
            "needs_llm": self.needs_llm,
            "kind": self.kind,
            "explicit_command": (
                self.explicit_command
            ),
            "normalized_message": (
                self.normalized_message
            ),
            "metadata": dict(self.metadata),
        }


# ============================================================
# DETECTOR
# ============================================================

class IntentDetector:
    """
    Fast deterministic intent detector for Nova.

    No model is loaded.

    No memory is accessed.

    No network operation is performed.

    Classification is based on compiled regular expressions and
    lightweight scoring.
    """

    VERSION = INTENT_DETECTOR_VERSION

    def __init__(
        self,
        *,
        minimum_confidence: float = 0.45,
    ):

        try:
            minimum_confidence = float(
                minimum_confidence
            )
        except (TypeError, ValueError):
            minimum_confidence = 0.45

        self.minimum_confidence = max(
            0.0,
            min(
                1.0,
                minimum_confidence
            )
        )

        self.calls = 0

        self.intent_counts: Dict[str, int] = {}

        self.last_result: Optional[
            IntentResult
        ] = None

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def normalize(
        message: Any,
    ) -> str:

        if message is None:
            return ""

        text = str(message)

        text = text.replace(
            "\u00a0",
            " ",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ========================================================
    # COMMANDS
    # ========================================================

    @staticmethod
    def parse_command(
        text: str,
    ) -> Tuple[
        Optional[str],
        str,
    ]:

        match = EXPLICIT_COMMAND_PATTERN.match(
            text
        )

        if not match:
            return None, text

        command = (
            match.group(1)
            .strip()
            .casefold()
        )

        remainder = (
            match.group(2)
            or ""
        ).strip()

        return command, remainder

    # ========================================================
    # PATTERN MATCHING
    # ========================================================

    @staticmethod
    def _matched_signals(
        text: str,
        patterns: Mapping[
            str,
            Iterable[re.Pattern[str]],
        ],
    ) -> List[str]:

        signals = []

        for name, compiled in patterns.items():

            if _matches_any(
                text,
                compiled,
            ):
                signals.append(name)

        return signals

    # ========================================================
    # SPECIAL CASES
    # ========================================================

    @staticmethod
    def _is_greeting(
        text: str,
    ) -> bool:

        return _matches_any(
            text,
            GREETING_PATTERNS,
        )

    @staticmethod
    def _is_thanks(
        text: str,
    ) -> bool:

        return _matches_any(
            text,
            THANKS_PATTERNS,
        )

    @staticmethod
    def _is_farewell(
        text: str,
    ) -> bool:

        return _matches_any(
            text,
            FAREWELL_PATTERNS,
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _confidence(
        score: float,
        *,
        question: bool = False,
        explicit: bool = False,
    ) -> float:

        confidence = score

        if question:
            confidence += 0.05

        if explicit:
            confidence += 0.25

        return max(
            0.0,
            min(
                0.99,
                confidence,
            )
        )

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        message: Any,
    ) -> Dict[str, Any]:

        self.calls += 1

        text = self.normalize(
            message
        )

        if not text:

            result = IntentResult(
                intent=INTENT_INVALID,
                confidence=1.0,
                lightweight=False,
                needs_memory=False,
                needs_learning_context=False,
                needs_llm=False,
                kind="invalid",
                normalized_message="",
            )

            self._record(result)

            return result.to_dict()

        command, command_text = (
            self.parse_command(text)
        )

        # ----------------------------------------------------
        # EXPLICIT COMMAND
        # ----------------------------------------------------

        if command in COMMAND_MAP:

            intent = COMMAND_MAP[
                command
            ]

            result = self._build_result(
                intent=intent,
                confidence=self._confidence(
                    0.95,
                    explicit=True,
                ),
                signals=[
                    "explicit_command",
                    command,
                ],
                text=command_text or text,
                explicit_command=command,
            )

            self._record(result)

            return result.to_dict()

        # ----------------------------------------------------
        # LIGHTWEIGHT REQUESTS
        # ----------------------------------------------------

        if self._is_greeting(text):

            result = self._build_result(
                intent=INTENT_GREETING,
                confidence=0.99,
                signals=["exact_greeting"],
                text=text,
            )

            self._record(result)

            return result.to_dict()

        if self._is_thanks(text):

            result = self._build_result(
                intent=INTENT_THANKS,
                confidence=0.99,
                signals=["exact_thanks"],
                text=text,
            )

            self._record(result)

            return result.to_dict()

        if self._is_farewell(text):

            result = self._build_result(
                intent=INTENT_FAREWELL,
                confidence=0.99,
                signals=["exact_farewell"],
                text=text,
            )

            self._record(result)

            return result.to_dict()

        # ----------------------------------------------------
        # LEARNING SIGNALS
        # ----------------------------------------------------

        patterns = {
            INTENT_QUIZ: QUIZ_PATTERNS,
            INTENT_SUMMARY: SUMMARY_PATTERNS,
            INTENT_EXPLANATION: EXPLANATION_PATTERNS,
            INTENT_TRANSLATION: TRANSLATION_PATTERNS,
            INTENT_HOMEWORK: HOMEWORK_PATTERNS,
            INTENT_CORRECTION: CORRECTION_PATTERNS,
            INTENT_PRACTICE: PRACTICE_PATTERNS,
            INTENT_PROBLEM_SOLVING: (
                PROBLEM_SOLVING_PATTERNS
            ),
            INTENT_DEFINITION: DEFINITION_PATTERNS,
            INTENT_STUDY: STUDY_PATTERNS,
        }

        matches = self._matched_signals(
            text,
            patterns,
        )

        has_question = _matches_any(
            text,
            QUESTION_PATTERNS,
        )

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        scores: Dict[str, float] = {}

        for intent in matches:

            # Base score for a direct semantic signal.
            scores[intent] = (
                scores.get(
                    intent,
                    0.0,
                )
                + 0.70
            )

        # Stronger signals receive additional weight.
        if INTENT_QUIZ in matches:
            scores[INTENT_QUIZ] += 0.15

        if INTENT_TRANSLATION in matches:
            scores[INTENT_TRANSLATION] += 0.15

        if INTENT_CORRECTION in matches:
            scores[INTENT_CORRECTION] += 0.10

        if INTENT_PROBLEM_SOLVING in matches:
            scores[INTENT_PROBLEM_SOLVING] += 0.10

        if INTENT_DEFINITION in matches:
            scores[INTENT_DEFINITION] += 0.08

        if INTENT_EXPLANATION in matches:
            scores[INTENT_EXPLANATION] += 0.08

        # Question marks strengthen learning/question intents.
        if has_question:

            for intent in (
                INTENT_DEFINITION,
                INTENT_EXPLANATION,
                INTENT_PROBLEM_SOLVING,
            ):

                if intent in scores:
                    scores[intent] += 0.05

        # ----------------------------------------------------
        # CHOOSE BEST INTENT
        # ----------------------------------------------------

        if scores:

            best_intent = max(
                scores,
                key=scores.get,
            )

            best_score = scores[
                best_intent
            ]

            confidence = self._confidence(
                min(
                    best_score,
                    0.90,
                ),
                question=has_question,
            )

            matched_signals = [
                name
                for name in matches
                if name == best_intent
            ]

            if has_question:
                matched_signals.append(
                    "question"
                )

            result = self._build_result(
                intent=best_intent,
                confidence=confidence,
                signals=matched_signals,
                text=text,
            )

            self._record(result)

            return result.to_dict()

        # ----------------------------------------------------
        # GENERIC QUESTION
        # ----------------------------------------------------

        if has_question:

            result = self._build_result(
                intent=INTENT_GENERAL,
                confidence=0.65,
                signals=["question"],
                text=text,
            )

            self._record(result)

            return result.to_dict()

        # ----------------------------------------------------
        # GENERAL CONVERSATION
        # ----------------------------------------------------

        result = self._build_result(
            intent=INTENT_CONVERSATION,
            confidence=0.60,
            signals=[],
            text=text,
        )

        self._record(result)

        return result.to_dict()

    # ========================================================
    # RESULT BUILDER
    # ========================================================

    def _build_result(
        self,
        *,
        intent: str,
        confidence: float,
        signals: List[str],
        text: str,
        explicit_command: Optional[str] = None,
    ) -> IntentResult:

        lightweight = (
            intent in LIGHTWEIGHT_INTENTS
        )

        needs_memory = (
            intent in MEMORY_RELEVANT_INTENTS
        )

        needs_learning_context = (
            intent in LEARNING_INTENTS
        )

        needs_llm = (
            intent in LLM_REQUIRED_INTENTS
        )

        if intent in {
            INTENT_GENERAL,
            INTENT_CONVERSATION,
        }:
            needs_llm = True

        if intent in LIGHTWEIGHT_INTENTS:
            needs_llm = False

        if intent == INTENT_INVALID:
            needs_llm = False

        if intent in LEARNING_INTENTS:
            kind = "learning"

        elif intent in LIGHTWEIGHT_INTENTS:
            kind = "casual"

        elif intent == INTENT_INVALID:
            kind = "invalid"

        else:
            kind = "general"

        return IntentResult(
            intent=intent,
            confidence=max(
                0.0,
                min(
                    0.99,
                    float(confidence),
                )
            ),
            signals=list(
                dict.fromkeys(
                    signals
                )
            ),
            lightweight=lightweight,
            needs_memory=needs_memory,
            needs_learning_context=(
                needs_learning_context
            ),
            needs_llm=needs_llm,
            kind=kind,
            explicit_command=explicit_command,
            normalized_message=text,
            metadata={
                "detector_version": self.VERSION,
            },
        )

    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================

    def detect(
        self,
        message: Any,
    ) -> str:
        """
        Backward-compatible API.

        Existing NovaCore code can continue using:

            intent = detector.detect(message)

        and receives a simple string.
        """

        result = self.analyze(
            message
        )

        return str(
            result.get(
                "intent",
                INTENT_GENERAL,
            )
        )

    # ========================================================
    # FAST ROUTING HELPERS
    # ========================================================

    def is_lightweight(
        self,
        message: Any,
    ) -> bool:

        result = self.analyze(
            message
        )

        return bool(
            result.get(
                "lightweight",
                False,
            )
        )

    def needs_memory(
        self,
        message: Any,
    ) -> bool:

        result = self.analyze(
            message
        )

        return bool(
            result.get(
                "needs_memory",
                False,
            )
        )

    def needs_llm(
        self,
        message: Any,
    ) -> bool:

        result = self.analyze(
            message
        )

        return bool(
            result.get(
                "needs_llm",
                True,
            )
        )

    def is_learning_request(
        self,
        message: Any,
    ) -> bool:

        result = self.analyze(
            message
        )

        return bool(
            result.get(
                "needs_learning_context",
                False,
            )
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    def _record(
        self,
        result: IntentResult,
    ) -> None:

        self.last_result = result

        intent = result.intent

        self.intent_counts[
            intent
        ] = (
            self.intent_counts.get(
                intent,
                0,
            )
            + 1
        )

    def diagnostics(
        self,
    ) -> Dict[str, Any]:

        return {
            "name": "IntentDetector",
            "version": self.VERSION,
            "calls": self.calls,
            "intent_counts": dict(
                self.intent_counts
            ),
            "last_intent": (
                self.last_result.intent
                if self.last_result
                else None
            ),
            "last_confidence": (
                self.last_result.confidence
                if self.last_result
                else None
            ),
        }

    def health(
        self,
    ) -> Dict[str, Any]:

        return {
            "name": "IntentDetector",
            "version": self.VERSION,
            "healthy": True,
            "calls": self.calls,
            "supported_intents": sorted(
                set(
                    LEARNING_INTENTS
                )
                | LIGHTWEIGHT_INTENTS
                | {
                    INTENT_GENERAL,
                    INTENT_CONVERSATION,
                    INTENT_INVALID,
                }
            ),
        }


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "INTENT_DETECTOR_VERSION",

    "INTENT_GREETING",
    "INTENT_THANKS",
    "INTENT_FAREWELL",
    "INTENT_QUIZ",
    "INTENT_SUMMARY",
    "INTENT_EXPLANATION",
    "INTENT_TRANSLATION",
    "INTENT_HOMEWORK",
    "INTENT_CORRECTION",
    "INTENT_PRACTICE",
    "INTENT_PROBLEM_SOLVING",
    "INTENT_DEFINITION",
    "INTENT_STUDY",
    "INTENT_CONVERSATION",
    "INTENT_GENERAL",
    "INTENT_INVALID",

    "LEARNING_INTENTS",
    "LIGHTWEIGHT_INTENTS",
    "MEMORY_RELEVANT_INTENTS",
    "LLM_REQUIRED_INTENTS",

    "IntentResult",
    "IntentDetector",
]