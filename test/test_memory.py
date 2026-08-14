import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from memory.manager import MemoryManager


memory = MemoryManager()

memory.remember_conversation(
    "Hello",
    "Hi"
)

print(memory.get_recent_messages())