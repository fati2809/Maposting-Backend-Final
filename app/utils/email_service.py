import requests
import uuid
import os
from datetime import datetime


def fmt_ical(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def enviar_invitacion(
    email_destino: str,
    nombre_profe: str,
    nombre_evento: str,
    descripcion: str,
    nombre_edificio: str,
    fecha_inicio: datetime,
    fecha_fin: datetime,
) -> bool:

    print("📨 Enviando correo con Resend...")

    try:
        # ============================
        # 📅 ICS (calendario)
        # ============================
        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SistemaEventos//ES
METHOD:REQUEST
BEGIN:VEVENT
UID:{uuid.uuid4()}
DTSTAMP:{fmt_ical(datetime.utcnow())}
DTSTART:{fmt_ical(fecha_inicio)}
DTEND:{fmt_ical(fecha_fin)}
SUMMARY:{nombre_evento}
DESCRIPTION:{descripcion or 'Sin descripcion'}
LOCATION:{nombre_edificio}
ORGANIZER:mailto:events@tudominio.com
ATTENDEE:mailto:{email_destino}
END:VEVENT
END:VCALENDAR
"""

        # ============================
        # 📨 HTML bonito
        # ============================
        html = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:auto;
                    border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
          <div style="background:#6433b4;padding:24px 28px">
            <h2 style="color:#fff;margin:0">📅 {nombre_evento}</h2>
          </div>
          <div style="padding:24px 28px">
            <p>Hola <strong>{nombre_profe}</strong>,</p>
            <p>Has sido asignado a un nuevo evento.</p>
            <p><b>📍 Lugar:</b> {nombre_edificio}</p>
            <p><b>🕐 Inicio:</b> {fecha_inicio.strftime('%d/%m/%Y %H:%M')}</p>
            <p><b>🕐 Fin:</b> {fecha_fin.strftime('%d/%m/%Y %H:%M')}</p>
            <p>{descripcion or 'Sin descripción'}</p>
          </div>
        </div>
        """

        # ============================
        # 🚀 ENVÍO CON RESEND
        # ============================
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "from": "onboarding@resend.dev",  # luego puedes cambiarlo
                "to": [email_destino],
                "subject": f"📅 Invitación: {nombre_evento}",
                "html": html,
                "attachments": [
                    {
                        "filename": "invitacion.ics",
                        "content": ical
                    }
                ]
            }
        )

        print("📬 Respuesta:", response.json())

        if response.status_code in [200, 201]:
            print(f"✅ Email enviado a {email_destino}")
            return True
        else:
            print("❌ Error en Resend:", response.text)
            return False

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error enviando email: {e}")
        return False
