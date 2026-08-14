from backend.memory_system.memory_manager import (
    MemoryManager
)

from backend.memory_system.memory_extractor import (
    MemoryExtractor
)


class MemoryEngine:

    def __init__(self):

        print(
            "Loading Nova Memory Engine..."
        )

        self.manager = (
            MemoryManager()
        )

        self.extractor = (
            MemoryExtractor()
        )

        print(
            "Nova Memory Engine ready."
        )


    # =====================================
    # PROCESS MEMORY
    # =====================================

    def remember_turn(
        self,
        user_email,
        user_message,
        assistant_message,
        subject=None,
        confidence=None,
        conversation_id=None
    ):

        if not user_message:
            return

        self.manager.remember(

            user_email,

            user_message,

            assistant_message,

            subject=subject,

            confidence=confidence,

            conversation_id=conversation_id
        )


    # =====================================
    # RECALL
    # =====================================

    def recall(
        self,
        user_email,
        query,
        limit=12
    ):

        return self.manager.search(

            user_email,

            query,

            limit=limit
        )


    # =====================================
    # BUILD CONTEXT
    # =====================================

    def build_context(
        self,
        user_email,
        query,
        subject=None,
        limit=10
    ):

        return self.manager.build_context(

            user_email,

            query,

            subject=subject,

            limit=limit
        )

