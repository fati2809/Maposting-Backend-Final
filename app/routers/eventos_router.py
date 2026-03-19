from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
import asyncio

router = APIRouter()

class EventoCreate(BaseModel):
    name_event: str
    id_building: Optional[int] = None
    timedate_event: Optional[datetime] = None
    timedate_end: Optional[datetime] = None
    id_profe: Optional[int] = None
    id_user: Optional[UUID] = None
    descrip_event: Optional[str] = None
    img_event: Optional[str] = None
    id_aula: Optional[int] = None
    capacidad_esperada: Optional[int] = 0
    prioridad: Optional[int] = 1

class EventoUpdate(BaseModel):
    name_event: Optional[str] = None
    id_building: Optional[int] = None
    timedate_event: Optional[datetime] = None
    timedate_end: Optional[datetime] = None
    id_profe: Optional[int] = None
    id_user: Optional[UUID] = None
    descrip_event: Optional[str] = None
    img_event: Optional[str] = None
    id_aula: Optional[int] = None
    capacidad_esperada: Optional[int] = None
    prioridad: Optional[int] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def hay_traslape(ini1: str, fin1: str, ini2: str, fin2: str) -> bool:
    a_ini = datetime.fromisoformat(ini1)
    a_fin = datetime.fromisoformat(fin1)
    b_ini = datetime.fromisoformat(ini2)
    b_fin = datetime.fromisoformat(fin2)
    return a_ini < b_fin and b_ini < a_fin


async def reasignar_evento_menor(supabase, evento: dict, capacidad_necesaria: int) -> dict:
    ini = evento["timedate_event"]
    fin = evento["timedate_end"]
    edificio_actual = evento["id_building"]

    edificios_resp = await asyncio.to_thread(
        lambda: supabase.table("edificios").select("*").neq("id_building", edificio_actual).execute()
    )
    edificios = edificios_resp.data or []

    if not edificios:
        return {"reasignado": False, "motivo": "No hay otros edificios registrados"}

    eventos_resp = await asyncio.to_thread(
        lambda: supabase.table("eventos")
            .select("id_building, timedate_event, timedate_end")
            .neq("id_event", evento["id_event"])
            .eq("status_event", 1)
            .execute()
    )
    eventos_existentes = eventos_resp.data or []

    edificios_ocupados = set()
    for ev in eventos_existentes:
        if ev.get("timedate_event") and ev.get("timedate_end"):
            if hay_traslape(ini, fin, ev["timedate_event"], ev["timedate_end"]):
                if ev["id_building"]:
                    edificios_ocupados.add(ev["id_building"])

    edificios_libres = [e for e in edificios if e["id_building"] not in edificios_ocupados]
    candidatos = edificios_libres if edificios_libres else edificios

    def cap(e):
        return e.get("capacidad_building") or e.get("capacidad") or 0

    con_capacidad = [e for e in candidatos if cap(e) >= capacidad_necesaria]
    elegido = con_capacidad[0] if con_capacidad else sorted(candidatos, key=cap, reverse=True)[0]

    await asyncio.to_thread(
        lambda: supabase.table("eventos")
            .update({"id_building": elegido["id_building"]})
            .eq("id_event", evento["id_event"])
            .execute()
    )

    return {
        "reasignado": True,
        "evento_movido": evento["name_event"],
        "edificio_anterior": edificio_actual,
        "edificio_nuevo": elegido["id_building"],
        "nombre_edificio_nuevo": elegido.get("name_building", f"Edificio {elegido['id_building']}"),
        "tenia_capacidad_suficiente": bool(con_capacidad),
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/eventos")
async def get_eventos():
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .select("*")
                .order("timedate_event", desc=False)
                .execute()
        )
        eventos = response.data or []
        for e in eventos:
            if e.get("timedate_event"):
                e["timedate_event"] = str(e["timedate_event"])
            if e.get("timedate_end"):
                e["timedate_end"] = str(e["timedate_end"])
        return eventos
    except Exception as e:
        raise HTTPException(500, f"Error al obtener eventos: {e}")


@router.get("/aulas")
async def get_aulas():
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("aulas")
                .select("id_aula, nombre_aula, codigo_aula, id_building, planta, capacidad, tipo_aula, disponible")
                .eq("disponible", True)
                .order("nombre_aula")
                .execute()
        )
        return response.data or []
    except Exception as e:
        raise HTTPException(500, f"Error al obtener aulas: {e}")


@router.post("/eventos")
async def create_evento(data: EventoCreate):
    try:
        supabase = get_supabase_client()

        # Validación de fechas
        if data.timedate_event and data.timedate_end:
            if data.timedate_end <= data.timedate_event:
                raise HTTPException(422, "La fecha/hora de fin debe ser posterior a la de inicio")

        # Validar capacidad contra aula
        if data.id_aula and data.capacidad_esperada and data.capacidad_esperada > 0:
            aula = await asyncio.to_thread(
                lambda: supabase.table("aulas").select("capacidad").eq("id_aula", data.id_aula).limit(1).execute()
            )
            if aula.data and data.capacidad_esperada > aula.data[0]["capacidad"]:
                raise HTTPException(422, f"Capacidad esperada ({data.capacidad_esperada}) excede capacidad del aula ({aula.data[0]['capacidad']})")

        # ── Reasignación por prioridad ─────────────────────────────────────────
        reasignaciones = []
        if data.id_building and data.timedate_event and data.timedate_end and data.prioridad:
            ini = data.timedate_event.isoformat()
            fin = data.timedate_end.isoformat()

            eventos_edificio = await asyncio.to_thread(
                lambda: supabase.table("eventos")
                    .select("*")
                    .eq("id_building", data.id_building)
                    .eq("status_event", 1)
                    .execute()
            )

            for ev in (eventos_edificio.data or []):
                ev_ini = ev.get("timedate_event")
                ev_fin = ev.get("timedate_end")
                if ev_ini and ev_fin and hay_traslape(ini, fin, ev_ini, ev_fin):
                    if ev.get("prioridad", 1) < data.prioridad:
                        resultado = await reasignar_evento_menor(supabase, ev, ev.get("capacidad_esperada", 0))
                        reasignaciones.append(resultado)
        # ──────────────────────────────────────────────────────────────────────

        evento_data = {
            "name_event": data.name_event,
            "id_building": data.id_building,
            "timedate_event": data.timedate_event.isoformat() if data.timedate_event else None,
            "timedate_end": data.timedate_end.isoformat() if data.timedate_end else None,
            "status_event": 1,
            "id_profe": data.id_profe,
            "id_user": str(data.id_user) if data.id_user else None,
            "descrip_event": data.descrip_event,
            "img_event": data.img_event,
            "id_aula": data.id_aula,
            "capacidad_esperada": data.capacidad_esperada,
            "prioridad": data.prioridad,
        }

        response = await asyncio.to_thread(
            lambda: supabase.table("eventos").insert(evento_data).execute()
        )
        if not response.data:
            raise HTTPException(500, "No se pudo crear el evento")

        return {
            "success": True,
            "id_event": response.data[0]["id_event"],
            "mensaje": "Evento creado correctamente",
            "reasignaciones": reasignaciones,
        }
    except Exception as e:
        raise HTTPException(500, f"Error al crear evento: {str(e)}")


@router.put("/eventos/{id_event}")
async def update_evento(id_event: int, data: EventoUpdate):
    try:
        supabase = get_supabase_client()

        current = await asyncio.to_thread(
            lambda: supabase.table("eventos").select("*").eq("id_event", id_event).limit(1).execute()
        )
        if not current.data:
            raise HTTPException(404, "Evento no encontrado")

        update_data = {}
        if data.name_event is not None:       update_data["name_event"] = data.name_event
        if data.id_building is not None:      update_data["id_building"] = data.id_building
        if data.timedate_event is not None:   update_data["timedate_event"] = data.timedate_event.isoformat()
        if data.timedate_end is not None:     update_data["timedate_end"] = data.timedate_end.isoformat()
        if data.id_profe is not None:         update_data["id_profe"] = data.id_profe
        if data.id_user is not None:          update_data["id_user"] = str(data.id_user)
        if data.descrip_event is not None:    update_data["descrip_event"] = data.descrip_event
        if data.img_event is not None:        update_data["img_event"] = data.img_event
        if data.id_aula is not None:          update_data["id_aula"] = data.id_aula
        if data.capacidad_esperada is not None: update_data["capacidad_esperada"] = data.capacidad_esperada
        if data.prioridad is not None:        update_data["prioridad"] = data.prioridad

        if not update_data:
            raise HTTPException(400, "No hay campos para actualizar")

        # Validar capacidad contra aula
        if "id_aula" in update_data or "capacidad_esperada" in update_data:
            target_aula = update_data.get("id_aula", current.data[0].get("id_aula"))
            target_cap  = update_data.get("capacidad_esperada", current.data[0].get("capacidad_esperada"))
            if target_aula and target_cap and target_cap > 0:
                aula = await asyncio.to_thread(
                    lambda: supabase.table("aulas").select("capacidad").eq("id_aula", target_aula).limit(1).execute()
                )
                if aula.data and target_cap > aula.data[0]["capacidad"]:
                    raise HTTPException(422, "Capacidad esperada excede capacidad del aula")

        await asyncio.to_thread(
            lambda: supabase.table("eventos").update(update_data).eq("id_event", id_event).execute()
        )
        return {"success": True, "mensaje": "Evento actualizado correctamente"}
    except Exception as e:
        raise HTTPException(500, f"Error al actualizar evento: {str(e)}")


@router.patch("/eventos/{id_event}/toggle-status")
async def toggle_status_evento(id_event: int):
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("eventos").select("status_event").eq("id_event", id_event).execute()
        )
        if not response.data:
            raise HTTPException(404, "Evento no encontrado")
        evento = response.data[0]
        nuevo_status = 0 if evento["status_event"] == 1 else 1
        await asyncio.to_thread(
            lambda: supabase.table("eventos").update({"status_event": nuevo_status}).eq("id_event", id_event).execute()
        )
        return {"success": True, "nuevo_status": nuevo_status}
    except Exception as e:
        raise HTTPException(500, f"Error al cambiar estado: {str(e)}")


@router.delete("/eventos/{id_event}")
async def delete_evento(id_event: int):
    try:
        supabase = get_supabase_client()
        await asyncio.to_thread(
            lambda: supabase.table("eventos").delete().eq("id_event", id_event).execute()
        )
        return {"success": True, "mensaje": "Evento eliminado correctamente"}
    except Exception as e:
        raise HTTPException(500, f"Error al eliminar evento: {str(e)}")


@router.get("/profesores")
async def get_profesores():
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("profesor").select("id_profe, nombre_profe").order("nombre_profe").execute()
        )
        return response.data
    except Exception as e:
        raise HTTPException(500, f"Error al obtener profesores: {str(e)}")