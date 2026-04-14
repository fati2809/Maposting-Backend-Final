import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

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
     print("📨 Intentando enviar correo...")
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️  SMTP no configurado, omitiendo envío de email")
        return False
    try:
        ical = f"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//SistemaEventos//ES\r
METHOD:REQUEST\r
BEGIN:VEVENT\r
UID:{uuid.uuid4()}\r
DTSTAMP:{fmt_ical(datetime.utcnow())}\r
DTSTART:{fmt_ical(fecha_inicio)}\r
DTEND:{fmt_ical(fecha_fin)}\r
SUMMARY:{nombre_evento}\r
DESCRIPTION:{descripcion or 'Sin descripcion'}\r
LOCATION:{nombre_edificio}\r
ORGANIZER;CN=Sistema Eventos:mailto:{SMTP_USER}\r
ATTENDEE;CN={nombre_profe};RSVP=TRUE;ROLE=REQ-PARTICIPANT:mailto:{email_destino}\r
STATUS:CONFIRMED\r
SEQUENCE:0\r
END:VEVENT\r
END:VCALENDAR\r
"""
        html = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:auto;
                    border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
          <div style="background:#6433b4;padding:24px 28px">
            <h2 style="color:#fff;margin:0">📅 {nombre_evento}</h2>
          </div>
          <div style="padding:24px 28px">
            <p style="color:#374151">Hola <strong>{nombre_profe}</strong>,</p>
            <p style="color:#374151">Has sido asignado a un nuevo evento:</p>
            <table style="width:100%;border-collapse:collapse;font-size:14px">
              <tr>
                <td style="padding:8px 0;color:#6b7280;width:110px">📌 Evento</td>
                <td style="color:#111827;font-weight:600">{nombre_evento}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#6b7280">🏢 Edificio</td>
                <td style="color:#111827">{nombre_edificio}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#6b7280">🕐 Inicio</td>
                <td style="color:#111827">{fecha_inicio.strftime('%d/%m/%Y %H:%M')}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#6b7280">🕐 Fin</td>
                <td style="color:#111827">{fecha_fin.strftime('%d/%m/%Y %H:%M')}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#6b7280">📝 Descripción</td>
                <td style="color:#111827">{descripcion or 'Sin descripción'}</td>
              </tr>
            </table>
            <p style="color:#6b7280;font-size:13px;margin-top:20px">
              El archivo adjunto <strong>.ics</strong> es una invitación de calendario.
              Ábrelo para agregarlo directamente a Google Calendar, Outlook o Apple Calendar.
            </p>
          </div>
          <div style="background:#f9fafb;padding:14px 28px;font-size:12px;color:#9ca3af">
            Sistema de Gestión de Eventos © 2026
          </div>
        </div>"""

        msg            = MIMEMultipart("mixed")
        msg["Subject"] = f"📅 Invitación al evento: {nombre_evento}"
        msg["From"]    = SMTP_USER
        msg["To"]      = email_destino
        msg.attach(MIMEText(html, "html"))

        ics_part = MIMEBase("text", "calendar", method="REQUEST", name="invitacion.ics")
        ics_part.set_payload(ical.encode("utf-8"))
        encoders.encode_base64(ics_part)
        ics_part.add_header("Content-Disposition", "attachment", filename="invitacion.ics")
        ics_part.add_header("Content-Type", 'text/calendar; method=REQUEST; charset=UTF-8')
        msg.attach(ics_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, email_destino, msg.as_string())

        print(f"✅ Email enviado a {email_destino}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False
