from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

router = APIRouter()

class UsuarioResponse(BaseModel):
    id_user: UUID
    name_user: str
    email_user: str
    matricula_user: Optional[int] = None
    id_rol: int
    rol: str
    division: Optional[str] = None
    planta: Optional[str] = None
    edificio: Optional[str] = None

class UsuarioUpdate(BaseModel):
    name_user: Optional[str] = None
    email_user: Optional[str] = None
    matricula_user: Optional[int] = None
    id_rol: Optional[int] = None

class RegisterProfesor(BaseModel):
    name_user: str
    email_user: str
    pass_user: str
    matricula_user: int
    id_rol: int = 3
    id_division: Optional[int] = None
    planta_profe: Optional[str] = None
    id_building: Optional[int] = None

# ============================
# 📋 GET ALL USUARIOS
# ============================
@router.get("/usuarios", response_model=list[UsuarioResponse])
async def get_usuarios():
    try:
        supabase = get_supabase_client()
        
        # Obtener usuarios con roles
        response = supabase.table("usuarios").select("""
            id_user, name_user, email_user, matricula_user, id_rol,
            rol!inner(name_rol)
        """).order("id_user").execute()
        
        usuarios = []
        for user in response.data:
            usuario_dict = {
                "id_user": user["id_user"],
                "name_user": user["name_user"],
                "email_user": user["email_user"],
                "matricula_user": user.get("matricula_user"),
                "id_rol": user["id_rol"],
                "rol": user["rol"]["name_rol"] if isinstance(user.get("rol"), dict) else "",
                "division": None,
                "planta": None,
                "edificio": None
            }
            
            # Si es profesor, obtener datos adicionales
            if user["id_rol"] == 3:
                prof_response = supabase.table("profesor").select("""
                    planta_profe, id_division, id_building,
                    divisiones(name_div),
                    edificios(name_building)
                """).eq("nombre_profe", user["name_user"]).execute()
                
                if prof_response.data and len(prof_response.data) > 0:
                    prof = prof_response.data[0]
                    usuario_dict["planta"] = prof.get("planta_profe")
                    if prof.get("divisiones"):
                        usuario_dict["division"] = prof["divisiones"].get("name_div")
                    if prof.get("edificios"):
                        usuario_dict["edificio"] = prof["edificios"].get("name_building")
            
            usuarios.append(usuario_dict)
        
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ✏️ UPDATE USUARIO
# ============================
@router.put("/usuarios/{id_user}")
async def update_usuario(id_user: UUID, data: UsuarioUpdate):
    try:
        supabase = get_supabase_client()
        update_data = {}
        if data.name_user is not None:
            update_data["name_user"] = data.name_user
        if data.email_user is not None:
            update_data["email_user"] = data.email_user
        if data.matricula_user is not None:
            update_data["matricula_user"] = data.matricula_user
        if data.id_rol is not None:
            update_data["id_rol"] = data.id_rol
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        supabase.table("usuarios").update(update_data).eq("id_user", id_user).execute()
        return {"success": True, "message": "Usuario actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 🗑️ DELETE USUARIO
# ============================
@router.delete("/usuarios/{id_user}")
async def delete_usuario(id_user: UUID):
    try:
        supabase = get_supabase_client()
        
        # Verificar si el usuario existe y obtener su rol y nombre
        response = supabase.table("usuarios").select("id_rol, name_user").eq("id_user", id_user).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        usuario = response.data[0]
        
        # Si es profesor (id_rol = 3), eliminarlo también de la tabla profesor
        if usuario["id_rol"] == 3:
            supabase.table("profesor").delete().eq("nombre_profe", usuario["name_user"]).execute()
        
        supabase.table("usuarios").delete().eq("id_user", id_user).execute()
        return {"success": True, "message": "Usuario eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 🔄 TOGGLE ROL
# ============================
@router.patch("/usuarios/{id_user}/toggle-rol")
async def toggle_rol(id_user: UUID):
    try:
        supabase = get_supabase_client()
        response = supabase.table("usuarios").select("id_rol").eq("id_user", id_user).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user = response.data[0]
        nuevo_rol = 2 if user["id_rol"] == 1 else 1
        supabase.table("usuarios").update({"id_rol": nuevo_rol}).eq("id_user", id_user).execute()
        return {"success": True, "nuevo_rol": nuevo_rol}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ➕ REGISTER PROFESOR
# ============================
@router.post("/register-profesor")
async def register_profesor(data: RegisterProfesor):
    from app.utils.security import hash_password
    try:
        supabase = get_supabase_client()
        
        # Verificar si el correo ya existe
        check = supabase.table("usuarios").select("id_user").eq("email_user", data.email_user).execute()
        if check.data:
            raise HTTPException(status_code=409, detail="Correo ya registrado")
        
        # Hash de la contraseña
        try:
            hashed = hash_password(data.pass_user)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Insertar usuario
        supabase.table("usuarios").insert({
            "name_user": data.name_user,
            "email_user": data.email_user,
            "pass_user": hashed,
            "matricula_user": data.matricula_user,
            "id_rol": 3
        }).execute()
        
        # Insertar en tabla profesor
        supabase.table("profesor").insert({
            "nombre_profe": data.name_user,
            "id_division": data.id_division,
            "planta_profe": data.planta_profe,
            "id_building": data.id_building
        }).execute()
        
        return {"success": True, "message": "Profesor registrado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📋 GET DIVISIONES
# ============================
@router.get("/divisiones")
async def get_divisiones():
    try:
        supabase = get_supabase_client()
        response = supabase.table("divisiones").select("id_div, name_div").order("id_div").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📋 GET EDIFICIOS LIST
# ============================
@router.get("/edificios-list")
async def get_edificios_list():
    try:
        supabase = get_supabase_client()
        response = supabase.table("edificios").select("id_building, name_building").order("id_building").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")