from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.config import Config

COLLECTION_NAME = "taskpulse_memory"


class MemoryManager:
    """Manages persistent local vector embeddings for semantic task memory."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or str(Config.CHROMA_PERSIST_DIR)
        self.client = None
        self.collection = None
        self._init_chroma()

    def _init_chroma(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings

            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "TaskPulse contextual memory of completed tasks and notes"},
            )
        except Exception:
            self.client = None
            self.collection = None

    def is_available(self) -> bool:
        return self.collection is not None

    def index_task(self, task: Dict[str, Any], subtasks: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Embeds and persists a task and its subtask structure into vector memory."""
        if not self.is_available() or not task.get("id"):
            return False

        task_id = str(task["id"])
        content = task.get("content") or task.get("title") or "Untitled Task"
        priority = task.get("priority") or "Medium"
        duration = int(task.get("remaining_minutes") or task.get("estimated_minutes") or 30)

        subtask_parts = []
        if subtasks:
            for s in subtasks:
                subtask_parts.append(f"{s.get('content')} ({s.get('estimated_minutes', 15)}m)")
        subtasks_text = "; ".join(subtask_parts) if subtask_parts else "None"

        # Semantic document string for embedding
        document = f"Task: {content}. Priority: {priority}. Actual Duration: {duration} minutes. Subtasks: {subtasks_text}."

        metadata = {
            "task_id": int(task["id"]),
            "priority": str(priority),
            "duration": duration,
            "status": str(task.get("status", "Completed")),
            "source": str(task.get("source", "taskpulse")),
        }

        try:
            self.collection.upsert(
                ids=[f"task_{task_id}"],
                documents=[document],
                metadatas=[metadata],
            )
            return True
        except Exception:
            return False

    def search_similar_tasks(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Finds past tasks semantically similar to the query."""
        if not self.is_available() or not query_text or not query_text.strip():
            return []

        try:
            count = self.collection.count()
            if count == 0:
                return []

            k = min(top_k, count)
            results = self.collection.query(
                query_texts=[query_text],
                n_results=k,
            )

            memories: List[Dict[str, Any]] = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

                for doc, meta, dist in zip(docs, metas, distances):
                    memories.append({
                        "summary": doc,
                        "metadata": meta,
                        "similarity_score": round(1.0 - min(1.0, dist), 3) if dist is not None else 1.0,
                    })

            return memories
        except Exception:
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """Returns statistics on the local vector store."""
        if not self.is_available():
            return {"available": False, "total_memories": 0, "storage_engine": "ChromaDB (Inactive)"}

        try:
            count = self.collection.count()
            return {
                "available": True,
                "total_memories": count,
                "collection": COLLECTION_NAME,
                "storage_engine": "ChromaDB Persistent",
                "persist_dir": self.persist_dir,
            }
        except Exception as exc:
            return {"available": False, "total_memories": 0, "error": str(exc)}

    def clear_memory(self) -> None:
        """Clears all vectors in the collection (primarily for tests)."""
        if self.is_available():
            try:
                self.client.delete_collection(COLLECTION_NAME)
                self._init_chroma()
            except Exception:
                pass


# Singleton Memory Instance
_memory_instance: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryManager()
    return _memory_instance
