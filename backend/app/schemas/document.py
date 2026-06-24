from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str


class DocumentCreate(DocumentBase):
    pass  # filename, file_path, file_size, mime_type vengono dal service dopo upload


class DocumentResponse(DocumentBase):
    id: int
    filename: str
    file_size: int
    mime_type: str
    uploaded_by: Optional[int] = None
    uploader_username: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
