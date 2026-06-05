import re
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol

import chromadb

from app.config import get_settings
from app.services.document_parser import DocumentParser


class EmbeddingTextClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class RegulationIndexer:
    supported_suffixes = {".txt", ".md", ".csv", ".pdf", ".docx", ".xlsx", ".doc"}
    direct_text_suffixes = {".txt", ".md", ".csv"}
    parser_suffixes = {".pdf", ".docx", ".xlsx"}
    year_pattern = re.compile(r"(19|20)\d{2}")

    def __init__(
        self,
        raw_dir,
        persist_dir,
        collection_name,
        embedding_client: EmbeddingTextClient,
    ) -> None:
        settings = get_settings()
        self.raw_dir = Path(raw_dir)
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.embedding_client = embedding_client
        self.document_parser = DocumentParser()
        self.chroma_client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.chroma_client.get_or_create_collection(collection_name)

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def build_index(self) -> int:
        """Scan raw_dir, parse supported files, chunk, embed, and write to ChromaDB."""
        total_chunks = 0
        for path in self._iter_supported_files():
            try:
                text = self._extract_text(path)
            except Exception:
                continue
            chunks = self._chunk_text(text)
            if not chunks:
                continue

            embeddings = self.embedding_client.embed_texts(chunks)
            if len(embeddings) != len(chunks):
                raise ValueError("Embedding count does not match chunk count")

            source_file = self._source_file(path)
            year_hint = self._extract_year_hint(path.name)
            ids = [self._chunk_id(source_file, chunk_index) for chunk_index in range(len(chunks))]
            metadatas = [
                {
                    "source_file": source_file,
                    "chunk_index": chunk_index,
                    "year_hint": year_hint,
                }
                for chunk_index in range(len(chunks))
            ]
            self.collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            total_chunks += len(chunks)
        return total_chunks

    def _iter_supported_files(self) -> list[Path]:
        if not self.raw_dir.exists():
            return []
        return sorted(
            path
            for path in self.raw_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in self.supported_suffixes
        )

    def _extract_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in self.direct_text_suffixes:
            return path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".pdf":
            return self.document_parser._read_pdf(path)
        if suffix == ".docx":
            return self.document_parser._read_docx(path)
        if suffix == ".xlsx":
            return self.document_parser._read_xlsx(path)
        if suffix == ".doc":
            return self._extract_doc_text(path)
        return ""

    def _extract_doc_text(self, path: Path) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "txt:Text",
                    "--outdir",
                    tmp,
                    str(path),
                ],
                check=True,
                timeout=120,
            )
            txt = Path(tmp) / f"{path.stem}.txt"
            if not txt.exists():
                return ""
            return txt.read_text(encoding="utf-8", errors="replace")

    def _chunk_text(self, text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        chunks: list[str] = []
        current: list[str] = []
        for paragraph in self._paragraphs(normalized):
            if len(paragraph) > self.chunk_size:
                if current:
                    chunks.append(self._join_paragraphs(current))
                    current = []
                chunks.extend(self._split_long_text(paragraph))
                continue

            candidate = [*current, paragraph]
            if not current or len(self._join_paragraphs(candidate)) <= self.chunk_size:
                current = candidate
                continue

            chunks.append(self._join_paragraphs(current))
            overlap = self._overlap_paragraphs(current)
            candidate = [*overlap, paragraph]
            current = candidate if len(self._join_paragraphs(candidate)) <= self.chunk_size else [paragraph]

        if current:
            chunks.append(self._join_paragraphs(current))
        return chunks

    def _paragraphs(self, text: str) -> list[str]:
        return [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", text) if paragraph.strip()]

    def _split_long_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        step = self.chunk_size - self.chunk_overlap
        while start < len(text):
            chunk = text[start : start + self.chunk_size].strip()
            if chunk:
                chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
            start += step
        return chunks

    def _overlap_paragraphs(self, paragraphs: list[str]) -> list[str]:
        if self.chunk_overlap == 0:
            return []

        overlap: list[str] = []
        for paragraph in reversed(paragraphs):
            candidate = [paragraph, *overlap]
            if len(self._join_paragraphs(candidate)) > self.chunk_overlap:
                break
            overlap = candidate
        return overlap

    def _join_paragraphs(self, paragraphs: list[str]) -> str:
        return "\n\n".join(paragraphs)

    def _source_file(self, path: Path) -> str:
        try:
            return path.relative_to(self.raw_dir).as_posix()
        except ValueError:
            return path.name

    def _extract_year_hint(self, filename: str) -> str:
        match = self.year_pattern.search(filename)
        return match.group(0) if match else ""

    def _chunk_id(self, source_file: str, chunk_index: int) -> str:
        return f"{source_file}:{chunk_index}"
