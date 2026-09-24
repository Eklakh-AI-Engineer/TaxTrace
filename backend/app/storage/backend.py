"""Storage backend abstraction for TaxTrace Evidence Vault.

Enforces SECURITY.md §6:
    - Files stored with random UUID storage keys outside executable paths.
    - Files are hashed with SHA-256 at storage time.
    - Path traversal protections and tenant-isolated subpaths.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Generator

from app.config import settings


class StorageBackend(ABC):
    """Abstract interface for storing and retrieving document artifacts."""

    @abstractmethod
    def save(self, tenant_id: str, file_obj: BinaryIO, extension: str = "") -> tuple[str, str, int]:
        """Save a file stream into storage.

        Args:
            tenant_id: Tenant/Firm identifier boundary.
            file_obj: Readable binary stream.
            extension: Optional file extension (e.g. '.csv', '.pdf').

        Returns:
            Tuple of (storage_uri, content_hash_hex, size_bytes).
        """
        pass

    @abstractmethod
    def read(self, storage_uri: str) -> bytes:
        """Read full file contents as bytes."""
        pass

    @abstractmethod
    def stream(self, storage_uri: str, chunk_size: int = 64 * 1024) -> Generator[bytes, None, None]:
        """Stream file contents in chunks."""
        pass

    @abstractmethod
    def delete(self, storage_uri: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def exists(self, storage_uri: str) -> bool:
        """Check if file exists in storage."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend for development and on-prem deployments."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or settings.storage_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storage_uri: str) -> Path:
        """Ensure storage_uri does not escape the base storage directory."""
        path = (self.base_dir / storage_uri).resolve()
        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected for URI: {storage_uri}")
        return path

    def save(self, tenant_id: str, file_obj: BinaryIO, extension: str = "") -> tuple[str, str, int]:
        import uuid

        # Sanitize extension
        clean_ext = extension if extension.startswith(".") else (f".{extension}" if extension else "")
        random_key = f"{uuid.uuid4().hex}{clean_ext}"

        # Tenant-isolated directory structure
        tenant_safe = Path(tenant_id).name
        target_dir = self.base_dir / tenant_safe
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / random_key
        hasher = hashlib.sha256()
        bytes_written = 0

        # Stream write and compute hash simultaneously
        file_obj.seek(0)
        with open(target_path, "wb") as f_out:
            while chunk := file_obj.read(64 * 1024):
                hasher.update(chunk)
                f_out.write(chunk)
                bytes_written += len(chunk)

        content_hash = hasher.hexdigest()
        storage_uri = f"{tenant_safe}/{random_key}"
        return storage_uri, content_hash, bytes_written

    def read(self, storage_uri: str) -> bytes:
        path = self._resolve_safe_path(storage_uri)
        if not path.is_file():
            raise FileNotFoundError(f"Stored file not found: {storage_uri}")
        return path.read_bytes()

    def stream(self, storage_uri: str, chunk_size: int = 64 * 1024) -> Generator[bytes, None, None]:
        path = self._resolve_safe_path(storage_uri)
        if not path.is_file():
            raise FileNotFoundError(f"Stored file not found: {storage_uri}")
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    def delete(self, storage_uri: str) -> bool:
        path = self._resolve_safe_path(storage_uri)
        if path.is_file():
            path.unlink()
            return True
        return False

    def exists(self, storage_uri: str) -> bool:
        path = self._resolve_safe_path(storage_uri)
        return path.is_file()


_default_backend: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    """Return the configured storage backend singleton."""
    global _default_backend
    if _default_backend is None:
        _default_backend = LocalStorageBackend()
    return _default_backend
