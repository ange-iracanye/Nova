from datetime import datetime


class MemoryConsolidator:

    def __init__(self, student_memory):
        self.student_memory = student_memory


    # =====================================
    # CONSOLIDATE A MEMORY
    # =====================================

    def consolidate(
        self,
        memory,
        subject=None
    ):

        if not memory:
            return


        memory_type = memory.get(
            "type",
            "episode"
        )


        text = memory.get(
            "text",
            ""
        )


        if not text:
            return


        # =================================
        # FACT
        # =================================

        if memory_type == "fact":

            self.student_memory.add_fact(

                text,

                subject=subject,

                confidence=
                    memory.get(
                        "confidence",
                        0.8
                    )
            )


        # =================================
        # PREFERENCE
        # =================================

        elif memory_type == "preference":

            self._store_preference(
                text
            )


        # =================================
        # LEARNING
        # =================================

        elif memory_type == "learning":

            self._store_learning(
                subject,
                text
            )


        # =================================
        # EXPLICIT MEMORY
        # =================================

        elif memory_type == "explicit_memory":

            self.student_memory.add_explicit_memory(

                text,

                subject=subject
            )


    # =====================================
    # PREFERENCE
    # =====================================

    def _store_preference(
        self,
        text
    ):

        key = (
            "preference_"
            + str(
                len(
                    self.student_memory
                    .memory[
                        "preferences"
                    ]
                )
            )
        )


        self.student_memory.set_preference(
            key,
            text
        )


    # =====================================
    # LEARNING
    # =====================================

    def _store_learning(
        self,
        subject,
        text
    ):

        if not subject:
            subject = "general"


        if subject not in (
            self.student_memory
            .memory[
                "progress"
            ]
        ):

            self.student_memory.memory[
                "progress"
            ][subject] = {

                "observations": [],

                "attempts": 0,

                "confidence": 50,

                "last_updated": None
            }


        data = (
            self.student_memory
            .memory[
                "progress"
            ][subject]
        )


        data[
            "observations"
        ].append(text)


        data[
            "attempts"
        ] += 1


        data[
            "last_updated"
        ] = (
            datetime.now()
            .isoformat()
        )


        # Keep the observations useful
        # without allowing unlimited growth.

        if len(
            data["observations"]
        ) > 100:

            data[
                "observations"
            ] = data[
                "observations"
            ][-100:]


        self.student_memory.save()