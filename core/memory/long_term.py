import chromadb
import os
from typing import List, Dict, Any
from core.interfaces import MemoryStore, MemoryEntry, MemoryEntryType


class SimpleEmbeddingFunction:
    """Simple embedding function that converts text to a basic numerical representation."""

    def name(self) -> str:
        """Return the name of the embedding function."""
        return "SimpleEmbeddingFunction"

    def is_legacy(self) -> bool:
        """Return whether this is a legacy embedding function."""
        return False

    def _embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        Uses a basic approach: character frequency + length normalization.

        Args:
            text: Text string to embed.

        Returns:
            Embedding as a list of floats.
        """
        # Create a simple 128-dimensional embedding based on character frequencies
        embedding = [0.0] * 128
        text_lower = text.lower()

        # Use character frequencies to populate embedding
        for i, char in enumerate(text_lower):
            if char.isalnum():
                char_code = ord(char)
                # Distribute character codes across embedding dimensions
                idx = (char_code + i) % 128
                embedding[idx] += 1.0

        # Normalize by text length
        text_len = max(len(text), 1)
        embedding = [x / text_len for x in embedding]

        return embedding

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate simple embeddings from text (for documents).

        Args:
            input: List of text strings to embed.

        Returns:
            List of embeddings (each embedding is a list of floats).
        """
        return [self._embed_text(text) for text in input]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents (ChromaDB interface).

        Args:
            texts: List of document texts.

        Returns:
            List of embeddings.
        """
        return [self._embed_text(text) for text in texts]

    def embed_query(self, input):
        """
        Embed a single query (ChromaDB interface).

        Args:
            input: Query text (can be a string or list of strings).

        Returns:
            List containing the embedding.
        """
        # Handle both string and list inputs from ChromaDB
        if isinstance(input, list):
            if len(input) > 0:
                text = input[0]
            else:
                text = ""
        else:
            text = input

        return [self._embed_text(text)]


class LongTermMemory(MemoryStore):
    """Long-term memory implementation using ChromaDB for persistent vector storage."""

    def __init__(self, persist_path: str = "data/memory"):
        """
        Initialize LongTermMemory with ChromaDB persistent client.

        Args:
            persist_path: Path where ChromaDB will persist data. Defaults to "data/memory".
        """
        self.persist_path = persist_path

        # Create persist path if it doesn't exist
        os.makedirs(persist_path, exist_ok=True)

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(path=persist_path)

        # Get or create collection with custom embedding function
        embedding_func = SimpleEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="apex_long_term",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_func
        )

    def store(self, entry: MemoryEntry) -> None:
        """
        Store a memory entry in the ChromaDB collection.
        Uses upsert to handle duplicate IDs by updating existing entries.

        Args:
            entry: MemoryEntry to store.
        """
        # Prepare metadata
        metadata = entry.metadata.copy()
        metadata["timestamp"] = entry.timestamp
        metadata["entry_type"] = entry.entry_type.value

        # Upsert document to collection (adds if new, updates if exists)
        self.collection.upsert(
            ids=[entry.id],
            documents=[entry.content],
            metadatas=[metadata]
        )

    def query(self, text: str, k: int = 5) -> List[MemoryEntry]:
        """
        Query the memory store for relevant entries using similarity search.

        Args:
            text: Text to search for using semantic similarity.
            k: Maximum number of results to return. Defaults to 5.

        Returns:
            List of the k most relevant MemoryEntry objects.
        """
        # Perform similarity search
        results = self.collection.query(
            query_texts=[text],
            n_results=k
        )

        # Convert results back to MemoryEntry objects
        entries = []
        if results and results["ids"] and len(results["ids"]) > 0:
            for i, entry_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                content = results["documents"][0][i]
                timestamp = metadata.pop("timestamp")
                entry_type_str = metadata.pop("entry_type")

                entry = MemoryEntry(
                    id=entry_id,
                    content=content,
                    metadata=metadata,
                    timestamp=timestamp,
                    entry_type=MemoryEntryType(entry_type_str)
                )
                entries.append(entry)

        return entries

    def clear(self) -> None:
        """
        Clear all entries by deleting and recreating the collection.
        """
        self.client.delete_collection(name="apex_long_term")
        # Recreate with the custom embedding function
        embedding_func = SimpleEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="apex_long_term",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_func
        )
