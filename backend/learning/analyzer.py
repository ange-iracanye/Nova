class LearningAnalyzer:
    """
    Analyzes the student's learning history.

    The analyzer uses the student's recorded topics to determine
    which subjects appear to be strengths and which may need
    additional attention.

    The current profile stores topic history as a list, for example:

        [
            "mathematics",
            "physics",
            "mathematics",
            "mathematics"
        ]

    Repeated topics are important because they show how often the
    student has interacted with a subject.

    Classification:

        1 occurrence
            -> new

        2 occurrences
            -> developing

        3 or more occurrences
            -> strength

    The analyzer deliberately does not assume that a topic seen
    only once is automatically a weakness. A new topic is simply
    a topic for which Nova does not yet have enough learning
    history.
    """

    # =====================================
    # TOPIC THRESHOLDS
    # =====================================

    STRENGTH_THRESHOLD = 3

    DEVELOPING_THRESHOLD = 2

    # =====================================
    # ANALYZE
    # =====================================

    def analyze(self, profile):

        if not isinstance(
            profile,
            dict
        ):

            profile = {}

        topics = profile.get(
            "topics_seen",
            []
        )

        # =====================================
        # VALIDATE TOPIC DATA
        # =====================================

        if not isinstance(
            topics,
            list
        ):

            topics = []

        # Remove invalid topic values while keeping
        # the original topic names and repetitions.

        valid_topics = []

        for topic in topics:

            if not isinstance(
                topic,
                str
            ):

                continue

            topic = topic.strip()

            if not topic:

                continue

            valid_topics.append(
                topic
            )

        # =====================================
        # COUNT TOPICS
        # =====================================

        counts = {}

        for topic in valid_topics:

            normalized_topic = (
                topic.lower()
            )

            if normalized_topic in counts:

                counts[
                    normalized_topic
                ]["count"] += 1

            else:

                counts[
                    normalized_topic
                ] = {

                    "topic":
                        topic,

                    "count":
                        1
                }

        # =====================================
        # RESULT
        # =====================================

        result = {

            # Number of unique subjects the
            # student has interacted with.
            "total_topics":
                len(counts),

            # Total number of topic interactions.
            "total_topic_attempts":
                len(valid_topics),

            # Topics with enough repeated exposure
            # to be considered strengths.
            "strengths":
                [],

            # Topics currently being developed.
            "developing":
                [],

            # Topics the student has only recently
            # encountered.
            "new_topics":
                [],

            # Topics that may need attention.
            #
            # This remains separate from "new_topics"
            # because seeing a topic once is not enough
            # evidence to call it a weakness.
            "weaknesses":
                [],

            # Complete topic statistics.
            "topic_counts":
                {}
        }

        # =====================================
        # CLASSIFY TOPICS
        # =====================================

        for normalized_topic, data in counts.items():

            topic = data["topic"]

            amount = data["count"]

            result[
                "topic_counts"
            ][topic] = amount

            # =================================
            # STRENGTH
            # =================================

            if amount >= self.STRENGTH_THRESHOLD:

                result[
                    "strengths"
                ].append(topic)

            # =================================
            # DEVELOPING
            # =================================

            elif amount >= self.DEVELOPING_THRESHOLD:

                result[
                    "developing"
                ].append(topic)

            # =================================
            # NEW TOPIC
            # =================================

            else:

                result[
                    "new_topics"
                ].append(topic)

        # =====================================
        # CURRENT WEAKNESSES
        # =====================================

        # A topic should not be classified as a
        # weakness simply because the student has
        # seen it once.
        #
        # Actual weakness detection should eventually
        # use the UnderstandingAnalyzer / KnowledgeMap
        # confidence information.
        #
        # For now, this remains an explicit empty list
        # rather than pretending that "new" means "weak".

        result[
            "weaknesses"
        ] = []

        # =====================================
        # SORT RESULTS
        # =====================================

        result[
            "strengths"
        ].sort()

        result[
            "developing"
        ].sort()

        result[
            "new_topics"
        ].sort()

        result[
            "weaknesses"
        ].sort()

        return result

    # =====================================
    # TOPIC DETAILS
    # =====================================

    def get_topic_analysis(
        self,
        profile,
        topic
    ):

        if not isinstance(
            topic,
            str
        ):

            return None

        topic = topic.strip()

        if not topic:

            return None

        analysis = self.analyze(
            profile
        )

        topic_counts = analysis.get(
            "topic_counts",
            {}
        )

        # =====================================
        # CASE-INSENSITIVE LOOKUP
        # =====================================

        for stored_topic, count in (
            topic_counts.items()
        ):

            if (
                stored_topic.lower()
                == topic.lower()
            ):

                if count >= self.STRENGTH_THRESHOLD:

                    category = "strength"

                elif count >= self.DEVELOPING_THRESHOLD:

                    category = "developing"

                else:

                    category = "new"

                return {

                    "topic":
                        stored_topic,

                    "count":
                        count,

                    "category":
                        category
                }

        return {

            "topic":
                topic,

            "count":
                0,

            "category":
                "unknown"
        }

    # =====================================
    # SUMMARY
    # =====================================

    def get_summary(
        self,
        profile
    ):

        analysis = self.analyze(
            profile
        )

        return {

            "total_topics":
                analysis[
                    "total_topics"
                ],

            "total_topic_attempts":
                analysis[
                    "total_topic_attempts"
                ],

            "strength_count":
                len(
                    analysis[
                        "strengths"
                    ]
                ),

            "developing_count":
                len(
                    analysis[
                        "developing"
                    ]
                ),

            "new_topic_count":
                len(
                    analysis[
                        "new_topics"
                    ]
                ),

            "weakness_count":
                len(
                    analysis[
                        "weaknesses"
                    ]
                )
        }

    # =====================================
    # GET
    # =====================================

    def get(
        self,
        profile
    ):

        return self.analyze(
            profile
        )
