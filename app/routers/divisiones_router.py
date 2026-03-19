from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class DivisionCreate(BaseModel):
    name_div: str

class DivisionUpdate(BaseModel):
    name_div: Optional[str] = None

# ============================
# 📋 GET ALL DIVISIONES
# ============================
@router.get("/divisiones-all")
async def get_divisiones_all():
    try:
        supabase = get_supabase_client()
        
        # Obtener todas las divisiones
        divisiones_response = supabase.table("divisiones").select("id_div, name_div").order("id_div").execute()
        
        result = []
        for division in divisiones_response.data:
            # Contar profesores
            profesores = supabase.table("profesor").select("id_profe", count="exact").eq("id_division", division["id_div"]).execute()
            
            # Contar edificios
            edificios = supabase.table("edificios").select("id_building", count="exact").eq("id_div", division["id_div"]).execute()
            
            result.append({
                "id_div": division["id_div"],
                "name_div": division["name_div"],
                "total_profesores": profesores.count if profesores.count else 0,
                "total_edificios": edificios.count if edificios.count else 0
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ➕ CREATE DIVISION
# ============================
@router.post("/divisiones")
async def create_division(data: DivisionCreate):
    try:
        supabase = get_supabase_client()
        response = supabase.table("divisiones").insert({"name_div": data.name_div}).execute()
        return {"success": True, "id_div": response.data[0]["id_div"] if response.data else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# ✏️ UPDATE DIVISION
# ============================
@router.put("/divisiones/{id_div}")
async def update_division(id_div: int, data: DivisionUpdate):
    try:
        if not data.name_div:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        supabase = get_supabase_client()
        supabase.table("divisiones").update({"name_div": data.name_div}).eq("id_div", id_div).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================
# 🗑️ DELETE DIVISION
# ============================
@router.delete("/divisiones/{id_div}")
async def delete_division(id_div: int):
    try:
        supabase = get_supabase_client()
        
        # Verificar si tiene profesores asociados
        profesores = supabase.table("profesor").select("id_profe", count="exact").eq("id_division", id_div).execute()
        if profesores.count and profesores.count > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar: tiene profesores asociados")
        
        # Verificar si tiene edificios asociados
        edificios = supabase.table("edificios").select("id_building", count="exact").eq("id_div", id_div).execute()
        if edificios.count and edificios.count > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar: tiene edificios asociados")
        
        supabase.table("divisiones").delete().eq("id_div", id_div).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")