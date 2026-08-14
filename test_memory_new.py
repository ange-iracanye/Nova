import tempfile

from backend.memory_system.memory_manager import MemoryManager


class FakeEmbedder:

    def encode(
        self,
        text,
        normalize_embeddings=True
    ):

        return [1.0, 0.0, 0.0]


# =====================================
# CREATE ISOLATED MEMORY SYSTEM
# =====================================

with tempfile.TemporaryDirectory() as temp_dir:

    memory = MemoryManager(
        embedder=FakeEmbedder(),
        base_path=temp_dir
    )

    # =================================
    # USER 1
    # =================================

    memory.remember(
        email="user1@test.com",
        user_message="My name is Alex.",
        assistant_message="Nice to meet you.",
        subject="general"
    )

    # =================================
    # USER 2
    # =================================

    memory.remember(
        email="user2@test.com",
        user_message="My name is Sarah.",
        assistant_message="Nice to meet you.",
        subject="general"
    )

    # =================================
    # LOAD MEMORIES
    # =================================

    user1 = memory.get_all(
        "user1@test.com"
    )

    user2 = memory.get_all(
        "user2@test.com"
    )

    print()
    print("USER 1:")
    print(user1["memories"])

    print()
    print("USER 2:")
    print(user2["memories"])

    # =================================
    # ISOLATION TEST
    # =================================

    assert len(
        user1["memories"]
    ) == 2

    assert len(
        user2["memories"]
    ) == 2

    assert "Alex" in str(
        user1["memories"]
    )

    assert "Sarah" in str(
        user2["memories"]
    )

    assert "Sarah" not in str(
        user1["memories"]
    )

    assert "Alex" not in str(
        user2["memories"]
    )

    print()
    print(
        "MEMORY ISOLATION TEST PASSED"
    )

    # =================================
    # SEARCH TEST
    # =================================

    results = memory.search(
        email="user1@test.com",
        query="What is my name?",
        limit=5
    )

    print()
    print("SEARCH RESULTS:")
    print(results)

    assert results

    assert "Alex" in str(
        results
    )

    assert "Sarah" not in str(
        results
    )

    print()
    print(
        "MEMORY SEARCH TEST PASSED"
    )

print()
print("ALL MEMORY TESTS PASSED")