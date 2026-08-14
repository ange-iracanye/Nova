import re


class SubjectDetector:
    """
    Detects the academic subject and concept of a student's message.

    Nova uses a hybrid detection strategy:

        1. Explicit subject names
        2. Strong subject/topic patterns
        3. Keyword scoring
        4. Optional semantic detector
        5. Confidence-based fallback

    The detector returns a structured result instead of only returning
    a string.

    Example:

        {
            "subject": "physics",
            "topic": "newton's second law",
            "confidence": 0.94,
            "method": "pattern"
        }

    For backwards compatibility, detect() can still return only the
    subject string.
    """

    # =====================================
    # SUBJECT DEFINITIONS
    # =====================================

    SUBJECTS = {

        "physics": {

            "aliases": [
                "physics",
                "physique"
            ],

            "keywords": [
                "gravity",
                "force",
                "velocity",
                "speed",
                "energy",
                "motion",
                "acceleration",
                "mass",
                "newton",
                "newtons",
                "momentum",
                "friction",
                "pressure",
                "work",
                "power",
                "wave",
                "waves",
                "frequency",
                "wavelength",
                "electricity",
                "electric",
                "magnetic",
                "magnetism",
                "voltage",
                "current",
                "resistance",
                "circuit",
                "charge",
                "light",
                "optics",
                "lens",
                "temperature",
                "thermodynamics"
            ]
        },

        "biology": {

            "aliases": [
                "biology",
                "biologie"
            ],

            "keywords": [
                "cell",
                "cells",
                "dna",
                "rna",
                "gene",
                "genes",
                "genetics",
                "chromosome",
                "heart",
                "blood",
                "plant",
                "plants",
                "photosynthesis",
                "chlorophyll",
                "organism",
                "organisms",
                "animal",
                "animals",
                "body",
                "tissue",
                "organ",
                "organs",
                "protein",
                "bacteria",
                "virus",
                "viruses",
                "evolution",
                "ecosystem",
                "species",
                "respiration",
                "digestion",
                "nervous system",
                "immune system"
            ]
        },

        "chemistry": {

            "aliases": [
                "chemistry",
                "chimie"
            ],

            "keywords": [
                "atom",
                "atoms",
                "molecule",
                "molecules",
                "acid",
                "acids",
                "base",
                "bases",
                "reaction",
                "reactions",
                "element",
                "elements",
                "compound",
                "compounds",
                "chemical",
                "chemicals",
                "electron",
                "electrons",
                "proton",
                "protons",
                "neutron",
                "neutrons",
                "periodic table",
                "bond",
                "bonds",
                "ionic",
                "covalent",
                "oxidation",
                "reduction",
                "ph",
                "molar",
                "mole",
                "moles",
                "solution",
                "solvent",
                "solute",
                "concentration"
            ]
        },

        "math": {

            "aliases": [
                "math",
                "mathematics",
                "maths",
                "mathematics",
                "mathématique",
                "mathématiques"
            ],

            "keywords": [
                "equation",
                "equations",
                "algebra",
                "fraction",
                "fractions",
                "percentage",
                "percent",
                "number",
                "numbers",
                "triangle",
                "triangles",
                "geometry",
                "area",
                "volume",
                "perimeter",
                "angle",
                "angles",
                "circle",
                "circles",
                "function",
                "functions",
                "derivative",
                "derivatives",
                "integral",
                "integrals",
                "calculus",
                "probability",
                "statistics",
                "matrix",
                "matrices",
                "vector",
                "vectors",
                "polynomial",
                "polynomials",
                "factor",
                "factorisation",
                "factorization",
                "logarithm",
                "logarithms",
                "exponent",
                "exponents",
                "sequence",
                "sequences"
            ]
        },

        "history": {

            "aliases": [
                "history",
                "histoire"
            ],

            "keywords": [
                "war",
                "wars",
                "king",
                "kings",
                "queen",
                "queens",
                "empire",
                "empires",
                "revolution",
                "revolutions",
                "civilization",
                "civilisation",
                "civilizations",
                "civilisations",
                "battle",
                "battles",
                "emperor",
                "empress",
                "president",
                "monarchy",
                "monarch",
                "colonization",
                "colonisation",
                "independence",
                "treaty",
                "ancient",
                "medieval",
                "renaissance"
            ]
        },

        "geography": {

            "aliases": [
                "geography",
                "géographie"
            ],

            "keywords": [
                "country",
                "countries",
                "capital",
                "capitals",
                "continent",
                "continents",
                "climate",
                "map",
                "maps",
                "population",
                "latitude",
                "longitude",
                "ocean",
                "oceans",
                "sea",
                "seas",
                "river",
                "rivers",
                "mountain",
                "mountains",
                "desert",
                "deserts",
                "region",
                "regions",
                "territory",
                "territories",
                "geography",
                "geographic",
                "geographical",
                "urban",
                "rural"
            ]
        }

    }

    # =====================================
    # STRONG CONCEPT PATTERNS
    # =====================================

    CONCEPT_PATTERNS = {

        "physics": {

            "newton's second law":
                [
                    "newton's second law",
                    "newtons second law",
                    "second law of newton",
                    "second law of motion",
                    "f = ma",
                    "f=ma"
                ],

            "newton's first law":
                [
                    "newton's first law",
                    "newtons first law",
                    "first law of motion",
                    "law of inertia"
                ],

            "newton's third law":
                [
                    "newton's third law",
                    "newtons third law",
                    "third law of motion",
                    "action and reaction"
                ],

            "gravity":
                [
                    "law of gravity",
                    "gravitational force",
                    "gravity"
                ],

            "kinematics":
                [
                    "kinematics",
                    "equations of motion",
                    "motion equation"
                ],

            "electric circuits":
                [
                    "electric circuit",
                    "electric circuits",
                    "ohm's law",
                    "ohms law",
                    "voltage current resistance"
                ]
        },

        "biology": {

            "photosynthesis":
                [
                    "photosynthesis",
                    "photosynthesis process"
                ],

            "cell structure":
                [
                    "cell structure",
                    "cell membrane",
                    "cell nucleus",
                    "organelles",
                    "mitochondria"
                ],

            "genetics":
                [
                    "genetics",
                    "genetic inheritance",
                    "inheritance",
                    "punnett square",
                    "dominant allele",
                    "recessive allele"
                ],

            "dna":
                [
                    "dna",
                    "dna replication",
                    "genetic code"
                ]
        },

        "chemistry": {

            "atomic structure":
                [
                    "atomic structure",
                    "structure of the atom",
                    "electron configuration",
                    "electron shells"
                ],

            "chemical reactions":
                [
                    "chemical reaction",
                    "chemical reactions",
                    "reaction equation",
                    "balancing equations"
                ],

            "acids and bases":
                [
                    "acid and base",
                    "acids and bases",
                    "acid base",
                    "ph scale",
                    "ph"
                ],

            "moles":
                [
                    "mole calculation",
                    "moles",
                    "molar mass",
                    "amount of substance"
                ]
        },

        "math": {

            "linear equations":
                [
                    "linear equation",
                    "linear equations",
                    "equation of a line"
                ],

            "quadratic equations":
                [
                    "quadratic equation",
                    "quadratic equations",
                    "second degree equation"
                ],

            "fractions":
                [
                    "fraction",
                    "fractions",
                    "adding fractions",
                    "subtracting fractions",
                    "multiplying fractions"
                ],

            "percentages":
                [
                    "percentage",
                    "percentages",
                    "percentage increase",
                    "percentage decrease"
                ],

            "pythagorean theorem":
                [
                    "pythagorean theorem",
                    "pythagoras theorem",
                    "theorem of pythagoras"
                ]
        },

        "history": {

            "french revolution":
                [
                    "french revolution",
                    "révolution française"
                ],

            "world war one":
                [
                    "world war one",
                    "world war i",
                    "first world war"
                ],

            "world war two":
                [
                    "world war two",
                    "world war ii",
                    "second world war"
                ]
        },

        "geography": {

            "climate":
                [
                    "climate",
                    "climate change",
                    "global warming"
                ],

            "population":
                [
                    "population",
                    "population growth",
                    "population density"
                ],

            "continents":
                [
                    "continent",
                    "continents"
                ]
        }

    }

    # =====================================
    # INITIALIZATION
    # =====================================

    def __init__(
        self,
        semantic_detector=None
    ):

        """
        semantic_detector:
            Optional callable used for AI-based detection.

        Expected:

            semantic_detector(text)

        It may return:

            {
                "subject": "physics",
                "topic": "newton's second law",
                "confidence": 0.95
            }

        If no semantic detector is supplied, Nova uses the
        local detection system.
        """

        self.semantic_detector = (
            semantic_detector
        )

    # =====================================
    # NORMALIZE
    # =====================================

    def _normalize(
        self,
        text
    ):

        if not isinstance(
            text,
            str
        ):

            return ""

        text = text.lower().strip()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # =====================================
    # WORD MATCH
    # =====================================

    def _contains_word(
        self,
        text,
        word
    ):

        word = self._normalize(
            word
        )

        if not word:

            return False

        # Multi-word concepts should be searched
        # as phrases.

        if " " in word:

            return word in text

        return bool(
            re.search(
                rf"\b{re.escape(word)}\b",
                text
            )
        )

    # =====================================
    # EXPLICIT SUBJECT
    # =====================================

    def _detect_explicit_subject(
        self,
        text
    ):

        for subject, data in (
            self.SUBJECTS.items()
        ):

            aliases = data.get(
                "aliases",
                []
            )

            for alias in aliases:

                if self._contains_word(
                    text,
                    alias
                ):

                    return {

                        "subject":
                            subject,

                        "confidence":
                            1.0,

                        "method":
                            "explicit"
                    }

        return None

    # =====================================
    # CONCEPT DETECTION
    # =====================================

    def _detect_concept(
        self,
        text
    ):

        matches = []

        for subject, concepts in (
            self.CONCEPT_PATTERNS.items()
        ):

            for topic, patterns in (
                concepts.items()
            ):

                for pattern in patterns:

                    if self._contains_word(
                        text,
                        pattern
                    ):

                        matches.append({

                            "subject":
                                subject,

                            "topic":
                                topic,

                            "confidence":
                                0.97,

                            "method":
                                "pattern"
                        })

                        break

        if not matches:

            return None

        # If multiple concepts are found,
        # choose the first strongest match.

        return matches[0]

    # =====================================
    # KEYWORD SCORING
    # =====================================

    def _score_subjects(
        self,
        text
    ):

        scores = {}

        matched_words = {}

        for subject, data in (
            self.SUBJECTS.items()
        ):

            keywords = data.get(
                "keywords",
                []
            )

            score = 0

            matches = []

            for keyword in keywords:

                if self._contains_word(
                    text,
                    keyword
                ):

                    # Longer phrases are more informative
                    # than generic single words.

                    if " " in keyword:

                        score += 3

                    else:

                        score += 1

                    matches.append(
                        keyword
                    )

            if score > 0:

                scores[
                    subject
                ] = score

                matched_words[
                    subject
                ] = matches

        if not scores:

            return None

        ranked = sorted(
            scores.items(),
            key=lambda item:
                item[1],
            reverse=True
        )

        best_subject = ranked[0][0]

        best_score = ranked[0][1]

        second_score = (
            ranked[1][1]
            if len(ranked) > 1
            else 0
        )

        # If two subjects are nearly tied,
        # local keyword detection isn't reliable enough.

        if (
            second_score > 0
            and best_score <= second_score + 1
        ):

            confidence = 0.45

        elif best_score >= 5:

            confidence = 0.90

        elif best_score >= 3:

            confidence = 0.78

        else:

            confidence = 0.65

        return {

            "subject":
                best_subject,

            "confidence":
                confidence,

            "method":
                "keyword",

            "matched_words":
                matched_words.get(
                    best_subject,
                    []
                )
        }

    # =====================================
    # SEMANTIC DETECTION
    # =====================================

    def _detect_semantic(
        self,
        text
    ):

        if not self.semantic_detector:

            return None

        try:

            result = (
                self.semantic_detector(
                    text
                )
            )

        except Exception:

            return None

        if not isinstance(
            result,
            dict
        ):

            return None

        subject = result.get(
            "subject"
        )

        if not isinstance(
            subject,
            str
        ):

            return None

        subject = (
            self._normalize(
                subject
            )
        )

        if subject not in self.SUBJECTS:

            return None

        confidence = result.get(
            "confidence",
            0.70
        )

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.70

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        topic = result.get(
            "topic"
        )

        if isinstance(
            topic,
            str
        ):

            topic = topic.strip()

        else:

            topic = None

        return {

            "subject":
                subject,

            "topic":
                topic,

            "confidence":
                confidence,

            "method":
                "semantic"
        }

    # =====================================
    # DETECT
    # =====================================

    def analyze(
        self,
        text,
        use_semantic=True
    ):

        text = self._normalize(
            text
        )

        if not text:

            return {

                "subject":
                    None,

                "topic":
                    None,

                "confidence":
                    0.0,

                "method":
                    "none",

                "matched_words":
                    []
            }

        # =====================================
        # 1. EXPLICIT SUBJECT
        # =====================================

        explicit = (
            self._detect_explicit_subject(
                text
            )
        )

        # =====================================
        # 2. STRONG CONCEPT
        # =====================================

        concept = (
            self._detect_concept(
                text
            )
        )

        # A known concept is stronger than a
        # generic subject keyword.

        if concept:

            if explicit:

                if (
                    explicit["subject"]
                    == concept["subject"]
                ):

                    concept["confidence"] = 1.0

            return concept

        # =====================================
        # 3. EXPLICIT SUBJECT
        # =====================================

        if explicit:

            return {

                "subject":
                    explicit["subject"],

                "topic":
                    None,

                "confidence":
                    explicit["confidence"],

                "method":
                    explicit["method"],

                "matched_words":
                    []
            }

        # =====================================
        # 4. KEYWORD SCORING
        # =====================================

        keyword_result = (
            self._score_subjects(
                text
            )
        )

        # =====================================
        # 5. SEMANTIC FALLBACK
        # =====================================

        semantic_result = None

        if use_semantic:

            # Only use semantic detection when
            # local detection is weak or uncertain.

            should_use_semantic = (

                keyword_result is None

                or keyword_result[
                    "confidence"
                ] < 0.80
            )

            if should_use_semantic:

                semantic_result = (
                    self._detect_semantic(
                        text
                    )
                )

        # =====================================
        # 6. COMPARE RESULTS
        # =====================================

        if semantic_result:

            if keyword_result is None:

                return semantic_result

            if (
                semantic_result[
                    "confidence"
                ]
                >
                keyword_result[
                    "confidence"
                ]
            ):

                return semantic_result

        # =====================================
        # 7. KEYWORD RESULT
        # =====================================

        if keyword_result:

            return {

                "subject":
                    keyword_result[
                        "subject"
                    ],

                "topic":
                    None,

                "confidence":
                    keyword_result[
                        "confidence"
                    ],

                "method":
                    keyword_result[
                        "method"
                    ],

                "matched_words":
                    keyword_result.get(
                        "matched_words",
                        []
                    )
            }

        # =====================================
        # 8. UNKNOWN
        # =====================================

        return {

            "subject":
                None,

            "topic":
                None,

            "confidence":
                0.0,

            "method":
                "none",

            "matched_words":
                []
        }

    # =====================================
    # BACKWARDS COMPATIBILITY
    # =====================================

    def detect(
        self,
        text,
        use_semantic=True
    ):

        result = self.analyze(
            text,
            use_semantic=use_semantic
        )

        return result[
            "subject"
        ]

    # =====================================
    # GET TOPIC
    # =====================================

    def detect_topic(
        self,
        text,
        use_semantic=True
    ):

        result = self.analyze(
            text,
            use_semantic=use_semantic
        )

        return result.get(
            "topic"
        )

    # =====================================
    # GET RESULT
    # =====================================

    def get_result(
        self,
        text,
        use_semantic=True
    ):

        return self.analyze(
            text,
            use_semantic=use_semantic
        )

    # =====================================
    # VALID SUBJECT
    # =====================================

    def is_valid_subject(
        self,
        subject
    ):

        if not isinstance(
            subject,
            str
        ):

            return False

        subject = (
            self._normalize(
                subject
            )
        )

        return (
            subject
            in self.SUBJECTS
        )

    # =====================================
    # GET SUBJECTS
    # =====================================

    def get_subjects(self):

        return list(
            self.SUBJECTS.keys()
        )

    # =====================================
    # GET TOPICS
    # =====================================

    def get_known_topics(
        self,
        subject=None
    ):

        if subject:

            subject = (
                self._normalize(
                    subject
                )
            )

            concepts = (
                self.CONCEPT_PATTERNS.get(
                    subject,
                    {}
                )
            )

            return list(
                concepts.keys()
            )

        topics = []

        for concepts in (
            self.CONCEPT_PATTERNS.values()
        ):

            topics.extend(
                concepts.keys()
            )

        return sorted(
            set(topics)
        )