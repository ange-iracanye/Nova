import tempfile

from backend.memory_system.memory_manager import MemoryManager
from backend.memory_system.memory_extractor import MemoryExtractor


# ============================================================
# MEMORY EXTRACTOR TEST
# ============================================================

extractor = MemoryExtractor()

text = "My name is Alex. I really like mathematics."

result = extractor.extract(
    text,
    subject="general"
)

print()
print("========== MEMORY EXTRACTOR DEBUG ==========")
print(result)
print("=============================================")


# ============================================================
# REAL MEMORY INTEGRATION TEST
# ============================================================

print()
print("=" * 60)
print("NOVA MEMORY INTEGRATION TEST")
print("=" * 60)
print()

with tempfile.TemporaryDirectory() as temp_dir:

    print("Creating memory system...")

    memory = MemoryManager(
        base_path=temp_dir
    )

    print()
    print("Memory system created.")
    print()

    # ========================================================
    # USER 1
    # ========================================================

    print("Adding memories for Alex...")

    memory.remember(
        email="alex@test.com",
        user_message=(
            "My name is Alex. "
            "I really like mathematics."
        ),
        assistant_message=(
            "Nice to meet you, Alex."
        ),
        subject="general"
    )

    memory.remember(
        email="alex@test.com",
        user_message=(
            "My goal is to learn Python "
            "and become better at programming."
        ),
        assistant_message=(
            "That is a useful goal."
        ),
        subject="programming"
    )

    memory.remember(
        email="alex@test.com",
        user_message=(
            "I am preparing a physics test "
            "about electricity."
        ),
        assistant_message=(
            "Let's prepare for it."
        ),
        subject="physics"
    )

    memory.remember(
        email="alex@test.com",
        user_message=(
            "I prefer explanations that are "
            "simple and not too long."
        ),
        assistant_message=(
            "I'll keep explanations clear."
        ),
        subject="preferences"
    )

    # ========================================================
    # USER 2
    # ========================================================

    print("Adding memories for Sarah...")

    memory.remember(
        email="sarah@test.com",
        user_message=(
            "My name is Sarah. "
            "I really like biology."
        ),
        assistant_message=(
            "Nice to meet you, Sarah."
        ),
        subject="general"
    )

    memory.remember(
        email="sarah@test.com",
        user_message=(
            "My goal is to improve my English."
        ),
        assistant_message=(
            "That is a good goal."
        ),
        subject="english"
    )

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    alex = memory.get_all(
        "alex@test.com"
    )

    sarah = memory.get_all(
        "sarah@test.com"
    )

    print()
    print("Alex memories:", len(alex["memories"]))
    print("Sarah memories:", len(sarah["memories"]))

    print()
    print("========== ALEX MEMORY DEBUG ==========")

    for i, item in enumerate(alex["memories"], 1):
        print(
            f"{i}. "
            f"type={item.get('type')} | "
            f"text={item.get('text')}"
        )

    print("=======================================")

    assert len(alex["memories"]) == 7
    assert len(sarah["memories"]) == 4

    print("Memory counts: PASSED")

    # ========================================================
    # USER ISOLATION
    # ========================================================

    alex_text = str(
        alex["memories"]
    )

    sarah_text = str(
        sarah["memories"]
    )

    assert "Alex" in alex_text
    assert "Sarah" not in alex_text

    assert "Sarah" in sarah_text
    assert "Alex" not in sarah_text

    print("User isolation: PASSED")

    # ========================================================
    # SEARCH: NAME
    # ========================================================

    print()
    print("Searching Alex's name...")

    results = memory.search(
        email="alex@test.com",
        query="What is my name?",
        limit=5
    )

    print(results)

    assert results
    assert "Alex" in str(results)
    assert "Sarah" not in str(results)

    print("Name search: PASSED")

    # ========================================================
    # SEARCH: GOAL
    # ========================================================

    print()
    print("Searching Alex's goal...")

    results = memory.search(
        email="alex@test.com",
        query="What am I trying to learn?",
        limit=5
    )

    print(results)

    assert results
    assert "Python" in str(results)

    print("Goal search: PASSED")

    # ========================================================
    # SEARCH: PHYSICS
    # ========================================================

    print()
    print("Searching Alex's physics test...")

    results = memory.search(
        email="alex@test.com",
        query="What exam am I preparing for?",
        limit=5
    )

    print(results)

    assert results
    assert "physics" in str(
        results
    ).lower()

    print("Physics search: PASSED")

    # ========================================================
    # SEARCH: PREFERENCE
    # ========================================================

    print()
    print("Searching Alex's preferences...")

    results = memory.search(
        email="alex@test.com",
        query="How should you explain things to me?",
        limit=5
    )

    print(results)

    assert results
    assert (
        "simple" in str(results).lower()
        or
        "long" in str(results).lower()
    )

    print("Preference search: PASSED")

    # ========================================================
    # CROSS-USER SEARCH ISOLATION
    # ========================================================

    print()
    print("Testing cross-user search isolation...")

    results = memory.search(
        email="sarah@test.com",
        query="What am I trying to learn?",
        limit=10
    )

    print(results)

    assert "Python" not in str(results)

    print(
        "Cross-user search isolation: PASSED"
    )

    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    print()
    print("Testing build_context()...")

    context = memory.build_context(
        email="alex@test.com",
        query="Tell me what you know about my Python goal.",
        limit=5
    )

    print()
    print("GENERATED MEMORY CONTEXT:")
    print("-" * 60)
    print(context)
    print("-" * 60)

    assert context
    assert "Python" in context

    print("Context generation: PASSED")

    # ========================================================
    # CONTEXT PROTECTION
    # ========================================================

    print()
    print("Testing context length protection...")

    context = memory.build_context(
        email="alex@test.com",
        query="Tell me everything you know about me.",
        limit=20,
        max_characters=200
    )

    assert len(context) <= 200 + len(
        "\n[Memory context truncated]"
    )

    print("Context protection: PASSED")


print()
print("=" * 60)
print("ALL NOVA MEMORY INTEGRATION TESTS PASSED")
print("=" * 60)