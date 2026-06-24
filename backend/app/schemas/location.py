from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# --- LocationType schemas ---

class LocationTypeBase(BaseModel):
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class LocationTypeCreate(LocationTypeBase):
    pass


class LocationTypeUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class LocationTypeResponse(LocationTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Location schemas ---

class LocationBase(BaseModel):
    name: str
    location_type_id: Optional[int] = None
    site_id: int
    floor: Optional[str] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    location_type_id: Optional[int] = None
    site_id: Optional[int] = None
    floor: Optional[str] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    id: int
    location_type_name: Optional[str] = None
    location_type_icon: Optional[str] = None
    site_name: Optional[str] = None
    display_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Paginated list schemas ---

class LocationTypeListResponse(BaseModel):
    items: List[LocationTypeResponse]
    total: int


class LocationListResponse(BaseModel):
    items: List[LocationResponse]
    total: int
