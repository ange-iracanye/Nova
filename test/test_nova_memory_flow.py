from backend.core import NovaCore


print()
print("=" * 70)
print("NOVA END-TO-END MEMORY FLOW TEST")
print("=" * 70)
print()


nova = NovaCore()


email = "alex@test.com"


# ============================================================
# FIRST MESSAGE
# ============================================================

print("USER:")
print("My name is Alex and my goal is to become better at Python.")
print()

response = nova.process(
    message=(
        "My name is Alex and my goal is "
        "to become better at Python."
    ),
    user_email=email
)

print()
print("NOVA:")
print(response["answer"])
print()


# ============================================================
# SECOND MESSAGE
# ============================================================

print("=" * 70)
print("TESTING MEMORY RECALL")
print("=" * 70)
print()

response = nova.process(
    message="What is my name and what am I trying to learn?",
    user_email=email
)

print()
print("NOVA:")
print(response["answer"])
print()


# ============================================================
# THIRD MESSAGE
# ============================================================

print("=" * 70)
print("TESTING PREFERENCE MEMORY")
print("=" * 70)
print()

response = nova.process(
    message=(
        "I prefer simple explanations. "
        "Can you explain Python variables?"
    ),
    user_email=email
)

print()
print("NOVA:")
print(response["answer"])
print()


# ============================================================
# FOURTH MESSAGE
# ============================================================

print("=" * 70)
print("TESTING MEMORY AFTER MULTIPLE CONVERSATIONS")
print("=" * 70)
print()

response = nova.process(
    message="How should you explain things to me?",
    user_email=email
)

print()
print("NOVA:")
print(response["answer"])
print()


print()
print("=" * 70)
print("END-TO-END TEST COMPLETE")
print("=" * 70)