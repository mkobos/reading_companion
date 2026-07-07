from app.blob import BlobNotFoundError


class InMemoryBlobStore:
    """Test double for BlobStore. Not for production use."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes) -> None:
        self._objects[key] = data

    def get(self, key: str) -> bytes:
        if key not in self._objects:
            raise BlobNotFoundError(key)
        return self._objects[key]

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)
