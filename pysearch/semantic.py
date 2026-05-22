from pathlib import Path
import hashlib
import json
import chromadb
from sentence_transformers import SentenceTransformer
from .scanner import scan_files, read_file_safe

MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 40


def file_hash(path: Path) -> str:
    """Dosyanın MD5 hash'ini döner."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def chunk_text(text: str, file_path: Path, chunk_size: int = CHUNK_SIZE):
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), chunk_size):
        block = lines[i: i + chunk_size]
        block_text = "\n".join(block)
        if block_text.strip():
            chunks.append({
                "text": block_text,
                "file": str(file_path),
                "start_line": i + 1,
                "end_line": i + len(block),
            })
    return chunks


class SemanticIndex:
    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.hash_file = index_dir / "file_hashes.json"
        self.model = SentenceTransformer(MODEL_NAME)
        self.client = chromadb.PersistentClient(path=str(index_dir))
        self.collection = self.client.get_or_create_collection("pysearch")
        self.hashes = self._load_hashes()

    def _load_hashes(self) -> dict:
        """Kaydedilmiş hash'leri yükler."""
        if self.hash_file.exists():
            return json.loads(self.hash_file.read_text())
        return {}

    def _save_hashes(self):
        """Hash'leri diske kaydeder."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.hash_file.write_text(json.dumps(self.hashes))

    def _needs_reindex(self, path: Path) -> bool:
        """Dosya değişmiş mi kontrol eder."""
        key = str(path)
        try:
            current_hash = file_hash(path)
            return self.hashes.get(key) != current_hash
        except (OSError, PermissionError):
            return False

    def index_directory(self, root: Path, extensions: list = None):
        """Sadece değişen dosyaları indexler (incremental)."""
        all_chunks = []
        indexed_files = 0

        for file_path in scan_files(root, extensions=extensions):
            if not self._needs_reindex(file_path):
                continue

            content = read_file_safe(file_path)
            if content is None:
                continue

            chunks = chunk_text(content, file_path)
            all_chunks.extend(chunks)
            self.hashes[str(file_path)] = file_hash(file_path)
            indexed_files += 1

        if not all_chunks:
            return 0, indexed_files

        texts = [c["text"] for c in all_chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True).tolist()
        ids = [f"{c['file']}::{c['start_line']}" for c in all_chunks]
        metadatas = [{"file": c["file"], "start_line": c["start_line"], "end_line": c["end_line"]} for c in all_chunks]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        self._save_hashes()
        return len(all_chunks), indexed_files

    def search(self, query: str, top_k: int = 5):
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )

        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "file": results["metadatas"][0][i]["file"],
                "start_line": results["metadatas"][0][i]["start_line"],
                "end_line": results["metadatas"][0][i]["end_line"],
                "text": results["documents"][0][i],
                "score": max(0.0, 1 - results["distances"][0][i] / 2),
            })
        return output