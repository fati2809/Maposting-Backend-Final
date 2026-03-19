from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Singleton: se crea UNA sola vez y se reutiliza en toda la app
_supabase_client: Client = None

def get_supabase_client() -> Client:
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Conexion a Supabase establecida correctamente")
        print(f"URL: {SUPABASE_URL}")
        return _supabase_client
    except Exception as e:
        print(f"Error al conectar con Supabase: {str(e)}")
        raise