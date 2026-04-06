import sys
import os
import tempfile
import shutil
import pytest
from typing import List

# Add the project root to sys.path
sys.path.insert(0, '/sessions/inspiring-beautiful-cannon/mnt/Jarvis')

from core.interfaces import MemoryEntry, MemoryEntryType
from core.memory import LongTermMemory


@pytest.fixture
def temp_memory_dir():
    """Create a temporary directory for memory storage and clean it up after tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def memory_store(temp_memory_dir):
    """Create a LongTermMemory instance with temporary storage."""
    return LongTermMemory(persist_path=temp_memory_dir)


class TestLongTermMemory:
    """Test suite for LongTermMemory implementation."""

    def test_store_and_query(self, memory_store: LongTermMemory):
        """Test storing entries and querying for relevant results."""
        # Create test entries
        entry1 = MemoryEntry(
            id="1",
            content="The weather today is sunny and warm",
            metadata={"category": "weather"},
            entry_type=MemoryEntryType.PERSISTENT
        )
        entry2 = MemoryEntry(
            id="2",
            content="I had coffee this morning",
            metadata={"category": "food"},
            entry_type=MemoryEntryType.SESSION
        )
        entry3 = MemoryEntry(
            id="3",
            content="The sky is blue and clear today",
            metadata={"category": "weather"},
            entry_type=MemoryEntryType.PERSISTENT
        )

        # Store entries
        memory_store.store(entry1)
        memory_store.store(entry2)
        memory_store.store(entry3)

        # Query for weather-related content
        results = memory_store.query("weather today", k=5)

        # Verify we got results
        assert len(results) > 0, "Query should return results"

        # Verify we got relevant results (should include entry1 and/or entry3)
        result_ids = [r.id for r in results]
        assert "1" in result_ids or "3" in result_ids, \
            "Weather-related query should return weather entries"

        # Verify that results are MemoryEntry objects
        for result in results:
            assert isinstance(result, MemoryEntry)
            assert hasattr(result, 'id')
            assert hasattr(result, 'content')
            assert hasattr(result, 'metadata')
            assert hasattr(result, 'timestamp')
            assert hasattr(result, 'entry_type')

    def test_query_returns_k(self, memory_store: LongTermMemory):
        """Test that query returns exactly k results when k entries exist."""
        # Create and store 10 entries with different content
        for i in range(10):
            entry = MemoryEntry(
                id=str(i),
                content=f"Entry number {i} with some unique content about topic {i}",
                metadata={"index": i},
                entry_type=MemoryEntryType.PERSISTENT
            )
            memory_store.store(entry)

        # Query with k=3
        results = memory_store.query("topic", k=3)

        # Verify we get exactly 3 results
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

        # Verify all results are valid MemoryEntry objects
        for result in results:
            assert isinstance(result, MemoryEntry)
            assert result.id is not None
            assert result.content is not None

    def test_clear(self, memory_store: LongTermMemory):
        """Test that clear removes all entries."""
        # Store some entries
        for i in range(5):
            entry = MemoryEntry(
                id=str(i),
                content=f"Entry {i} with some content",
                metadata={"index": i},
                entry_type=MemoryEntryType.SESSION
            )
            memory_store.store(entry)

        # Verify entries were stored by querying
        results_before = memory_store.query("content", k=10)
        assert len(results_before) > 0, "Should have entries before clear"

        # Clear the memory
        memory_store.clear()

        # Query should return no results
        results_after = memory_store.query("content", k=10)
        assert len(results_after) == 0, "Query should return no results after clear"

    def test_metadata_preservation(self, memory_store: LongTermMemory):
        """Test that metadata is preserved during store and query."""
        # Create entry with metadata
        metadata = {
            "category": "test",
            "source": "unit_test",
            "priority": "high"
        }
        entry = MemoryEntry(
            id="meta_test",
            content="Test entry with metadata",
            metadata=metadata,
            entry_type=MemoryEntryType.PERSISTENT
        )

        # Store entry
        memory_store.store(entry)

        # Query for it
        results = memory_store.query("metadata", k=5)

        # Find our entry in results
        found_entry = None
        for result in results:
            if result.id == "meta_test":
                found_entry = result
                break

        assert found_entry is not None, "Entry should be found in query results"

        # Verify metadata was preserved
        assert found_entry.metadata["category"] == "test"
        assert found_entry.metadata["source"] == "unit_test"
        assert found_entry.metadata["priority"] == "high"

    def test_entry_type_preservation(self, memory_store: LongTermMemory):
        """Test that entry types are preserved during store and query."""
        # Create entries with different types
        session_entry = MemoryEntry(
            id="session_1",
            content="Session type memory entry",
            entry_type=MemoryEntryType.SESSION
        )
        persistent_entry = MemoryEntry(
            id="persistent_1",
            content="Persistent type memory entry",
            entry_type=MemoryEntryType.PERSISTENT
        )

        # Store both
        memory_store.store(session_entry)
        memory_store.store(persistent_entry)

        # Query and verify types are preserved
        results = memory_store.query("memory entry", k=5)

        found_entries = {}
        for result in results:
            found_entries[result.id] = result

        assert "session_1" in found_entries
        assert "persistent_1" in found_entries
        assert found_entries["session_1"].entry_type == MemoryEntryType.SESSION
        assert found_entries["persistent_1"].entry_type == MemoryEntryType.PERSISTENT

    def test_multiple_stores_same_id_overwrites(self, memory_store: LongTermMemory):
        """Test that storing an entry with the same ID overwrites the previous one."""
        # Store initial entry
        entry1 = MemoryEntry(
            id="duplicate",
            content="Original content",
            metadata={"version": 1},
            entry_type=MemoryEntryType.PERSISTENT
        )
        memory_store.store(entry1)

        # Store entry with same ID but different content
        entry2 = MemoryEntry(
            id="duplicate",
            content="Updated content",
            metadata={"version": 2},
            entry_type=MemoryEntryType.PERSISTENT
        )
        memory_store.store(entry2)

        # Query and verify we have the updated content
        results = memory_store.query("Updated", k=5)

        assert len(results) > 0
        found_entry = None
        for result in results:
            if result.id == "duplicate":
                found_entry = result
                break

        assert found_entry is not None
        assert found_entry.content == "Updated content"
        assert found_entry.metadata["version"] == 2

    def test_empty_query_returns_empty(self, memory_store: LongTermMemory):
        """Test that querying an empty store returns empty list."""
        results = memory_store.query("any search term", k=5)
        assert len(results) == 0, "Empty store should return no results"
