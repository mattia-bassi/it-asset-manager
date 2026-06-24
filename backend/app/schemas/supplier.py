from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    contract_number: Optional[str] = None
    warranty_conditions: Optional[str] = None
    warranty_duration_months: Optional[int] = None
    notes: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    contract_number: Optional[str] = None
    warranty_conditions: Optional[str] = None
    warranty_duration_months: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SupplierListResponse(BaseModel):
    items: list[SupplierResponse]
    total: int
