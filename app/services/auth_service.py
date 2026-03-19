"""
Servicio de autenticación usando Supabase Auth
"""
from typing import Optional
from fastapi import HTTPException
from app.config import get_supabase_client


class AuthService:
    """Maneja autenticación con Supabase Auth"""
    
    @staticmethod
    async def sign_up(email: str, password: str, metadata: dict) -> dict:
        """
        Registra un nuevo usuario usando Supabase Auth
        
        Args:
            email: Email del usuario
            password: Contraseña
            metadata: Datos adicionales (nombre, matricula, rol)
        
        Returns:
            Dict con información del usuario y sesión
        """
        try:
            supabase = get_supabase_client()
            
            # Crear usuario en Supabase Auth
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata  # Guarda metadata en auth.users
                }
            })
            
            if response.user is None:
                raise HTTPException(
                    status_code=400,
                    detail="No se pudo crear el usuario. El email puede estar ya registrado."
                )
            
            # Insertar en tabla usuarios personalizada
            user_data = {
                "id_user": response.user.id,  # Usar el UUID de auth.users
                "name_user": metadata.get("name_user"),
                "email_user": email,
                "matricula_user": metadata.get("matricula_user"),
                "id_rol": metadata.get("id_rol", 2),
            }
            
            supabase.table("usuarios").insert(user_data).execute()
            
            return {
                "user": response.user,
                "session": response.session
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error al registrar usuario: {str(e)}"
            )
    
    @staticmethod
    async def sign_in(email: str, password: str) -> dict:
        """
        Inicia sesión usando Supabase Auth
        
        Args:
            email: Email del usuario
            password: Contraseña
        
        Returns:
            Dict con usuario, sesión y rol
        """
        try:
            supabase = get_supabase_client()
            
            # Autenticar con Supabase Auth
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user is None:
                raise HTTPException(
                    status_code=401,
                    detail="Credenciales incorrectas"
                )
            
            # Obtener datos adicionales de la tabla usuarios
            user_response = supabase.table("usuarios").select("""
                id_user, name_user, email_user, matricula_user, id_rol,
                rol!inner(name_rol)
            """).eq("id_user", response.user.id).execute()
            
            if not user_response.data:
                raise HTTPException(
                    status_code=404,
                    detail="Usuario no encontrado en la base de datos"
                )
            
            user_data = user_response.data[0]
            
            return {
                "user": response.user,
                "session": response.session,
                "user_data": {
                    "id_user": user_data["id_user"],
                    "name_user": user_data["name_user"],
                    "email_user": user_data["email_user"],
                    "matricula_user": user_data.get("matricula_user"),
                    "id_rol": user_data["id_rol"],
                    "rol": user_data["rol"]["name_rol"] if isinstance(user_data.get("rol"), dict) else ""
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Error al iniciar sesión: {str(e)}"
            )
    
    @staticmethod
    async def sign_out(access_token: str) -> dict:
        """Cierra sesión del usuario"""
        try:
            supabase = get_supabase_client()
            supabase.auth.sign_out()
            return {"message": "Sesión cerrada correctamente"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al cerrar sesión: {str(e)}"
            )
    
    @staticmethod
    async def reset_password(email: str) -> dict:
        """
        Envía email para resetear contraseña
        
        Args:
            email: Email del usuario
        
        Returns:
            Mensaje de confirmación
        """
        try:
            supabase = get_supabase_client()
            supabase.auth.reset_password_for_email(email)
            return {
                "message": "Se ha enviado un email con instrucciones para resetear tu contraseña"
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al enviar email: {str(e)}"
            )
    
    @staticmethod
    async def update_password(access_token: str, new_password: str) -> dict:
        """
        Actualiza la contraseña del usuario autenticado
        
        Args:
            access_token: Token de sesión
            new_password: Nueva contraseña
        
        Returns:
            Mensaje de confirmación
        """
        try:
            supabase = get_supabase_client()
            # El cliente debe estar autenticado con el token
            supabase.auth.update_user({"password": new_password})
            return {"message": "Contraseña actualizada correctamente"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al actualizar contraseña: {str(e)}"
            )
    
    @staticmethod
    async def get_user(access_token: str) -> dict:
        """
        Obtiene información del usuario autenticado
        
        Args:
            access_token: Token de sesión
        
        Returns:
            Datos del usuario
        """
        try:
            supabase = get_supabase_client()
            user = supabase.auth.get_user(access_token)
            if user is None:
                raise HTTPException(status_code=401, detail="Token inválido")
            return user
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Error al obtener usuario: {str(e)}"
            )
    
    @staticmethod
    async def sync_oauth_user(id_user: str, email_user: str, name_user: str, provider: str) -> dict:
        """
        Sincroniza un usuario autenticado con OAuth en la tabla usuarios
        Si el usuario no existe, lo crea. Si existe, devuelve sus datos.
        
        Args:
            id_user: ID del usuario de Supabase Auth
            email_user: Email del usuario
            name_user: Nombre del usuario
            provider: Proveedor OAuth (google, etc)
        
        Returns:
            Datos del usuario con rol
        """
        try:
            supabase = get_supabase_client()
            
            # Verificar si el usuario ya existe en la tabla usuarios
            user_response = supabase.table("usuarios").select("""
                id_user, name_user, email_user, matricula_user, id_rol,
                rol!inner(name_rol)
            """).eq("id_user", id_user).execute()
            
            # Si el usuario existe, devolver sus datos
            if user_response.data and len(user_response.data) > 0:
                user_data = user_response.data[0]
                return {
                    "success": True,
                    "message": "Usuario sincronizado correctamente",
                    "user": {
                        "id_user": user_data["id_user"],
                        "name_user": user_data["name_user"],
                        "email_user": user_data["email_user"],
                        "matricula_user": user_data.get("matricula_user"),
                        "id_rol": user_data["id_rol"],
                        "rol": user_data["rol"]["name_rol"] if isinstance(user_data.get("rol"), dict) else ""
                    }
                }
            
            # Si no existe, crear el usuario con rol 2 (Estudiante por defecto)
            new_user_data = {
                "id_user": id_user,
                "name_user": name_user,
                "email_user": email_user,
                "matricula_user": None,  # OAuth users no tienen matrícula
                "id_rol": 2  # Rol de Estudiante por defecto
            }
            
            insert_response = supabase.table("usuarios").insert(new_user_data).execute()
            
            if not insert_response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Error al crear usuario en la base de datos"
                )
            
            # Obtener el usuario recién creado con su rol
            user_response = supabase.table("usuarios").select("""
                id_user, name_user, email_user, matricula_user, id_rol,
                rol!inner(name_rol)
            """).eq("id_user", id_user).execute()
            
            if not user_response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Error al obtener datos del usuario creado"
                )
            
            user_data = user_response.data[0]
            
            return {
                "success": True,
                "message": "Usuario creado y sincronizado correctamente",
                "user": {
                    "id_user": user_data["id_user"],
                    "name_user": user_data["name_user"],
                    "email_user": user_data["email_user"],
                    "matricula_user": user_data.get("matricula_user"),
                    "id_rol": user_data["id_rol"],
                    "rol": user_data["rol"]["name_rol"] if isinstance(user_data.get("rol"), dict) else ""
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al sincronizar usuario OAuth: {str(e)}"
            )
