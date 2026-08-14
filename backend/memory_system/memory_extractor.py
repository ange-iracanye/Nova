import re


class MemoryExtractor:

    def __init__(self):

        self.preference_patterns = [

            r"\bi prefer (.+)",

            r"\bi like (.+)",

            r"\bi don't like (.+)",

            r"\bi hate (.+)",

            r"\bi want (.+)",

            r"\bi need (.+)",

            r"\bmy goal is (.+)",

            r"\bi'm planning to (.+)",

            r"\bi am planning to (.+)",

            r"\bi'm trying to (.+)",

            r"\bi am trying to (.+)",

            r"\bi usually (.+)",

            r"\bi always (.+)",

            r"\bi never (.+)"
        ]

        self.fact_patterns = [

            r"\bmy name is (.+)",

            r"\bi am (.+) years old",

            r"\bi'm (.+) years old",

            r"\bi study (.+)",

            r"\bi'm studying (.+)",

            r"\bi am studying (.+)",

            r"\bi live in (.+)",

            r"\bi use (.+)",

            r"\bi have (.+)"
        ]

    # =====================================
    # CLEAN VALUE
    # =====================================

    def _clean_value(
        self,
        value
    ):

        if value is None:
            return ""

        value = str(
            value
        ).strip()

        # Remove repeated whitespace.
        value = re.sub(
            r"\s+",
            " ",
            value
        )

        # Remove sentence punctuation at
        # the end of the extracted memory.
        value = value.rstrip(
            " \t\r\n.!?,;:"
        )

        return value.strip()

    # =====================================
    # EXTRACT
    # =====================================

    def extract(
        self,
        text,
        subject=None,
        conversation_id=None
    ):

        if not text:
            return []

        memories = []

        # =====================================
        # SPLIT INTO SENTENCES
        # =====================================

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text.strip()
        )

        # =====================================
        # HELPERS
        # =====================================

        def add_memory(
            memory_type,
            value,
            importance,
            confidence
        ):

            value = self._clean_value(
                value
            )

            if not value:
                return

            if len(value) < 2:
                return

            memories.append({

                "type":
                    memory_type,

                "text":
                    value,

                "subject":
                    subject,

                "conversation_id":
                    conversation_id,

                "importance":
                    importance,

                "confidence":
                    confidence
            })

        # =====================================
        # PROCESS SENTENCES
        # =====================================

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            # ---------------------------------
            # EXPLICIT MEMORY
            # ---------------------------------

            match = re.search(

                r"^\s*(?:remember that|remember this|"
                r"don't forget that|keep in mind that)\s+(.+?)"
                r"\s*$",

                sentence,

                flags=re.IGNORECASE
            )

            if match:

                add_memory(
                    "explicit_memory",
                    match.group(1),
                    1.0,
                    1.0
                )

                continue

            # ---------------------------------
            # GOAL
            # ---------------------------------

            match = re.search(

                r"^\s*my goal is\s+(?:to\s+)?(.+?)\s*$",

                sentence,

                flags=re.IGNORECASE
            )

            if match:

                add_memory(
                    "goal",
                    match.group(1),
                    0.90,
                    0.90
                )

                continue

            match = re.search(

                r"^\s*i(?:'m| am)?\s+planning to\s+(.+?)\s*$",

                sentence,

                flags=re.IGNORECASE
            )

            if match:

                add_memory(
                    "goal",
                    match.group(1),
                    0.85,
                    0.85
                )

                continue

            # ---------------------------------
            # TRYING TO
            # ---------------------------------

            match = re.search(

                r"^\s*i(?:'m| am)\s+trying to\s+(.+?)\s*$",

                sentence,

                flags=re.IGNORECASE
            )

            if match:

                add_memory(
                    "goal",
                    match.group(1),
                    0.80,
                    0.80
                )

                continue

            # ---------------------------------
            # PREFERENCES
            # ---------------------------------

            preference_patterns = [

                r"^\s*i prefer\s+(.+?)\s*$",

                r"^\s*i like\s+(.+?)\s*$",

                r"^\s*i don't like\s+(.+?)\s*$",

                r"^\s*i hate\s+(.+?)\s*$",

                r"^\s*i want\s+(.+?)\s*$",

                r"^\s*i need\s+(.+?)\s*$",

                r"^\s*i usually\s+(.+?)\s*$",

                r"^\s*i always\s+(.+?)\s*$",

                r"^\s*i never\s+(.+?)\s*$"
            ]

            matched = False

            for pattern in preference_patterns:

                match = re.search(

                    pattern,

                    sentence,

                    flags=re.IGNORECASE
                )

                if match:

                    add_memory(
                        "preference",
                        match.group(1),
                        0.75,
                        0.85
                    )

                    matched = True

                    break

            if matched:
                continue

            # ---------------------------------
            # FACTS
            # ---------------------------------

            fact_patterns = [

                (
                    r"^\s*my name is\s+(.+?)\s*$",
                    "fact"
                ),

                (
                    r"^\s*i am\s+(\d+)\s+years old\s*$",
                    "fact"
                ),

                (
                    r"^\s*i'm\s+(\d+)\s+years old\s*$",
                    "fact"
                ),

                (
                    r"^\s*i study\s+(.+?)\s*$",
                    "fact"
                ),

                (
                    r"^\s*i'm studying\s+(.+?)\s*$",
                    "fact"
                ),

                (
                    r"^\s*i am studying\s+(.+?)\s*$",
                    "fact"
                ),

                (
                    r"^\s*i live in\s+(.+?)\s*$",
                    "fact"
                ),

                (
                    r"^\s*i use\s+(.+?)\s*$",
                    "fact"
                ),

                (
                    r"^\s*i have\s+(.+?)\s*$",
                    "fact"
                )
            ]

            for pattern, memory_type in fact_patterns:

                match = re.search(

                    pattern,

                    sentence,

                    flags=re.IGNORECASE
                )

                if match:

                    add_memory(
                        memory_type,
                        match.group(1),
                        0.80,
                        0.85
                    )

                    break

        return memories