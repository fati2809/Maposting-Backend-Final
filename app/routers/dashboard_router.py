from fastapi import APIRouter, HTTPException
from app.config import get_supabase_client
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/dashboard/stats")
async def get_stats():
    try:
        supabase = get_supabase_client()
        
        # Total usuarios
        usuarios_response = supabase.table("usuarios").select("id_user", count="exact").execute()
        total_usuarios = usuarios_response.count if usuarios_response.count else 0
        
        # Total eventos
        eventos_response = supabase.table("eventos").select("id_event", count="exact").execute()
        total_eventos = eventos_response.count if eventos_response.count else 0
        
        return {
            "total_usuarios": total_usuarios,
            "total_eventos": total_eventos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/dashboard/grafica")
async def get_grafica(periodo: str = "semana"):
    try:
        supabase = get_supabase_client()
        now = datetime.now(timezone.utc)

        periodo_limpio = periodo.split(":")[0]

        if periodo_limpio == "dia":
            fecha_inicio = now - timedelta(hours=24)
        elif periodo_limpio == "semana":
            fecha_inicio = now - timedelta(days=7)
        else:
            fecha_inicio = now - timedelta(days=30)

        eventos_response = (
            supabase.table("eventos")
            .select("timedate_event")
            .gte("timedate_event", fecha_inicio.isoformat())
            .execute()
        )

        eventos_dict = {}
        for evento in eventos_response.data:
            if evento.get("timedate_event"):
                dt = datetime.fromisoformat(evento["timedate_event"].replace("Z", "+00:00"))
                if periodo_limpio == "dia":
                    label = dt.strftime("%H:00")
                elif periodo_limpio == "semana":
                    label = dt.strftime("%a")
                else:
                    label = dt.strftime("%d/%m")
                eventos_dict[label] = eventos_dict.get(label, 0) + 1

        labels_completos = {}

        if periodo_limpio == "dia":
            for i in range(24):
                hora = (fecha_inicio + timedelta(hours=i)).strftime("%H:00")
                labels_completos[hora] = eventos_dict.get(hora, 0)

        elif periodo_limpio == "semana":
            for i in range(7):
                dia = (fecha_inicio + timedelta(days=i)).strftime("%a")
                labels_completos[dia] = eventos_dict.get(dia, 0)

        else:  
            for i in range(30):
                dia = (fecha_inicio + timedelta(days=i)).strftime("%d/%m")
                labels_completos[dia] = eventos_dict.get(dia, 0)

        eventos = [{"label": k, "eventos": v} for k, v in labels_completos.items()]

        return {
            "periodo": periodo_limpio,
            "eventos": eventos,
            "usuarios": [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/dashboard/reporte")
async def get_reporte():
    try:
        supabase = get_supabase_client()
        
        # Obtener usuarios con roles
        usuarios_response = supabase.table("usuarios").select("""
            name_user, email_user, matricula_user,
            rol!inner(name_rol)
        """).order("id_user").execute()
        
        usuarios = []
        for u in usuarios_response.data:
            usuarios.append({
                "name_user": u["name_user"],
                "email_user": u["email_user"],
                "matricula_user": u.get("matricula_user"),
                "rol": u["rol"]["name_rol"] if isinstance(u.get("rol"), dict) else ""
            })
        
        # Obtener eventos con relaciones
        eventos_response = supabase.table("eventos").select("""
                name_event, timedate_event, status_event, id_building, id_profe,
                edificios!eventos_id_building_fkey(name_building),
                profesor!eventos_id_profe_fkey(nombre_profe)
            """).order("timedate_event", desc=True).execute()
        
        eventos = []
        for e in eventos_response.data:
            eventos.append({
                "name_event": e["name_event"],
                "name_building": e["edificios"]["name_building"] if e.get("edificios") else None,
                "timedate_event": e.get("timedate_event"),
                "nombre_profe": e["profesor"]["nombre_profe"] if e.get("profesor") else None,
                "status_event": e.get("status_event")
            })
        
        return {"usuarios": usuarios, "eventos": eventos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")