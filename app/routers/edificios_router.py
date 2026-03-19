from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class EdificioCreate(BaseModel):
    name_building: str
    descrip_building: Optional[str] = None
    code_building: Optional[str] = None
    imagen_url: Optional[str] = None
    lat_building: float
    lon_building: float
    id_div: Optional[int] = None

class EdificioUpdate(BaseModel):
    name_building: Optional[str] = None
    descrip_building: Optional[str] = None
    code_building: Optional[str] = None
    imagen_url: Optional[str] = None
    lat_building: Optional[float] = None
    lon_building: Optional[float] = None
    id_div: Optional[int] = None

@router.get("/edificios")
async def get_edificios():
    try:
        supabase = get_supabase_client()
        response = supabase.table("edificios").select("""
            id_building, name_building, descrip_building, code_building,
            imagen_url, lat_building, lon_building, id_div,
            divisiones(name_div)
        """).order("id_building").execute()
        
        # Transformar para incluir name_div al mismo nivel
        data = []
        for row in response.data:
            edificio = {
                "id_building": row["id_building"],
                "name_building": row["name_building"],
                "descrip_building": row.get("descrip_building"),
                "code_building": row.get("code_building"),
                "imagen_url": row.get("imagen_url"),
                "lat_building": float(row["lat_building"]) if row.get("lat_building") else None,
                "lon_building": float(row["lon_building"]) if row.get("lon_building") else None,
                "id_div": row.get("id_div"),
                "name_div": row["divisiones"]["name_div"] if row.get("divisiones") else None
            }
            data.append(edificio)
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/edificios")
async def create_edificio(data: EdificioCreate):
    try:
        supabase = get_supabase_client()
        edificio_data = {
            "name_building": data.name_building,
            "descrip_building": data.descrip_building,
            "code_building": data.code_building,
            "imagen_url": data.imagen_url,
            "lat_building": data.lat_building,
            "lon_building": data.lon_building,
            "id_div": data.id_div
        }
        response = supabase.table("edificios").insert(edificio_data).execute()
        return {"success": True, "id_building": response.data[0]["id_building"] if response.data else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/edificios/{id_building}")
async def update_edificio(id_building: int, data: EdificioUpdate):
    try:
        supabase = get_supabase_client()
        update_data = {}
        if data.name_building is not None:
            update_data["name_building"] = data.name_building
        if data.descrip_building is not None:
            update_data["descrip_building"] = data.descrip_building
        if data.code_building is not None:
            update_data["code_building"] = data.code_building
        if data.imagen_url is not None:
            update_data["imagen_url"] = data.imagen_url
        if data.lat_building is not None:
            update_data["lat_building"] = data.lat_building
        if data.lon_building is not None:
            update_data["lon_building"] = data.lon_building
        if data.id_div is not None:
            update_data["id_div"] = data.id_div
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        supabase.table("edificios").update(update_data).eq("id_building", id_building).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.delete("/edificios/{id_building}")
async def delete_edificio(id_building: int):
    try:
        supabase = get_supabase_client()
        supabase.table("edificios").delete().eq("id_building", id_building).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")