from typing import Optional
from uuid import UUID

from pydantic import Field

from zou.app.utils.validation import BaseSchema


class CreatePersonalAssetSchema(BaseSchema):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    file_name: Optional[str] = None
    extension: Optional[str] = None
    file_size: Optional[int] = 0
    source: Optional[str] = "upload"
    data: Optional[dict] = Field(default={})
    project_id: Optional[UUID] = None


class UpdatePersonalAssetSchema(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    file_name: Optional[str] = None
    extension: Optional[str] = None
    file_size: Optional[int] = None
    source: Optional[str] = None
    data: Optional[dict] = None
    project_id: Optional[UUID] = None


class PromotePersonalAssetSchema(BaseSchema):
    project_id: UUID = Field(...)
    asset_type_id: UUID = Field(...)
