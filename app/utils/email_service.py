import requests
import os
import base64
import uuid
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

    print("📨 Enviando correo con SendGrid...")

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
ORGANIZER:mailto:lopez.uribe.fatima@gmail.com
ATTENDEE:mailto:{email_destino}
END:VEVENT
END:VCALENDAR
"""

        ical_base64 = base64.b64encode(ical.encode()).decode()

        # ============================
        # 📨 HTML
        # ============================
        html = f"""
        <div style="font-family:sans-serif">
            <h2>📅 {nombre_evento}</h2>
            <p>Hola <b>{nombre_profe}</b>,</p>
            <p>Tienes un nuevo evento asignado:</p>
            <ul>
                <li><b>📍 Lugar:</b> {nombre_edificio}</li>
                <li><b>🕐 Inicio:</b> {fecha_inicio.strftime('%d/%m/%Y %H:%M')}</li>
                <li><b>🕐 Fin:</b> {fecha_fin.strftime('%d/%m/%Y %H:%M')}</li>
                <li><b>📝 Descripción:</b> {descripcion or 'Sin descripción'}</li>
            </ul>
            <p>📎 Se adjunta invitación (.ics)</p>
        </div>
        """

        # ============================
        # 🚀 SENDGRID REQUEST
        # ============================
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "personalizations": [
                    {
                        "to": [{"email": email_destino}]
                    }
                ],
                "from": {
                    "email": "lopez.uribe.fatima@gmail.com"  # ⚠️ debe ser el verificado
                },
                "subject": f"📅 Invitación: {nombre_evento}",
                "content": [
                    {
                        "type": "text/html",
                        "value": html
                    }
                ],
                "attachments": [
                    {
                        "content": ical_base64,
                        "type": "text/calendar",
                        "filename": "invitacion.ics"
                    }
                ]
            }
        )

        print("STATUS:", response.status_code)
        print("BODY:", response.text)

        if response.status_code in [200, 202]:
            print(f"✅ Email enviado a {email_destino}")
            return True
        else:
            print("❌ Error:", response.text)
            return False

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error enviando email: {e}")
        return False
