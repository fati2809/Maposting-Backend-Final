from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from app.models.models import HorarioProfesorCreate, HorarioProfesorUpdate, HorarioProfesorResponse
from typing import List, Optional

router = APIRouter()

# ============================
# 📋 GET ALL HORARIOS
# ============================
@router.get("/horarios-profesor", response_model=List[dict])
async def get_horarios_profesor(id_profe: Optional[int] = None, dia_semana: Optional[str] = None):
    """
    Obtener todos los horarios de profesores con filtros opcionales
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("horarios_profesor").select("""
            id_horario, id_profe, dia_semana, hora_inicio, hora_fin, 
            id_building, aula,
            profesor(nombre_profe, id_division),
            edificios(name_building, code_building)
        """)
        
        if id_profe:
            query = query.eq("id_profe", id_profe)
        if dia_semana:
            query = query.eq("dia_semana", dia_semana)
        
        response = query.order("id_profe").order("dia_semana").order("hora_inicio").execute()
        
        horarios = []
        for item in response.data:
            horario = {
                "id_horario": item["id_horario"],
                "id_profe": item["id_profe"],
                "dia_semana": item["dia_semana"],
                "hora_inicio": str(item["hora_inicio"]) if item.get("hora_inicio") else None,
                "hora_fin": str(item["hora_fin"]) if item.get("hora_fin") else None,
                "id_building": item.get("id_building"),
                "aula": item.get("aula"),
                "nombre_profe": item["profesor"]["nombre_profe"] if item.get("profesor") else None,
                "name_building": item["edificios"]["name_building"] if item.get("edificios") else None,
                "code_building": item["edificios"]["code_building"] if item.get("edificios") else None
            }
            horarios.append(horario)
        
        return horarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📋 GET HORARIO BY ID
# ============================
@router.get("/horarios-profesor/{id_horario}")
async def get_horario_profesor(id_horario: int):
    try:
        supabase = get_supabase_client()
        response = supabase.table("horarios_profesor").select("""
            id_horario, id_profe, dia_semana, hora_inicio, hora_fin, 
            id_building, aula,
            profesor(nombre_profe, id_division, planta_profe),
            edificios(name_building, code_building)
        """).eq("id_horario", id_horario).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Horario no encontrado")
        
        item = response.data[0]
        return {
            "id_horario": item["id_horario"],
            "id_profe": item["id_profe"],
            "dia_semana": item["dia_semana"],
            "hora_inicio": str(item["hora_inicio"]) if item.get("hora_inicio") else None,
            "hora_fin": str(item["hora_fin"]) if item.get("hora_fin") else None,
            "id_building": item.get("id_building"),
            "aula": item.get("aula"),
            "profesor": item.get("profesor"),
            "edificio": item.get("edificios")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ➕ CREATE HORARIO
# ============================
@router.post("/horarios-profesor")
async def create_horario_profesor(data: HorarioProfesorCreate):
    try:
        supabase = get_supabase_client()
        
        # Verificar que el profesor existe
        profe_check = supabase.table("profesor").select("id_profe").eq("id_profe", data.id_profe).execute()
        if not profe_check.data:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        
        # Validar día de la semana
        dias_validos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        if data.dia_semana not in dias_validos:
            raise HTTPException(status_code=400, detail=f"Día inválido. Debe ser uno de: {', '.join(dias_validos)}")
        
        # Verificar conflicto de horario (mismo profesor, mismo día, horarios solapados)
        existing = supabase.table("horarios_profesor").select("id_horario, hora_inicio, hora_fin").eq("id_profe", data.id_profe).eq("dia_semana", data.dia_semana).execute()
        
        for horario in existing.data:
            inicio_existente = horario["hora_inicio"]
            fin_existente = horario["hora_fin"]
            
            # Convertir strings a time objects si es necesario
            from datetime import time as time_type
            if isinstance(data.hora_inicio, str):
                hora_inicio = time_type.fromisoformat(data.hora_inicio)
            else:
                hora_inicio = data.hora_inicio
            
            if isinstance(data.hora_fin, str):
                hora_fin = time_type.fromisoformat(data.hora_fin)
            else:
                hora_fin = data.hora_fin
            
            # Verificar solapamiento
            if not (hora_fin <= inicio_existente or hora_inicio >= fin_existente):
                raise HTTPException(status_code=409, detail="Conflicto de horario: El profesor ya tiene clase en este horario")
        
        horario_data = {
            "id_profe": data.id_profe,
            "dia_semana": data.dia_semana,
            "hora_inicio": str(data.hora_inicio) if data.hora_inicio else None,
            "hora_fin": str(data.hora_fin) if data.hora_fin else None,
            "id_building": data.id_building,
            "aula": data.aula
        }
        
        response = supabase.table("horarios_profesor").insert(horario_data).execute()
        return {
            "success": True,
            "message": "Horario registrado correctamente",
            "id_horario": response.data[0]["id_horario"] if response.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ✏️ UPDATE HORARIO
# ============================
@router.put("/horarios-profesor/{id_horario}")
async def update_horario_profesor(id_horario: int, data: HorarioProfesorUpdate):
    try:
        supabase = get_supabase_client()
        
        # Verificar que existe
        check = supabase.table("horarios_profesor").select("id_horario, id_profe, dia_semana").eq("id_horario", id_horario).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Horario no encontrado")
        
        horario_actual = check.data[0]
        
        update_data = {}
        
        if data.dia_semana is not None:
            dias_validos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
            if data.dia_semana not in dias_validos:
                raise HTTPException(status_code=400, detail=f"Día inválido. Debe ser uno de: {', '.join(dias_validos)}")
            update_data["dia_semana"] = data.dia_semana
        
        if data.hora_inicio is not None:
            update_data["hora_inicio"] = str(data.hora_inicio)
        
        if data.hora_fin is not None:
            update_data["hora_fin"] = str(data.hora_fin)
        
        if data.id_building is not None:
            update_data["id_building"] = data.id_building
        
        if data.aula is not None:
            update_data["aula"] = data.aula
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        supabase.table("horarios_profesor").update(update_data).eq("id_horario", id_horario).execute()
        return {"success": True, "message": "Horario actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 🗑️ DELETE HORARIO
# ============================
@router.delete("/horarios-profesor/{id_horario}")
async def delete_horario_profesor(id_horario: int):
    try:
        supabase = get_supabase_client()
        
        # Verificar que existe
        check = supabase.table("horarios_profesor").select("id_horario").eq("id_horario", id_horario).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Horario no encontrado")
        
        supabase.table("horarios_profesor").delete().eq("id_horario", id_horario).execute()
        return {"success": True, "message": "Horario eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📊 GET HORARIO SEMANAL COMPLETO
# ============================
@router.get("/horarios-profesor/semanal/{id_profe}")
async def get_horario_semanal(id_profe: int):
    """
    Obtener el horario completo de la semana de un profesor
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar que el profesor existe
        profe_check = supabase.table("profesor").select("nombre_profe").eq("id_profe", id_profe).execute()
        if not profe_check.data:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        
        # Obtener todos los horarios del profesor
        horarios = supabase.table("horarios_profesor").select("""
            id_horario, dia_semana, hora_inicio, hora_fin, aula,
            edificios(name_building, code_building)
        """).eq("id_profe", id_profe).order("dia_semana").order("hora_inicio").execute()
        
        # Organizar por día
        dias_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        horario_semanal = {dia: [] for dia in dias_orden}
        
        for horario in horarios.data:
            dia = horario["dia_semana"]
            if dia in horario_semanal:
                horario_semanal[dia].append({
                    "id_horario": horario["id_horario"],
                    "hora_inicio": str(horario["hora_inicio"]) if horario.get("hora_inicio") else None,
                    "hora_fin": str(horario["hora_fin"]) if horario.get("hora_fin") else None,
                    "aula": horario.get("aula"),
                    "edificio": horario["edificios"]["name_building"] if horario.get("edificios") else None
                })
        
        return {
            "profesor": profe_check.data[0]["nombre_profe"],
            "horario_semanal": horario_semanal
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 📋 GET DISPONIBILIDAD POR DÍA
# ============================
@router.get("/horarios-profesor/disponibilidad/{dia_semana}")
async def get_disponibilidad_dia(dia_semana: str):
    """
    Obtener qué profesores están ocupados en un día específico
    """
    try:
        dias_validos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        if dia_semana not in dias_validos:
            raise HTTPException(status_code=400, detail=f"Día inválido. Debe ser uno de: {', '.join(dias_validos)}")
        
        supabase = get_supabase_client()
        
        horarios = supabase.table("horarios_profesor").select("""
            id_horario, hora_inicio, hora_fin, aula,
            profesor(nombre_profe, id_division),
            edificios(name_building)
        """).eq("dia_semana", dia_semana).order("hora_inicio").execute()
        
        return {
            "dia": dia_semana,
            "total_clases": len(horarios.data),
            "horarios": horarios.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
