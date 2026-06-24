from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    role: str = Field(..., pattern="^(admin|operatore|user)$")
    is_active: bool = True
    person_id: Optional[int] = None  # NUOVO: collegamento a Person

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Validazione password robusta e configurabile
        Legge requisiti da environment per flessibilità
        """
        import re
        import os
        
        # Lunghezza minima configurabile (default: 12)
        min_length = int(os.getenv('PASSWORD_MIN_LENGTH', '12'))
        if len(v) < min_length:
            raise ValueError(f'Password must be at least {min_length} characters')
        
        # Check opzionali (tutti default: true, ma disabilitabili per compatibilità)
        require_upper = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
        require_lower = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
        require_numbers = os.getenv('PASSWORD_REQUIRE_NUMBERS', 'true').lower() == 'true'
        require_special = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true'
        
        if require_upper and not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if require_lower and not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if require_numbers and not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&* etc.)')
        
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['admin', 'operatore', 'user']
        if v not in allowed_roles:
            raise ValueError(f"Ruolo deve essere uno tra: {', '.join(allowed_roles)}")
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    role: Optional[str] = Field(None, pattern="^(admin|operatore|user)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)
    person_id: Optional[int] = None  # NUOVO: può essere modificato
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['admin', 'operatore', 'user']
            if v not in allowed_roles:
                raise ValueError(f"Ruolo deve essere uno tra: {', '.join(allowed_roles)}")
        return v

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    is_permanently_disabled: bool = False
    person_id: Optional[int] = None
    person_first_name: Optional[str] = None
    person_last_name: Optional[str] = None
    person_email: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserChangeRole(BaseModel):
    role: str = Field(..., pattern="^(admin|operatore|user)$")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['admin', 'operatore', 'user']
        if v not in allowed_roles:
            raise ValueError(f"Ruolo deve essere uno tra: {', '.join(allowed_roles)}")
        return v


class UserLinkPerson(BaseModel):
    person_id: int = Field(..., gt=0, description="ID of the person to link")
