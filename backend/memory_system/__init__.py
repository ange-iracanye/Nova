"""Nova memory system package.

V3 quality adapters are installed before NovaCore imports the concrete
memory classes, preserving compatibility while making memory and learning
state user-isolated and lifecycle-aware.
"""

from .memory_quality import install_memory_quality
from .learning_quality import install_learning_quality
from .memory_manager import MemoryManager
from .learning_memory import LearningMemory

install_memory_quality(MemoryManager)
install_learning_quality(MemoryManager, LearningMemory)

__all__ = ["MemoryManager", "LearningMemory"]
