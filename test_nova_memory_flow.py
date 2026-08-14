from backend.core.nova_core import NovaCore

print()
print("=" * 60)
print("NOVA MEMORY FLOW TEST")
print("=" * 60)
print()


nova = NovaCore()


email = "alex@test.com"


# ============================================================
# REQUEST 1
# ============================================================

print()
print("REQUEST 1")
print("-" * 60)

result = nova.process(
    message=(
        "My name is Alex and my goal is to become "
        "better at Python programming."
    ),
    user_email=email
)

print()
print("Nova:")
print(result["answer"])


# ============================================================
# REQUEST 2
# ============================================================

print()
print("REQUEST 2")
print("-" * 60)

result = nova.process(
    message="What am I trying to achieve?",
    user_email=email
)

print()
print("Nova:")
print(result["answer"])


# ============================================================
# REQUEST 3
# ============================================================

print()
print("REQUEST 3")
print("-" * 60)

result = nova.process(
    message=(
        "I prefer simple explanations that are "
        "not too long."
    ),
    user_email=email
)

print()
print("Nova:")
print(result["answer"])


# ============================================================
# REQUEST 4
# ============================================================

print()
print("REQUEST 4")
print("-" * 60)

result = nova.process(
    message="How should you explain things to me?",
    user_email=email
)

print()
print("Nova:")
print(result["answer"])


# ============================================================
# MEMORY INSPECTION
# ============================================================

print()
print("=" * 60)
print("FINAL MEMORY STATE")
print("=" * 60)

memories = nova.memory.get_all(email)

for i, item in enumerate(
    memories["memories"],
    1
):

    print(
        f"{i}. "
        f"type={item.get('type')} | "
        f"text={item.get('text')} | "
        f"confidence={item.get('confidence')}"
    )


print()
print("=" * 60)
print("NOVA MEMORY FLOW TEST COMPLETE")
print("=" * 60)