from typing import Optional
from uuid import UUID

from pydantic import Field

from zou.app.utils.validation import BaseSchema


class CreatePersonalAssetSchema(BaseSchema):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    file_name: Optional[str] = None
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = 0
    file_hash: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = "upload"
    source_id: Optional[str] = None
    data: Optional[dict] = Field(default={})
    project_id: Optional[UUID] = None


class UpdatePersonalAssetSchema(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    file_name: Optional[str] = None
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[str] = None
    data: Optional[dict] = None
    project_id: Optional[UUID] = None


class PromotePersonalAssetSchema(BaseSchema):
    project_id: UUID = Field(...)
    asset_type_id: UUID = Field(...)
