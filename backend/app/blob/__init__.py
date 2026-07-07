"""Raw-document blob storage port. See spec/contracts/data-model.yaml's
blob_store_mapping: object key `raw/{workspace_id}`, backend-service-account
access only, never publicly readable, no signed URLs."""

from typing import Protocol


class BlobNotFoundError(Exception):
    pass


class BlobStore(Protocol):
    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes:
        """Raises BlobNotFoundError if the key doesn't exist."""

    def delete(self, key: str) -> None:
        """No-op-safe to call on a nonexistent key (idempotent)."""


def raw_document_key(workspace_id: str) -> str:
    return f"raw/{workspace_id}"
