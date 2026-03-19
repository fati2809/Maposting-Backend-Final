# Migraciones de Base de Datos

Este directorio contiene los scripts SQL de migración para Supabase.

## 📋 Lista de Migraciones

| #   | Archivo                    | Descripción                 | Fecha      |
| --- | -------------------------- | --------------------------- | ---------- |
| 001 | `001_add_aulas_system.sql` | Sistema de Gestión de Aulas | 2026-03-04 |

## 🚀 Cómo Ejecutar una Migración

### Opción 1: Supabase Dashboard (Recomendado)

1. Accede a tu proyecto en [https://supabase.com](https://supabase.com)
2. Ve a **SQL Editor** en el menú lateral
3. Haz clic en **+ New Query**
4. Copia y pega el contenido del archivo de migración
5. Haz clic en **Run** o presiona `Ctrl/Cmd + Enter`
6. Revisa los mensajes en la consola para verificar que todo se ejecutó correctamente

### Opción 2: CLI de Supabase

```bash
# Si tienes Supabase CLI instalado
supabase db push --db-url "postgresql://..."
```

### Opción 3: psql (Postgres CLI)

```bash
# Conéctate a tu base de datos
psql "postgresql://usuario:password@host:puerto/database"

# Ejecuta el script
\i backend/migrations/001_add_aulas_system.sql
```

## ⚠️ Notas Importantes

### Antes de Ejecutar

- ✅ **Haz backup** de tu base de datos si ya tiene datos en producción
- ✅ **Revisa el script** para asegurarte de que se ajusta a tus necesidades
- ✅ **Prueba primero en desarrollo** antes de aplicar en producción
- ✅ **Verifica las referencias** a tablas existentes (edificios, eventos)

### Después de Ejecutar

- ✅ Verifica que todas las tablas se crearon correctamente
- ✅ Revisa que los índices se aplicaron
- ✅ Comprueba las relaciones de foreign keys
- ✅ Prueba insertar datos de ejemplo manualmente

## 🔄 Rollback

Si necesitas revertir una migración, ejecuta el script correspondiente:

### Para revertir 001_add_aulas_system.sql

```sql
-- Eliminar índices de eventos
DROP INDEX IF EXISTS idx_eventos_aula;
DROP INDEX IF EXISTS idx_eventos_aula_fecha;
DROP INDEX IF EXISTS idx_eventos_timedate;
DROP INDEX IF EXISTS idx_eventos_timedate_end;

-- Eliminar columnas de eventos
ALTER TABLE eventos DROP COLUMN IF EXISTS id_aula;
ALTER TABLE eventos DROP COLUMN IF EXISTS capacidad_esperada;
ALTER TABLE eventos DROP COLUMN IF EXISTS prioridad;
ALTER TABLE eventos DROP COLUMN IF EXISTS timedate_end;

-- Eliminar índices de aulas
DROP INDEX IF EXISTS idx_aulas_building;
DROP INDEX IF EXISTS idx_aulas_planta;
DROP INDEX IF EXISTS idx_aulas_disponible;
DROP INDEX IF EXISTS idx_aulas_capacidad;

-- Eliminar tabla aulas
DROP TABLE IF EXISTS aulas;
```

⚠️ **ADVERTENCIA**: El rollback eliminará todos los datos de aulas y las referencias en eventos.

## 📊 Estructura Resultante

Después de ejecutar `001_add_aulas_system.sql`:

### Tabla: aulas

```
id_aula (PK)
nombre_aula
codigo_aula
id_building (FK → edificios)
planta
capacidad
tipo_aula
equipamiento (JSONB)
disponible
created_at
```

### Tabla: eventos (columnas añadidas)

```
id_aula (FK → aulas)
capacidad_esperada
prioridad
timedate_end
```

## 🔍 Verificación Post-Migración

Ejecuta estas queries para verificar:

```sql
-- Ver estructura de aulas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'aulas';

-- Ver índices de aulas
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'aulas';

-- Ver nuevas columnas en eventos
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'eventos'
  AND column_name IN ('id_aula', 'capacidad_esperada', 'prioridad', 'timedate_end');

-- Contar aulas por edificio
SELECT e.name_building, COUNT(a.id_aula) as total_aulas
FROM edificios e
LEFT JOIN aulas a ON e.id_building = a.id_building
GROUP BY e.id_building, e.name_building
ORDER BY e.name_building;
```

## 💡 Tips

- Los scripts usan `IF NOT EXISTS` / `IF EXISTS` para ser idempotentes (se pueden ejecutar múltiples veces sin error)
- Los comentarios en las tablas ayudan a documentar el propósito de cada columna
- Los mensajes `RAISE NOTICE` te informan del progreso de la migración

## 📝 Datos de Ejemplo

El script `001_add_aulas_system.sql` incluye datos de ejemplo comentados. Para usarlos:

1. Abre el archivo
2. Busca la sección 6 (DATOS DE EJEMPLO)
3. Descomenta el bloque de INSERT
4. Ajusta el `id_building` según tus datos
5. Ejecuta el script

## ❓ Solución de Problemas

### Error: "relation edificios does not exist"

- Verifica que la tabla `edificios` existe en tu base de datos
- Ejecuta primero las migraciones base del proyecto

### Error: "duplicate key value violates unique constraint"

- Ya ejecutaste el script antes y hay datos existentes
- Es seguro, el script usa `IF NOT EXISTS`

### Error: "permission denied"

- Tu usuario de base de datos no tiene permisos suficientes
- Usa un usuario con privilegios de administrador

## 📞 Soporte

Si tienes problemas con la migración:

1. Revisa los logs de Supabase
2. Verifica que tu plan de Supabase soporte las features usadas
3. Consulta la documentación de PostgreSQL para características específicas
