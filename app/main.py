from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.models.models import LoginRequest, RegisterRequest, LoginResponse, UserResponse, ResetPasswordRequest, OAuthSyncRequest
from app.config import get_supabase_client
from app.services.auth_service import AuthService
from app.routers.eventos_router import router as eventos_router
from app.routers.usuarios_router import router as usuarios_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.edificios_router import router as edificios_router
from app.routers.divisiones_router import router as divisiones_router
from app.routers.asistencias_router import router as asistencias_router
from app.routers.horarios_router import router as horarios_router
from app.routers.aulas_router import router as aulas_router
from app.routers.profesores_router import router as profesores_router

app = FastAPI()

# ================================================
# 1. CORS — SIEMPRE primero, antes de todo
# ================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # desarrollo: permite todo
    allow_credentials=False,    # debe ser False cuando allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# ============================
# 2. STARTUP EVENT
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
# 3. TEST endpoints (para debug)
# ============================
@app.get("/test")
async def test():
    return {"ok": True, "message": "Servidor funcionando correctamente"}

@app.get("/test-db")
async def test_db():
    try:
        supabase = get_supabase_client()
        result = supabase.table("usuarios").select("id_user").limit(1).execute()
        return {"ok": True, "supabase": "conectado", "data": result.data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ============================
# 4. LOGIN
# ============================
@app.get("/login")
async def login_get_not_allowed():
    """Endpoint informativo - Login requiere POST"""
    raise HTTPException(
        status_code=405, 
        detail="Method Not Allowed: Use POST method to /login with email_user and pass_user in body"
    )

@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    try:
        result = await AuthService.sign_in(
            email=credentials.email_user,
            password=credentials.pass_user
        )
        user_data = result["user_data"]
        return LoginResponse(
            success=True,
            message="Login exitoso",
            user=UserResponse(
                id_user=user_data["id_user"],
                name_user=user_data["name_user"],
                email_user=user_data["email_user"],
                matricula_user=user_data.get("matricula_user"),
                id_rol=user_data["id_rol"],
                rol=user_data["rol"]
            ),
            session={
                "access_token": result["session"].access_token,
                "refresh_token": result["session"].refresh_token,
                "expires_at": result["session"].expires_at
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 5. REGISTER
# ============================
@app.post("/register")
async def register(user_data: RegisterRequest):
    try:
        from app.utils.security import validate_password
        try:
            validate_password(user_data.pass_user)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        result = await AuthService.sign_up(
            email=user_data.email_user,
            password=user_data.pass_user,
            metadata={
                "name_user": user_data.name_user,
                "matricula_user": user_data.matricula_user,
                "id_rol": user_data.id_rol
            }
        )
        return {
            "success": True,
            "message": "Usuario registrado correctamente. Revisa tu email para verificar tu cuenta."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 6. RESET PASSWORD
# ============================
@app.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    try:
        result = await AuthService.reset_password(data.email)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 7. OAUTH SYNC
# ============================
@app.post("/auth/oauth/sync")
async def oauth_sync(data: OAuthSyncRequest):
    """
    Sincroniza un usuario autenticado con OAuth en la tabla usuarios
    Se llama después del callback de Google/OAuth
    """
    try:
        result = await AuthService.sync_oauth_user(
            id_user=data.id_user,
            email_user=data.email_user,
            name_user=data.name_user,
            provider=data.provider
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 8. LOGOUT
# ============================
@app.get("/logout")
async def logout_get_not_allowed():
    """Endpoint informativo - Logout requiere POST"""
    raise HTTPException(
        status_code=405,
        detail="Method Not Allowed: Use POST method to /logout"
    )

@app.post("/logout")
async def logout():
    try:
        result = await AuthService.sign_out("")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 9. CHECK AUTH (útil para frontend)
# ============================
@app.get("/check-auth")
async def check_auth(request: Request):
    """Verifica si hay un token válido en el header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    token = auth_header.split(" ")[1]
    try:
        supabase = get_supabase_client()
        user = supabase.auth.get_user(token)
        return {"authenticated": True, "user": user.user.id if user.user else None}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido")

# ================================================
# 10. ROUTERS
# ================================================
app.include_router(eventos_router)
app.include_router(usuarios_router)
app.include_router(dashboard_router)
app.include_router(edificios_router)
app.include_router(divisiones_router)
app.include_router(asistencias_router)
app.include_router(horarios_router)
app.include_router(aulas_router)
app.include_router(profesores_router)

# ================================================
# 11. OPTIONS catch-all — SIEMPRE al final
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
# 🚀 Run local
# ============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)