"""Real BlobStore backed by a single private GCS bucket. Never generates
signed URLs and is never given a route that re-exposes raw bytes to
clients — only parsed DocumentView blocks are ever served."""

from google.cloud import storage
from google.cloud.exceptions import NotFound

from app.blob import BlobNotFoundError


class GcsBlobStore:
    def __init__(self, bucket_name: str, client: storage.Client | None = None) -> None:
        self._client = client or storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    def put(self, key: str, data: bytes) -> None:
        self._bucket.blob(key).upload_from_string(data)

    def get(self, key: str) -> bytes:
        try:
            return self._bucket.blob(key).download_as_bytes()
        except NotFound as exc:
            raise BlobNotFoundError(key) from exc

    def delete(self, key: str) -> None:
        try:
            self._bucket.blob(key).delete()
        except NotFound:
            pass
