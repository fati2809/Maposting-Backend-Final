from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
import asyncio

from app.utils.email_service import enviar_invitacion

router = APIRouter()

class EventoCreate(BaseModel):
    name_event: str
    id_building: Optional[int] = None
    timedate_event: Optional[datetime] = None
    timedate_end: Optional[datetime] = None
    id_profe: Optional[int] = None
    id_user: Optional[UUID] = None
    id_user_profe: Optional[str] = None  # 👈 nuevo: para profesores locales
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


def hay_traslape(ini1: str, fin1: str, ini2: str, fin2: str) -> bool:
    a_ini = datetime.fromisoformat(ini1)
    a_fin = datetime.fromisoformat(fin1)
    b_ini = datetime.fromisoformat(ini2)
    b_fin = datetime.fromisoformat(fin2)
    return a_ini < b_fin and b_ini < a_fin


async def get_email_profesor(supabase, id_profe: int) -> tuple[str | None, str | None]:
    resp = await asyncio.to_thread(
        lambda: supabase.table("profesor")
            .select("nombre_profe, id_user, usuarios(email_user)")
            .eq("id_profe", id_profe)
            .limit(1)
            .execute()
    )
    if not resp.data:
        return None, None
    profe  = resp.data[0]
    nombre = profe.get("nombre_profe")
    email  = None
    if profe.get("usuarios") and profe["usuarios"].get("email_user"):
        email = profe["usuarios"]["email_user"]
    return nombre, email


async def get_email_por_id_user(supabase, id_user: str) -> tuple[str | None, str | None]:
    """Busca nombre y email directamente en usuarios por id_user."""
    resp = await asyncio.to_thread(
        lambda: supabase.table("usuarios")
            .select("name_user, email_user")
            .eq("id_user", id_user)
            .limit(1)
            .execute()
    )
    if not resp.data:
        return None, None
    return resp.data[0]["name_user"], resp.data[0]["email_user"]


async def reasignar_evento_menor(supabase, evento: dict, capacidad_necesaria: int) -> dict:
    ini             = evento["timedate_event"]
    fin             = evento["timedate_end"]
    edificio_actual = evento["id_building"]

    edificios_resp = await asyncio.to_thread(
        lambda: supabase.table("edificios")
            .select("*")
            .neq("id_building", edificio_actual)
            .execute()
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
    candidatos       = edificios_libres if edificios_libres else edificios

    def cap(e):
        return e.get("capacidad_building") or e.get("capacidad") or 0

    con_capacidad = [e for e in candidatos if cap(e) >= capacidad_necesaria]
    elegido       = con_capacidad[0] if con_capacidad else sorted(candidatos, key=cap, reverse=True)[0]

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


@router.get("/eventos")
async def get_eventos():
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .select("""
                    *,
                    edificios!eventos_id_building_fkey(name_building),
                    aulas!eventos_id_aula_fkey(nombre_aula, planta, capacidad),
                    profesor!eventos_id_profe_fkey(nombre_profe)
                """)
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

        if data.timedate_event and data.timedate_end:
            if data.timedate_end <= data.timedate_event:
                raise HTTPException(422, "La fecha/hora de fin debe ser posterior a la de inicio")

        if data.id_aula and data.capacidad_esperada and data.capacidad_esperada > 0:
            aula = await asyncio.to_thread(
                lambda: supabase.table("aulas")
                    .select("capacidad")
                    .eq("id_aula", data.id_aula)
                    .limit(1)
                    .execute()
            )
            if aula.data and data.capacidad_esperada > aula.data[0]["capacidad"]:
                raise HTTPException(422, f"Capacidad esperada ({data.capacidad_esperada}) excede capacidad del aula ({aula.data[0]['capacidad']})")

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

        evento_data = {
            "name_event":         data.name_event,
            "id_building":        data.id_building,
            "timedate_event":     data.timedate_event.isoformat() if data.timedate_event else None,
            "timedate_end":       data.timedate_end.isoformat()   if data.timedate_end   else None,
            "status_event":       1,
            "id_profe":           data.id_profe,
            "id_user":            str(data.id_user) if data.id_user else None,
            "descrip_event":      data.descrip_event,
            "img_event":          data.img_event,
            "id_aula":            data.id_aula,
            "capacidad_esperada": data.capacidad_esperada,
            "prioridad":          data.prioridad,
        }

        response = await asyncio.to_thread(
            lambda: supabase.table("eventos").insert(evento_data).execute()
        )
        if not response.data:
            raise HTTPException(500, "No se pudo crear el evento")

        nuevo_evento = response.data[0]

        # ── Email: soporta tanto id_profe como id_user_profe (local) ──────────
        email_enviado = False
        if data.timedate_event and data.timedate_end:
            nombre_profe, email_profe = None, None

            if data.id_profe:
                nombre_profe, email_profe = await get_email_profesor(supabase, data.id_profe)
            elif data.id_user_profe:  # 👈 profesor local (Yanny, etc.)
                nombre_profe, email_profe = await get_email_por_id_user(supabase, data.id_user_profe)

            if email_profe:
                nombre_edificio = "Sin edificio"
                if data.id_building:
                    ed_resp = await asyncio.to_thread(
                        lambda: supabase.table("edificios")
                            .select("name_building")
                            .eq("id_building", data.id_building)
                            .limit(1)
                            .execute()
                    )
                    if ed_resp.data:
                        nombre_edificio = ed_resp.data[0]["name_building"]

                asyncio.create_task(
                    asyncio.to_thread(
                        enviar_invitacion,
                        email_profe,
                        nombre_profe,
                        data.name_event,
                        data.descrip_event or "",
                        nombre_edificio,
                        data.timedate_event,
                        data.timedate_end,
                    )
                )
                email_enviado = True

        return {
            "success":        True,
            "id_event":       nuevo_evento["id_event"],
            "mensaje":        "Evento creado correctamente",
            "reasignaciones": reasignaciones,
            "email_enviado":  email_enviado,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al crear evento: {str(e)}")


@router.put("/eventos/{id_event}")
async def update_evento(id_event: int, data: EventoUpdate):
    try:
        supabase = get_supabase_client()

        current = await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .select("*")
                .eq("id_event", id_event)  # 👈 fix: quitada la 'a' suelta
                .limit(1)
                .execute()
        )
        if not current.data:
            raise HTTPException(404, "Evento no encontrado")

        update_data = {}
        if data.name_event is not None:         update_data["name_event"]         = data.name_event
        if data.id_building is not None:        update_data["id_building"]        = data.id_building
        if data.timedate_event is not None:     update_data["timedate_event"]     = data.timedate_event.isoformat()
        if data.timedate_end is not None:       update_data["timedate_end"]       = data.timedate_end.isoformat()
        if data.id_profe is not None:           update_data["id_profe"]           = data.id_profe
        if data.id_user is not None:            update_data["id_user"]            = str(data.id_user)
        if data.descrip_event is not None:      update_data["descrip_event"]      = data.descrip_event
        if data.img_event is not None:          update_data["img_event"]          = data.img_event
        if data.id_aula is not None:            update_data["id_aula"]            = data.id_aula
        if data.capacidad_esperada is not None: update_data["capacidad_esperada"] = data.capacidad_esperada
        if data.prioridad is not None:          update_data["prioridad"]          = data.prioridad

        if not update_data:
            raise HTTPException(400, "No hay campos para actualizar")

        if "id_aula" in update_data or "capacidad_esperada" in update_data:
            target_aula = update_data.get("id_aula", current.data[0].get("id_aula"))
            target_cap  = update_data.get("capacidad_esperada", current.data[0].get("capacidad_esperada"))
            if target_aula and target_cap and target_cap > 0:
                aula = await asyncio.to_thread(
                    lambda: supabase.table("aulas")
                        .select("capacidad")
                        .eq("id_aula", target_aula)
                        .limit(1)
                        .execute()
                )
                if aula.data and target_cap > aula.data[0]["capacidad"]:
                    raise HTTPException(422, "Capacidad esperada excede capacidad del aula")

        await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .update(update_data)
                .eq("id_event", id_event)
                .execute()
        )
        return {"success": True, "mensaje": "Evento actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al actualizar evento: {str(e)}")


@router.patch("/eventos/{id_event}/toggle-status")
async def toggle_status_evento(id_event: int):
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .select("status_event")
                .eq("id_event", id_event)
                .execute()
        )
        if not response.data:
            raise HTTPException(404, "Evento no encontrado")
        nuevo_status = 0 if response.data[0]["status_event"] == 1 else 1
        await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .update({"status_event": nuevo_status})
                .eq("id_event", id_event)
                .execute()
        )
        return {"success": True, "nuevo_status": nuevo_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al cambiar estado: {str(e)}")


@router.delete("/eventos/{id_event}")
async def delete_evento(id_event: int):
    try:
        supabase = get_supabase_client()
        await asyncio.to_thread(
            lambda: supabase.table("eventos")
                .delete()
                .eq("id_event", id_event)
                .execute()
        )
        return {"success": True, "mensaje": "Evento eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al eliminar evento: {str(e)}")


@router.get("/profesores")
async def get_profesores():
    try:
        supabase = get_supabase_client()
        response = await asyncio.to_thread(
            lambda: supabase.table("profesor")
                .select("id_profe, nombre_profe, id_user, usuarios(email_user)")
                .order("nombre_profe")
                .execute()
        )
        result = []
        for p in (response.data or []):
            result.append({
                "id_profe":     p["id_profe"],
                "nombre_profe": p["nombre_profe"],
                "id_user":      p.get("id_user"),
                "email_profe":  p["usuarios"]["email_user"] if p.get("usuarios") else None,
            })
        return result
    except Exception as e:
        raise HTTPException(500, f"Error al obtener profesores: {str(e)}")


@router.patch("/profesores/{id_profe}/vincular-usuario")
async def vincular_usuario_profesor(id_profe: int, body: dict):
    try:
        supabase = get_supabase_client()
        id_user  = body.get("id_user")
        if not id_user:
            raise HTTPException(400, "id_user es requerido")

        user_resp = await asyncio.to_thread(
            lambda: supabase.table("usuarios")
                .select("id_user, name_user, email_user")
                .eq("id_user", id_user)
                .limit(1)
                .execute()
        )
        if not user_resp.data:
            raise HTTPException(404, "Usuario no encontrado")

        resp = await asyncio.to_thread(
            lambda: supabase.table("profesor")
                .update({"id_user": id_user})
                .eq("id_profe", id_profe)
                .execute()
        )
        if not resp.data:
            raise HTTPException(404, "Profesor no encontrado")

        return {
            "success":         True,
            "email_vinculado": user_resp.data[0]["email_user"],
            "nombre_user":     user_resp.data[0]["name_user"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al vincular usuario: {str(e)}")