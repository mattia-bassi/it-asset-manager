from typing import Optional
from pydantic import BaseModel, Field


class PDFGenerateRequest(BaseModel):
    """Schema per richiesta generazione PDF assegnazione"""
    password: Optional[str] = Field(None, description="Password da includere nel documento")
    pin_sim: Optional[str] = Field(None, description="PIN SIM da includere nel documento")
    pin_sblocco: Optional[str] = Field(None, description="PIN sblocco dispositivo")
