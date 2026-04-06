from typing import List
from core.interfaces import MemoryStore, MemoryEntry


class ShortTermMemory(MemoryStore):
    """Short-term memory implementation with configurable max entries."""

    def __init__(self, max_entries: int = 50):
        """
        Initialize ShortTermMemory.

        Args:
            max_entries: Maximum number of entries to store. Oldest entries are removed
                        when exceeding this limit.
        """
        self.max_entries = max_entries
        self._entries: List[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a memory entry. Removes oldest entry if max_entries is exceeded.

        Args:
            entry: MemoryEntry to store.
        """
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)

    def query(self, text: str, k: int = 5) -> List[MemoryEntry]:
        """
        Query memory entries by text substring match.

        Args:
            text: Text to search for (case-insensitive substring match).
            k: Maximum number of results to return.

        Returns:
            List of matching MemoryEntry objects sorted by timestamp descending.
        """
        text_lower = text.lower()
        matches = [
            entry for entry in self._entries
            if text_lower in entry.content.lower()
        ]
        # Sort by timestamp descending (newest first)
        matches.sort(key=lambda entry: entry.timestamp, reverse=True)
        return matches[:k]

    def clear(self) -> None:
        """Clear all stored entries."""
        self._entries = []

    def get_recent(self, k: int = 10) -> List[MemoryEntry]:
        """
        Get the most recent k entries.

        Args:
            k: Number of recent entries to return.

        Returns:
            List of the k most recent MemoryEntry objects.
        """
        return self._entries[-k:] if len(self._entries) > 0 else []
