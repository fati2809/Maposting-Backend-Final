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
    print("SMTP_HOST:", SMTP_HOST)
    print("SMTP_PORT:", SMTP_PORT)
    print("SMTP_USER:", SMTP_USER)

    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️ SMTP no configurado, omitiendo envío de email")
        return False

    try:
        # 📅 ICS
        ical = f"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//SistemaEventos//ES\r
METHOD:REQUEST\r
BEGIN:VEVENT\r
UID:{uuid.uuid4()}\r
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%S")}\r
DTSTART:{fecha_inicio.strftime("%Y%m%dT%H%M%S")}\r
DTEND:{fecha_fin.strftime("%Y%m%dT%H%M%S")}\r
SUMMARY:{nombre_evento}\r
DESCRIPTION:{descripcion or 'Sin descripcion'}\r
LOCATION:{nombre_edificio}\r
ORGANIZER:mailto:{SMTP_USER}\r
ATTENDEE:mailto:{email_destino}\r
END:VEVENT\r
END:VCALENDAR\r
"""

        # 📨 HTML
        html = f"""
        <h2>📅 {nombre_evento}</h2>
        <p>Hola {nombre_profe},</p>
        <p>Tienes un nuevo evento.</p>
        """

        # 📦 Email
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"📅 Invitación: {nombre_evento}"
        msg["From"] = SMTP_USER
        msg["To"] = email_destino

        msg.attach(MIMEText(html, "html"))

        ics_part = MIMEBase("text", "calendar")
        ics_part.set_payload(ical.encode("utf-8"))
        encoders.encode_base64(ics_part)
        ics_part.add_header("Content-Disposition", "attachment", filename="invitacion.ics")
        msg.attach(ics_part)

        # 🔐 SMTP
        print("🔐 Conectando a SMTP...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()

            print("🔑 Login...")
            server.login(SMTP_USER, SMTP_PASSWORD)

            print("📤 Enviando email...")
            server.sendmail(SMTP_USER, email_destino, msg.as_string())

        print(f"✅ Email enviado a {email_destino}")
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error enviando email: {e}")
        return False
