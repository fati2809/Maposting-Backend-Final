from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

router = APIRouter()

# ============================================================
# MODELOS PYDANTIC
# ============================================================

class AulaBase(BaseModel):
    nombre_aula: str
    codigo_aula: Optional[str] = None
    id_building: int
    planta: Optional[str] = None
    capacidad: int = 0
    tipo_aula: Optional[str] = None
    equipamiento: Optional[Dict[str, Any]] = {}
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

# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/aulas")
async def get_aulas():
    """
    Obtener todas las aulas con información del edificio
    """
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("aulas").select("""
                id_aula, nombre_aula, codigo_aula, id_building,
                planta, capacidad, tipo_aula, equipamiento, disponible, created_at,
                edificios(name_building, code_building)
            """).order("id_building", desc=False).order("nombre_aula", desc=False).execute()
        )
        
        # Transformar para aplanar la estructura
        aulas = []
        for aula in response.data:
            aula_data = {
                "id_aula": aula["id_aula"],
                "nombre_aula": aula["nombre_aula"],
                "codigo_aula": aula.get("codigo_aula"),
                "id_building": aula["id_building"],
                "planta": aula.get("planta"),
                "capacidad": aula.get("capacidad", 0),
                "tipo_aula": aula.get("tipo_aula"),
                "equipamiento": aula.get("equipamiento", {}),
                "disponible": aula.get("disponible", True),
                "created_at": aula.get("created_at"),
                "name_building": aula["edificios"]["name_building"] if aula.get("edificios") else None,
                "code_building": aula["edificios"]["code_building"] if aula.get("edificios") else None
            }
            aulas.append(aula_data)
        
        return aulas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener aulas: {str(e)}")


@router.get("/aulas/{id_aula}")
async def get_aula(id_aula: int):
    """
    Obtener una aula específica por ID
    """
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("aulas").select("""
                id_aula, nombre_aula, codigo_aula, id_building,
                planta, capacidad, tipo_aula, equipamiento, disponible, created_at,
                edificios(name_building, code_building)
            """).eq("id_aula", id_aula).single().execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Aula no encontrada")
        
        aula = response.data
        return {
            "id_aula": aula["id_aula"],
            "nombre_aula": aula["nombre_aula"],
            "codigo_aula": aula.get("codigo_aula"),
            "id_building": aula["id_building"],
            "planta": aula.get("planta"),
            "capacidad": aula.get("capacidad", 0),
            "tipo_aula": aula.get("tipo_aula"),
            "equipamiento": aula.get("equipamiento", {}),
            "disponible": aula.get("disponible", True),
            "created_at": aula.get("created_at"),
            "name_building": aula["edificios"]["name_building"] if aula.get("edificios") else None,
            "code_building": aula["edificios"]["code_building"] if aula.get("edificios") else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener aula: {str(e)}")


@router.get("/aulas/edificio/{id_building}")
async def get_aulas_by_edificio(id_building: int):
    """
    Obtener todas las aulas de un edificio específico
    Útil para el modal en la página de edificios
    """
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("aulas").select("""
                id_aula, nombre_aula, codigo_aula, id_building,
                planta, capacidad, tipo_aula, equipamiento, disponible, created_at
            """).eq("id_building", id_building).order("planta").order("nombre_aula").execute()
        )
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener aulas del edificio: {str(e)}")


@router.get("/aulas/disponibles/buscar")
async def get_aulas_disponibles(
    id_building: Optional[int] = None,
    planta: Optional[str] = None,
    capacidad_minima: Optional[int] = None,
    tipo_aula: Optional[str] = None,
    solo_disponibles: bool = True
):
    """
    Buscar aulas disponibles con filtros opcionales
    Útil para buscar aulas alternativas cuando hay conflictos
    """
    try:
        supabase = get_supabase_client()
        
        # Construir query base
        query = supabase.table("aulas").select("""
            id_aula, nombre_aula, codigo_aula, id_building,
            planta, capacidad, tipo_aula, equipamiento, disponible, created_at,
            edificios(name_building, code_building)
        """)
        
        # Aplicar filtros
        if id_building is not None:
            query = query.eq("id_building", id_building)
        
        if planta is not None:
            query = query.eq("planta", planta)
        
        if capacidad_minima is not None:
            query = query.gte("capacidad", capacidad_minima)
        
        if tipo_aula is not None:
            query = query.eq("tipo_aula", tipo_aula)
        
        if solo_disponibles:
            query = query.eq("disponible", True)
        
        response = await asyncio.to_thread(
            lambda: query.order("capacidad", desc=False).execute()
        )
        
        # Transformar para aplanar estructura
        aulas = []
        for aula in response.data:
            aula_data = {
                "id_aula": aula["id_aula"],
                "nombre_aula": aula["nombre_aula"],
                "codigo_aula": aula.get("codigo_aula"),
                "id_building": aula["id_building"],
                "planta": aula.get("planta"),
                "capacidad": aula.get("capacidad", 0),
                "tipo_aula": aula.get("tipo_aula"),
                "equipamiento": aula.get("equipamiento", {}),
                "disponible": aula.get("disponible", True),
                "created_at": aula.get("created_at"),
                "name_building": aula["edificios"]["name_building"] if aula.get("edificios") else None
            }
            aulas.append(aula_data)
        
        return aulas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar aulas: {str(e)}")


@router.post("/aulas")
async def create_aula(data: AulaCreate):
    """
    Crear una nueva aula
    """
    try:
        supabase = get_supabase_client()
        
        # Validar que el edificio existe
        edificio_response = await asyncio.to_thread(
            lambda: supabase.table("edificios").select("id_building").eq("id_building", data.id_building).execute()
        )
        
        if not edificio_response.data:
            raise HTTPException(status_code=404, detail="El edificio especificado no existe")
        
        # Validar valores de planta
        plantas_validas = ["baja", "alta", "sotano", "azotea"]
        if data.planta and data.planta not in plantas_validas:
            raise HTTPException(
                status_code=400, 
                detail=f"Planta inválida. Valores permitidos: {', '.join(plantas_validas)}"
            )
        
        # Validar capacidad
        if data.capacidad < 0:
            raise HTTPException(status_code=400, detail="La capacidad no puede ser negativa")
        
        # Preparar datos para insertar
        aula_data = {
            "nombre_aula": data.nombre_aula,
            "codigo_aula": data.codigo_aula,
            "id_building": data.id_building,
            "planta": data.planta,
            "capacidad": data.capacidad,
            "tipo_aula": data.tipo_aula,
            "equipamiento": data.equipamiento or {},
            "disponible": data.disponible
        }
        
        response = await asyncio.to_thread(
            lambda: supabase.table("aulas").insert(aula_data).execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo crear el aula")
        
        return {
            "success": True,
            "id_aula": response.data[0]["id_aula"],
            "mensaje": "Aula creada correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear aula: {str(e)}")


@router.put("/aulas/{id_aula}")
async def update_aula(id_aula: int, data: AulaUpdate):
    """
    Actualizar una aula existente
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar que el aula existe
        aula_response = await asyncio.to_thread(
            lambda: supabase.table("aulas").select("id_aula").eq("id_aula", id_aula).execute()
        )
        
        if not aula_response.data:
            raise HTTPException(status_code=404, detail="Aula no encontrada")
        
        # Construir objeto de actualización solo con campos proporcionados
        update_data = {}
        
        if data.nombre_aula is not None:
            update_data["nombre_aula"] = data.nombre_aula
        
        if data.codigo_aula is not None:
            update_data["codigo_aula"] = data.codigo_aula
        
        if data.id_building is not None:
            # Validar que el edificio existe
            edificio_response = await asyncio.to_thread(
                lambda: supabase.table("edificios").select("id_building").eq("id_building", data.id_building).execute()
            )
            if not edificio_response.data:
                raise HTTPException(status_code=404, detail="El edificio especificado no existe")
            update_data["id_building"] = data.id_building
        
        if data.planta is not None:
            plantas_validas = ["baja", "alta", "sotano", "azotea"]
            if data.planta not in plantas_validas:
                raise HTTPException(
                    status_code=400,
                    detail=f"Planta inválida. Valores permitidos: {', '.join(plantas_validas)}"
                )
            update_data["planta"] = data.planta
        
        if data.capacidad is not None:
            if data.capacidad < 0:
                raise HTTPException(status_code=400, detail="La capacidad no puede ser negativa")
            update_data["capacidad"] = data.capacidad
        
        if data.tipo_aula is not None:
            update_data["tipo_aula"] = data.tipo_aula
        
        if data.equipamiento is not None:
            update_data["equipamiento"] = data.equipamiento
        
        if data.disponible is not None:
            update_data["disponible"] = data.disponible
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        await asyncio.to_thread(
            lambda: supabase.table("aulas").update(update_data).eq("id_aula", id_aula).execute()
        )
        
        return {"success": True, "mensaje": "Aula actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar aula: {str(e)}")


@router.patch("/aulas/{id_aula}/toggle-disponibilidad")
async def toggle_disponibilidad_aula(id_aula: int):
    """
    Alternar disponibilidad de un aula (útil para mantenimiento)
    """
    try:
        supabase = get_supabase_client()
        
        # Obtener estado actual
        response = await asyncio.to_thread(
            lambda: supabase.table("aulas").select("disponible").eq("id_aula", id_aula).execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Aula no encontrada")
        
        aula = response.data[0]
        nuevo_estado = not aula["disponible"]
        
        await asyncio.to_thread(
            lambda: supabase.table("aulas").update({"disponible": nuevo_estado}).eq("id_aula", id_aula).execute()
        )
        
        return {
            "success": True,
            "disponible": nuevo_estado,
            "mensaje": f"Aula {'habilitada' if nuevo_estado else 'deshabilitada'} correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar disponibilidad: {str(e)}")


@router.delete("/aulas/{id_aula}")
async def delete_aula(id_aula: int):
    """
    Eliminar un aula
    NOTA: Fallará si hay eventos asociados (por foreign key)
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar si hay eventos asociados
        eventos_response = await asyncio.to_thread(
            lambda: supabase.table("eventos").select("id_event", count="exact").eq("id_aula", id_aula).execute()
        )
        
        if eventos_response.count and eventos_response.count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede eliminar el aula porque tiene {eventos_response.count} evento(s) asociado(s). Elimina los eventos primero."
            )
        
        # Verificar que el aula existe
        aula_response = await asyncio.to_thread(
            lambda: supabase.table("aulas").select("id_aula").eq("id_aula", id_aula).execute()
        )
        
        if not aula_response.data:
            raise HTTPException(status_code=404, detail="Aula no encontrada")
        
        # Eliminar aula
        await asyncio.to_thread(
            lambda: supabase.table("aulas").delete().eq("id_aula", id_aula).execute()
        )
        
        return {"success": True, "mensaje": "Aula eliminada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar aula: {str(e)}")


@router.get("/aulas/{id_aula}/eventos")
async def get_eventos_by_aula(id_aula: int):
    """
    Obtener todos los eventos programados para un aula
    Útil para ver la disponibilidad del aula
    """
    try:
        supabase = get_supabase_client()
        
        response = await asyncio.to_thread(
            lambda: supabase.table("eventos").select("""
                id_event, name_event, timedate_event, timedate_end,
                status_event, capacidad_esperada, prioridad,
                profesor(nombre_profe),
                usuarios(name_user, email_user)
            """).eq("id_aula", id_aula).order("timedate_event", desc=False).execute()
        )
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos del aula: {str(e)}")
