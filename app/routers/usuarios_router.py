from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ============================
# 📦 MODELOS
# ============================

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
    id_rol: int = 4  # 🔥 profesor siempre es 4
    id_division: Optional[int] = None
    planta_profe: Optional[str] = None
    id_building: Optional[int] = None


# ============================
# 📋 GET USUARIOS
# ============================

@router.get("/usuarios", response_model=list[UsuarioResponse])
async def get_usuarios():
    try:
        supabase = get_supabase_client()

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
                "rol": user["rol"]["name_rol"],
                "division": None,
                "planta": None,
                "edificio": None
            }

            # SOLO si es profesor
            if user["id_rol"] == 4:
                prof_response = supabase.table("profesor").select("""
                    planta_profe,
                    divisiones(name_div),
                    edificios(name_building)
                """).eq("id_user", user["id_user"]).execute()

                if prof_response.data:
                    prof = prof_response.data[0]
                    usuario_dict["planta"] = prof.get("planta_profe")

                    if prof.get("divisiones"):
                        usuario_dict["division"] = prof["divisiones"].get("name_div")

                    if prof.get("edificios"):
                        usuario_dict["edificio"] = prof["edificios"].get("name_building")

            usuarios.append(usuario_dict)

        return usuarios

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# ✏️ UPDATE
# ============================

@router.put("/usuarios/{id_user}")
async def update_usuario(id_user: UUID, data: UsuarioUpdate):
    try:
        supabase = get_supabase_client()

        update_data = {k: v for k, v in data.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(400, "No hay campos para actualizar")

        supabase.table("usuarios").update(update_data).eq("id_user", id_user).execute()

        return {"success": True}

    except Exception as e:
        raise HTTPException(500, str(e))


# ============================
# 🗑️ DELETE
# ============================

@router.delete("/usuarios/{id_user}")
async def delete_usuario(id_user: UUID):
    try:
        supabase = get_supabase_client()

        # eliminar datos de profesor si existen
        supabase.table("profesor").delete().eq("id_user", id_user).execute()

        # eliminar usuario
        supabase.table("usuarios").delete().eq("id_user", id_user).execute()

        return {"success": True}

    except Exception as e:
        raise HTTPException(500, str(e))


# ============================
# ➕ REGISTER PROFESOR
# ============================

@router.post("/register-profesor")
async def register_profesor(data: RegisterProfesor):
    from app.utils.security import hash_password

    try:
        supabase = get_supabase_client()

        # verificar email
        check = supabase.table("usuarios").select("id_user").eq("email_user", data.email_user).execute()
        if check.data:
            raise HTTPException(409, "Correo ya registrado")

        hashed = hash_password(data.pass_user)

        # 🔥 INSERT usuario como PROFESOR (4)
        user_resp = supabase.table("usuarios").insert({
            "name_user": data.name_user,
            "email_user": data.email_user,
            "pass_user": hashed,
            "matricula_user": data.matricula_user,
            "id_rol": 4   # ✅ CORRECTO
        }).execute()

        if not user_resp.data:
            raise HTTPException(500, "No se pudo crear usuario")

        id_user = user_resp.data[0]["id_user"]

        # 🔥 INSERT en tabla profesor
        supabase.table("profesor").insert({
            "id_user": id_user,
            "nombre_profe": data.name_user,
            "id_division": data.id_division,
            "planta_profe": data.planta_profe,
            "id_building": data.id_building
        }).execute()

        return {"success": True}

    except Exception as e:
        raise HTTPException(500, str(e))


# ============================
# 📋 DIVISIONES
# ============================

@router.get("/divisiones")
async def get_divisiones():
    try:
        supabase = get_supabase_client()
        return supabase.table("divisiones").select("id_div, name_div").execute().data
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================
# 📋 EDIFICIOS
# ============================

@router.get("/edificios-list")
async def get_edificios_list():
    try:
        supabase = get_supabase_client()
        return supabase.table("edificios").select("id_building, name_building").execute().data
    except Exception as e:
        raise HTTPException(500, str(e))
