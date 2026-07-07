"""Request/response schemas mirroring spec/contracts/api.openapi.yaml and
data-model.yaml. Document upload is parsed directly from multipart/path
params in its router (no request body schema needed there)."""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceResponse(BaseModel):
    workspace_id: str
    created_at: datetime
    last_accessed_at: datetime | None = None


class WorkspaceDetailResponse(WorkspaceResponse):
    has_document: bool
    note_count: int
    discussion_count: int
    has_journal: bool


class BlockResponse(BaseModel):
    block_id: str
    type: str
    text: str
    level: int | None = None


class DocumentViewResponse(BaseModel):
    filename: str
    format: str
    size_bytes: int
    uploaded_at: datetime
    blocks: list[BlockResponse]


class PassageRequest(BaseModel):
    first_block_id: str
    first_block_offset: int = Field(ge=0)
    last_block_id: str
    last_block_offset: int = Field(ge=0)
    text: str


class PassageResponse(BaseModel):
    first_block_id: str
    first_block_offset: int
    last_block_id: str
    last_block_offset: int
    text: str


class NoteCreateRequest(BaseModel):
    anchor: PassageRequest
    text: str = Field(min_length=1)


class NoteUpdateRequest(BaseModel):
    text: str = Field(min_length=1)


class NoteResponse(BaseModel):
    note_id: str
    anchor: PassageResponse
    text: str
    created_at: datetime
    updated_at: datetime
