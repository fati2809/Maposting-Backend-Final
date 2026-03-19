from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from app.models.models import AsistenciaCreate, AsistenciaUpdate, AsistenciaResponse
from typing import List, Optional

router = APIRouter()

# ============================
# 📋 GET ALL ASISTENCIAS
# ============================
@router.get("/asistencias", response_model=List[AsistenciaResponse])
async def get_asistencias(id_event: Optional[int] = None, id_user: Optional[int] = None):
    """
    Obtener todas las asistencias, con filtros opcionales por evento o usuario
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("asistencias").select("""
            id_asistencia, id_user, id_event, fecha_hora, 
            status_asist, observacion,
            usuarios(name_user, email_user),
            eventos(name_event)
        """)
        
        if id_event:
            query = query.eq("id_event", id_event)
        if id_user:
            query = query.eq("id_user", id_user)
        
        response = query.order("fecha_hora", desc=True).execute()
        
        asistencias = []
        for item in response.data:
            asistencia = {
                "id_asistencia": item["id_asistencia"],
                "id_user": item["id_user"],
                "id_event": item["id_event"],
                "fecha_hora": item["fecha_hora"],
                "status_asist": item.get("status_asist", "presente"),
                "observacion": item.get("observacion"),
                "name_user": item["usuarios"]["name_user"] if item.get("usuarios") else None,
                "name_event": item["eventos"]["name_event"] if item.get("eventos") else None
            }
            asistencias.append(asistencia)
        
        return asistencias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📋 GET ASISTENCIA BY ID
# ============================
@router.get("/asistencias/{id_asistencia}")
async def get_asistencia(id_asistencia: int):
    try:
        supabase = get_supabase_client()
        response = supabase.table("asistencias").select("""
            id_asistencia, id_user, id_event, fecha_hora, 
            status_asist, observacion,
            usuarios(name_user, email_user, matricula_user),
            eventos(name_event, timedate_event)
        """).eq("id_asistencia", id_asistencia).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
        item = response.data[0]
        return {
            "id_asistencia": item["id_asistencia"],
            "id_user": item["id_user"],
            "id_event": item["id_event"],
            "fecha_hora": item["fecha_hora"],
            "status_asist": item.get("status_asist", "presente"),
            "observacion": item.get("observacion"),
            "usuario": item.get("usuarios"),
            "evento": item.get("eventos")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ➕ CREATE ASISTENCIA
# ============================
@router.post("/asistencias")
async def create_asistencia(data: AsistenciaCreate):
    try:
        supabase = get_supabase_client()
        
        # Verificar que el usuario existe
        user_check = supabase.table("usuarios").select("id_user").eq("id_user", data.id_user).execute()
        if not user_check.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que el evento existe
        event_check = supabase.table("eventos").select("id_event").eq("id_event", data.id_event).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        # Verificar que no exista ya una asistencia para este usuario y evento
        existing = supabase.table("asistencias").select("id_asistencia").eq("id_user", data.id_user).eq("id_event", data.id_event).execute()
        if existing.data:
            raise HTTPException(status_code=409, detail="Ya existe un registro de asistencia para este usuario en este evento")
        
        asistencia_data = {
            "id_user": data.id_user,
            "id_event": data.id_event,
            "status_asist": data.status_asist or "presente",
            "observacion": data.observacion
        }
        
        response = supabase.table("asistencias").insert(asistencia_data).execute()
        return {
            "success": True, 
            "message": "Asistencia registrada correctamente",
            "id_asistencia": response.data[0]["id_asistencia"] if response.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ✏️ UPDATE ASISTENCIA
# ============================
@router.put("/asistencias/{id_asistencia}")
async def update_asistencia(id_asistencia: int, data: AsistenciaUpdate):
    try:
        supabase = get_supabase_client()
        
        # Verificar que existe
        check = supabase.table("asistencias").select("id_asistencia").eq("id_asistencia", id_asistencia).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
        update_data = {}
        if data.status_asist is not None:
            # Validar status
            valid_status = ["presente", "ausente", "justificado", "tardanza"]
            if data.status_asist not in valid_status:
                raise HTTPException(status_code=400, detail=f"Status inválido. Debe ser uno de: {', '.join(valid_status)}")
            update_data["status_asist"] = data.status_asist
        
        if data.observacion is not None:
            update_data["observacion"] = data.observacion
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        supabase.table("asistencias").update(update_data).eq("id_asistencia", id_asistencia).execute()
        return {"success": True, "message": "Asistencia actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 🗑️ DELETE ASISTENCIA
# ============================
@router.delete("/asistencias/{id_asistencia}")
async def delete_asistencia(id_asistencia: int):
    try:
        supabase = get_supabase_client()
        
        # Verificar que existe
        check = supabase.table("asistencias").select("id_asistencia").eq("id_asistencia", id_asistencia).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
        supabase.table("asistencias").delete().eq("id_asistencia", id_asistencia).execute()
        return {"success": True, "message": "Asistencia eliminada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📊 GET REPORTE DE ASISTENCIAS
# ============================
@router.get("/asistencias/reporte/evento/{id_event}")
async def get_reporte_asistencias(id_event: int):
    """
    Obtener reporte de asistencias por evento con estadísticas
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar que el evento existe
        evento_check = supabase.table("eventos").select("name_event, timedate_event").eq("id_event", id_event).execute()
        if not evento_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        # Obtener todas las asistencias del evento
        asistencias = supabase.table("asistencias").select("""
            id_asistencia, status_asist, observacion, fecha_hora,
            usuarios(name_user, email_user, matricula_user)
        """).eq("id_event", id_event).execute()
        
        # Calcular estadísticas
        total = len(asistencias.data)
        presentes = sum(1 for a in asistencias.data if a.get("status_asist") == "presente")
        ausentes = sum(1 for a in asistencias.data if a.get("status_asist") == "ausente")
        justificados = sum(1 for a in asistencias.data if a.get("status_asist") == "justificado")
        tardanza = sum(1 for a in asistencias.data if a.get("status_asist") == "tardanza")
        
        return {
            "evento": evento_check.data[0],
            "estadisticas": {
                "total": total,
                "presentes": presentes,
                "ausentes": ausentes,
                "justificados": justificados,
                "tardanza": tardanza,
                "porcentaje_asistencia": round((presentes / total * 100), 2) if total > 0 else 0
            },
            "asistencias": asistencias.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
