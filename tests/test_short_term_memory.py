import sys
sys.path.insert(0, '/sessions/inspiring-beautiful-cannon/mnt/Jarvis')

import pytest
import time
from core.memory import ShortTermMemory
from core.interfaces import MemoryEntry, MemoryEntryType


@pytest.fixture
def memory_store():
    """Fixture providing a ShortTermMemory instance."""
    return ShortTermMemory(max_entries=50)


@pytest.fixture
def sample_entries():
    """Fixture providing sample memory entries."""
    return [
        MemoryEntry(
            id="1",
            content="User asked about weather today",
            metadata={"type": "query"},
            timestamp=time.time() - 10,
            entry_type=MemoryEntryType.SESSION
        ),
        MemoryEntry(
            id="2",
            content="User likes python programming",
            metadata={"type": "preference"},
            timestamp=time.time() - 5,
            entry_type=MemoryEntryType.SESSION
        ),
        MemoryEntry(
            id="3",
            content="User location is New York",
            metadata={"type": "location"},
            timestamp=time.time(),
            entry_type=MemoryEntryType.SESSION
        ),
    ]


def test_store_and_query(memory_store, sample_entries):
    """Test storing entries and querying them by keyword."""
    # Store all sample entries
    for entry in sample_entries:
        memory_store.store(entry)

    # Query for "weather"
    results = memory_store.query("weather", k=5)
    assert len(results) == 1
    assert results[0].id == "1"
    assert "weather" in results[0].content.lower()

    # Query for "user" (should match all)
    results = memory_store.query("user", k=5)
    assert len(results) == 3

    # Query for "python"
    results = memory_store.query("python", k=5)
    assert len(results) == 1
    assert results[0].id == "2"


def test_max_entries(memory_store):
    """Test that oldest entries are removed when max_entries is exceeded."""
    small_memory = ShortTermMemory(max_entries=3)

    # Store 5 entries
    for i in range(5):
        entry = MemoryEntry(
            id=str(i),
            content=f"Entry {i}",
            metadata={},
            timestamp=time.time() + i,
            entry_type=MemoryEntryType.SESSION
        )
        small_memory.store(entry)

    # Should only have 3 most recent entries
    assert len(small_memory._entries) == 3
    assert small_memory._entries[0].id == "2"
    assert small_memory._entries[1].id == "3"
    assert small_memory._entries[2].id == "4"


def test_clear(memory_store, sample_entries):
    """Test clearing all entries."""
    # Store entries
    for entry in sample_entries:
        memory_store.store(entry)

    assert len(memory_store._entries) == 3

    # Clear
    memory_store.clear()

    assert len(memory_store._entries) == 0
    assert memory_store.query("user", k=5) == []


def test_get_recent(memory_store):
    """Test retrieving the k most recent entries."""
    # Store 5 entries
    for i in range(5):
        entry = MemoryEntry(
            id=str(i),
            content=f"Entry {i}",
            metadata={},
            timestamp=time.time() + i,
            entry_type=MemoryEntryType.SESSION
        )
        memory_store.store(entry)

    # Get 3 most recent
    recent = memory_store.get_recent(3)
    assert len(recent) == 3
    assert recent[0].id == "2"
    assert recent[1].id == "3"
    assert recent[2].id == "4"

    # Get more than available
    recent = memory_store.get_recent(10)
    assert len(recent) == 5


def test_query_no_match(memory_store, sample_entries):
    """Test query returns empty list when no matches found."""
    for entry in sample_entries:
        memory_store.store(entry)

    results = memory_store.query("nonexistent", k=5)
    assert results == []
    assert len(results) == 0


def test_query_case_insensitive(memory_store):
    """Test that query is case-insensitive."""
    entry = MemoryEntry(
        id="1",
        content="This is a Test",
        metadata={},
        timestamp=time.time(),
        entry_type=MemoryEntryType.SESSION
    )
    memory_store.store(entry)

    # Should match regardless of case
    assert len(memory_store.query("test", k=5)) == 1
    assert len(memory_store.query("TEST", k=5)) == 1
    assert len(memory_store.query("Test", k=5)) == 1


def test_query_returns_top_k(memory_store):
    """Test that query respects k parameter."""
    for i in range(10):
        entry = MemoryEntry(
            id=str(i),
            content=f"This is a test entry {i}",
            metadata={},
            timestamp=time.time() + i,
            entry_type=MemoryEntryType.SESSION
        )
        memory_store.store(entry)

    # Query with k=3
    results = memory_store.query("test", k=3)
    assert len(results) == 3
    # Should be sorted by timestamp descending (most recent first)
    assert results[0].id == "9"
    assert results[1].id == "8"
    assert results[2].id == "7"


def test_get_recent_empty(memory_store):
    """Test get_recent on empty memory."""
    recent = memory_store.get_recent(10)
    assert recent == []
