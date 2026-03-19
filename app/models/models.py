#modelos
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re
from datetime import datetime, time

class EventoBase(BaseModel):
    name_event: str
    id_building: Optional[int] = None
    timedate_event: Optional[datetime] = None
    status_event: Optional[int] = 1
    id_profe: Optional[int] = None
    id_user: Optional[int] = None

##lol
class EventoCreate(EventoBase):
    pass


class EventoResponse(EventoBase):
    id_event: int

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email_user: EmailStr
    pass_user: str

class RegisterRequest(BaseModel):
    name_user: str
    email_user: EmailStr
    pass_user: str
    matricula_user: int
    id_rol: int 

    @field_validator("pass_user")
    @classmethod
    def validate_password(cls, v):

        # 1. Longitud mínima
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        # 2. Límite bcrypt
        if len(v) > 72:
            raise ValueError("La contraseña no puede tener más de 72 caracteres")

        # 3. Al menos un número
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")

        # 4. Al menos un caracter especial
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\]]", v):
            raise ValueError("La contraseña debe contener al menos un caracter especial")

        return v


class UserResponse(BaseModel):
    id_user: int
    name_user: str
    email_user: str
    matricula_user: Optional[int]
    rol: str
    id_rol: int

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    session: Optional[dict] = None  # Incluye access_token, refresh_token, expires_at

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if len(v) > 72:
            raise ValueError("La contraseña no puede tener más de 72 caracteres")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\]]", v):
            raise ValueError("La contraseña debe contener al menos un caracter especial")
        return v

# ============================
# 📋 ASISTENCIAS Models
# ============================
class AsistenciaBase(BaseModel):
    id_user: int
    id_event: int
    status_asist: Optional[str] = "presente"
    observacion: Optional[str] = None

class AsistenciaCreate(AsistenciaBase):
    pass

class AsistenciaUpdate(BaseModel):
    status_asist: Optional[str] = None
    observacion: Optional[str] = None

class AsistenciaResponse(AsistenciaBase):
    id_asistencia: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

# ============================
# 🕐 HORARIOS_PROFESOR Models
# ============================
class HorarioProfesorBase(BaseModel):
    id_profe: int
    dia_semana: str
    hora_inicio: time
    hora_fin: time
    id_building: Optional[int] = None
    aula: Optional[str] = None

class HorarioProfesorCreate(HorarioProfesorBase):
    pass

class HorarioProfesorUpdate(BaseModel):
    dia_semana: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    id_building: Optional[int] = None
    aula: Optional[str] = None

class HorarioProfesorResponse(HorarioProfesorBase):
    id_horario: int

    class Config:
        from_attributes = True
# ============================
# 🔐 OAuth Models
# ============================
class OAuthSyncRequest(BaseModel):
    id_user: str  # UUID de Supabase Auth
    email_user: EmailStr
    name_user: str
    provider: str  # 'google', 'github', etc.

class OAuthSyncResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
