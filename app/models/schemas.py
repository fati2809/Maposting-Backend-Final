from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

# ============================================================
# 📅 MODELOS DE EVENTOS
# ============================================================

class EventoBase(BaseModel):
    name_event: str
    id_building: Optional[int] = None
    timedate_event: Optional[datetime] = None
    status_event: Optional[int] = 1
    id_profe: Optional[int] = None
    id_user: Optional[int] = None

class EventoCreate(EventoBase):
    pass

class EventoResponse(EventoBase):
    id_event: int

    class Config:
        from_attributes = True


# ============================================================
# 🏫 MODELOS DE AULAS
# ============================================================

class AulaBase(BaseModel):
    nombre_aula: str
    codigo_aula: Optional[str] = None
    id_building: int
    planta: Optional[str] = None
    capacidad: int = 0
    tipo_aula: Optional[str] = None
    equipamiento: Optional[Dict[str, Any]] = Field(default_factory=dict)  # ✅ FIX mutable
    disponible: bool = True

class AulaCreate(AulaBase):
    pass

class AulaUpdate(BaseModel):
    nombre_aula: Optional[str] = None
    codigo_aula: Optional[str] = None
    id_building: Optional[int] = None
    planta: Optional[str] = None
    capacidad: Optional[int] = None
    tipo_aula: Optional[str] = None
    equipamiento: Optional[Dict[str, Any]] = None
    disponible: Optional[bool] = None

class AulaResponse(AulaBase):
    id_aula: int
    created_at: datetime
    name_building: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# 👤 MODELOS DE USUARIO
# ============================================================

class UserLogin(BaseModel):
    email_user: EmailStr
    pass_user: str
