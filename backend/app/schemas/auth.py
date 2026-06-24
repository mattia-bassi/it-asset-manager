from pydantic import BaseModel
from typing import Dict, Any

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any] | None = None

class MeOut(BaseModel):
    username: str
    role: str

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "admin123",
                "new_password": "NewSecurePass123!"
            }
        }
