from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from app.models.models import LoginRequest, RegisterRequest, LoginResponse, UserResponse
from app.config import get_supabase_client  # ← corregido
from eventos_router import router as eventos_router
from usuarios_router import router as usuarios_router
from dashboard_router import router as dashboard_router
from edificios_router import router as edificios_router
from divisiones_router import router as divisiones_router

from app.utils.security import (
    verify_password,
    hash_password,
    validate_password
)
from app.services.auth_service import AuthService

app = FastAPI()

# ================================================
# CORS MIDDLEWARE
# ================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# ============================
# MODELOS OAUTH
# ============================
class GoogleLoginRequest(BaseModel):
    id_token: str
    email: str
    name: Optional[str] = None
    photo: Optional[str] = None

class OAuthSyncRequest(BaseModel):
    id_user: str
    email_user: str
    name_user: str
    provider: Optional[str] = "google"

class OAuthUserResponse(BaseModel):
    id_user: str
    name_user: str
    email_user: str
    matricula_user: Optional[int] = None
    id_rol: int
    rol: str

class OAuthSyncResponse(BaseModel):
    success: bool
    message: str
    user: OAuthUserResponse


# ============================
# STARTUP EVENT
# ============================
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("Iniciando servidor FastAPI...")
    print("="*50)
    try:
        supabase = get_supabase_client()
        supabase.table("usuarios").select("id_user", count="exact").limit(1).execute()
        print("Servidor iniciado correctamente")
        print("Documentacion: http://localhost:8000/docs")
        print("="*50 + "\n")
    except Exception as e:
        print(f"Error al conectar con Supabase: {str(e)}")
        print("Verifica tu archivo .env")
        print("="*50 + "\n")


# ============================
# TEST
# ============================
@app.get("/test")
async def test():
    return {"ok": True, "message": "Servidor funcionando correctamente"}


# ============================
# TEST SUPABASE
# ============================
@app.get("/test-db")
async def test_db():
    try:
        supabase = get_supabase_client()
        result = supabase.table("usuarios").select("id_user").limit(1).execute()
        return {"ok": True, "supabase": "conectado", "data": result.data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================
# LOGIN
# ============================
@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    try:
        supabase = get_supabase_client()

        response = supabase.table("usuarios").select("""
            id_user, name_user, email_user, pass_user,
            matricula_user, id_rol,
            rol!inner(name_rol)
        """).eq("email_user", credentials.email_user).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user = response.data[0]

        if not verify_password(credentials.pass_user, user["pass_user"]):
            raise HTTPException(status_code=401, detail="Contrasena incorrecta")

        return LoginResponse(
            success=True,
            message="Login exitoso",
            user=UserResponse(
                id_user=str(user["id_user"]),
                name_user=user["name_user"],
                email_user=user["email_user"],
                matricula_user=user.get("matricula_user"),
                id_rol=user["id_rol"],
                rol=user["rol"]["name_rol"] if isinstance(user.get("rol"), dict) else ""
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================
# REGISTER
# ============================
@app.post("/register")
async def register(user_data: RegisterRequest):
    try:
        supabase = get_supabase_client()

        check = supabase.table("usuarios").select("id_user").eq("email_user", user_data.email_user).execute()
        if check.data:
            raise HTTPException(status_code=409, detail="Correo ya registrado")

        try:
            hashed_password = hash_password(user_data.pass_user)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        supabase.table("usuarios").insert({
            "name_user": user_data.name_user,
            "email_user": user_data.email_user,
            "pass_user": hashed_password,
            "matricula_user": user_data.matricula_user,
            "id_rol": user_data.id_rol
        }).execute()

        return {"success": True, "message": "Usuario registrado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================
# AUTH OAUTH SYNC
# ============================
@app.post("/auth/oauth/sync", response_model=OAuthSyncResponse)
async def oauth_sync(data: OAuthSyncRequest):
    try:
        supabase = get_supabase_client()

        # Buscar si el usuario ya existe por email
        response = supabase.table("usuarios").select("""
            id_user, name_user, email_user,
            matricula_user, id_rol,
            rol!inner(name_rol)
        """).eq("email_user", data.email_user).execute()

        if response.data:
            user = response.data[0]
            return OAuthSyncResponse(
                success=True,
                message="Usuario autenticado correctamente",
                user=OAuthUserResponse(
                    id_user=str(user["id_user"]),
                    name_user=user["name_user"],
                    email_user=user["email_user"],
                    matricula_user=user.get("matricula_user"),
                    id_rol=user["id_rol"],
                    rol=user["rol"]["name_rol"] if isinstance(user.get("rol"), dict) else ""
                )
            )

        # Usuario nuevo — obtener id del rol 'usuario' por defecto
        rol_response = supabase.table("rol").select("id_rol").eq("name_rol", "usuario").single().execute()
        if not rol_response.data:
            raise HTTPException(status_code=500, detail="Rol 'usuario' no encontrado en la BD")

        id_rol_default = rol_response.data["id_rol"]

        # Insertar nuevo usuario
        insert_response = supabase.table("usuarios").insert({
            "id_user": data.id_user,
            "name_user": data.name_user,
            "email_user": data.email_user,
            "id_rol": id_rol_default
        }).execute()

        if not insert_response.data:
            raise HTTPException(status_code=500, detail="Error al crear el usuario")

        # Devolver el usuario recién creado con su rol
        new_user = supabase.table("usuarios").select("""
            id_user, name_user, email_user,
            matricula_user, id_rol,
            rol!inner(name_rol)
        """).eq("email_user", data.email_user).single().execute()

        user = new_user.data
        return OAuthSyncResponse(
            success=True,
            message="Usuario creado correctamente",
            user=OAuthUserResponse(
                id_user=str(user["id_user"]),
                name_user=user["name_user"],
                email_user=user["email_user"],
                matricula_user=user.get("matricula_user"),
                id_rol=user["id_rol"],
                rol=user["rol"]["name_rol"] if isinstance(user.get("rol"), dict) else ""
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en OAuth sync: {str(e)}")


# ============================
# LOGIN WITH GOOGLE
# ============================
@app.post("/login/google", response_model=LoginResponse)
async def login_google(data: GoogleLoginRequest):
    try:
        result = await AuthService.sign_in_with_google_token(
            id_token=data.id_token,
            email=data.email,
            name=data.name,
            photo=data.photo,
        )
        user_data = result["user_data"]
        session = result["session"]
        return LoginResponse(
            success=True,
            message="Login con Google exitoso",
            user=UserResponse(
                id_user=str(user_data["id_user"]),
                name_user=user_data["name_user"],
                email_user=user_data["email_user"],
                matricula_user=user_data.get("matricula_user"),
                id_rol=user_data["id_rol"],
                rol=user_data["rol"],
            ),
            session={
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expires_at": session.expires_at,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ================================================
# ROUTERS
# ================================================
app.include_router(eventos_router)
app.include_router(usuarios_router)
app.include_router(dashboard_router)
app.include_router(edificios_router)
app.include_router(divisiones_router)


# ================================================
# OPTIONS catch-all — SIEMPRE al final
# ================================================
@app.options("/{full_path:path}")
async def catch_all_options(full_path: str, request: Request):
    print(f"OPTIONS recibida: /{full_path}")
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Max-Age": "86400",
        }
    )


# ============================
# Run local
# ============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)