from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
import asyncio
import httpx
from difflib import SequenceMatcher

router = APIRouter()

def similitud(a: str, b: str) -> float:
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()

@router.get("/profesoresf")
async def get_profesores():
    try:
        supabase = get_supabase_client()

        response = supabase.table("profesor").select("""
            id_profe,
            nombre_profe,
            planta_profe,
            id_building,
            id_division,
            edificios(name_building),
            divisiones(name_div)
        """).order("id_profe").execute()

        data = []

        for row in response.data:
            profesor = {
                "id_profe": row["id_profe"],
                "nombre_profe": row["nombre_profe"],
                "planta_profe": row.get("planta_profe"),
                "id_building": row.get("id_building"),
                "id_division": row.get("id_division"),
                "name_building": row["edificios"]["name_building"] if row.get("edificios") else None,
                "name_div": row["divisiones"]["name_div"] if row.get("divisiones") else None
            }

            data.append(profesor)

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/profesoresf/{id_profe}/horario")
async def get_horario_profesor(id_profe: int):
    try:
        supabase = get_supabase_client()

        result = await asyncio.to_thread(
            lambda: supabase.table("profesor")
                .select("id_profe, nombre_profe, planta_profe, id_building")
                .eq("id_profe", id_profe)
                .single()
                .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")

        profesor = result.data
        nombre_local = profesor["nombre_profe"]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://horarios-backend-58w8.onrender.com/horarios",
                timeout=15.0
            )
            horarios_raw = response.json()

        profs: dict = {}
        for grupo in horarios_raw:
            for clase in grupo["data"]:
                nombre_ext = clase["prof"]
                if nombre_ext not in profs:
                    profs[nombre_ext] = []
                profs[nombre_ext].append({
                    "materia": clase["subj"],
                    "salon": clase["room"],
                    "grupo": clase["group"],
                    "horario": clase["start"],
                })

        UMBRAL = 0.75
        mejor_match = None
        mejor_score = 0.0

        for nombre_ext in profs:
            score = similitud(nombre_local, nombre_ext)
            if score > mejor_score:
                mejor_score = score
                mejor_match = nombre_ext

        clases = profs[mejor_match] if mejor_match and mejor_score >= UMBRAL else []

        return {
            "id_profe": profesor["id_profe"],
            "nombre_profe": profesor["nombre_profe"],
            "horario": clases
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/profesoresf/edificio/{id_building}")
async def get_profesores_by_edificio(id_building: int):
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("profesor")
                .select("id_profe, nombre_profe, planta_profe, id_building")
                .eq("id_building", id_building)
                .execute()
        )
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")