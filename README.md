# Backend - MapPosting

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip3 install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales de Supabase
```

### 3. Ejecutar el servidor

```bash
python3 run.py
```

O directamente:

```bash
uvicorn app.main:app --reload
```

El servidor estará disponible en:

- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs

---

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuración de Supabase
│   ├── routers/             # Endpoints de la API
│   │   ├── eventos_router.py
│   │   ├── usuarios_router.py
│   │   ├── edificios_router.py
│   │   ├── divisiones_router.py
│   │   └── dashboard_router.py
│   ├── models/              # Schemas de Pydantic
│   │   ├── models.py
│   │   └── schemas.py
│   └── utils/               # Utilidades
│       └── security.py      # Funciones de seguridad
├── .env                     # Variables de entorno (no commitear)
├── .env.example             # Plantilla de variables
├── requirements.txt         # Dependencias Python
└── run.py                   # Script de inicio
```

---

## 🔧 Tecnologías

- **FastAPI**: Framework web moderno
- **Supabase**: Base de datos PostgreSQL en la nube
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

---

## 📚 Documentación

La documentación interactiva está disponible en `/docs` cuando el servidor está corriendo.
