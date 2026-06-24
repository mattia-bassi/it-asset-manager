from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Schema base per item
class AssignmentItemBase(BaseModel):
    item_type: str = Field(..., description="Tipo item: 'asset', 'inventory' o 'sim'")
    asset_id: Optional[int] = Field(None, description="ID asset (se item_type='asset')")
    inventory_sku_id: Optional[int] = Field(None, description="ID materiale magazzino (se item_type='inventory')")
    sim_id: Optional[int] = Field(None, description="ID SIM (se item_type='sim')")
    quantity: int = Field(1, ge=1, description="Quantità (sempre 1 per asset)")
    notes: Optional[str] = Field(None, description="Note per questo item")

    @field_validator('item_type')
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        if v not in ['asset', 'inventory', 'sim']:
            raise ValueError("item_type deve essere 'asset', 'inventory' o 'sim'")
        return v


# Schema per creazione (POST)
class AssignmentItemCreate(AssignmentItemBase):
    pass


# Schema per risposta (GET)
class AssignmentItem(AssignmentItemBase):
    id: int
    assignment_id: int
    is_returned: bool = Field(default=False, description="True se item è stato restituito (sostituzione)")
    item_description: str = Field(..., description="Descrizione leggibile dell'item")

    model_config = {"from_attributes": True}

