"""Nova memory system package.

The quality layer is installed before MemoryManager is imported by NovaCore,
so existing callers keep the same API while receiving V3 memory behavior.
"""

from .memory_quality import install_memory_quality

# Importing MemoryManager here is intentional. It gives the compatibility
# layer one canonical class to enhance before application code imports it.
from .memory_manager import MemoryManager

install_memory_quality(MemoryManager)

__all__ = ["MemoryManager"]
