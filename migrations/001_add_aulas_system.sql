-- ============================================================
-- MIGRACIÓN: Sistema de Gestión de Aulas
-- Fecha: 2026-03-04
-- Descripción: Añade tabla de aulas y actualiza eventos
-- ============================================================

-- ============================================================
-- 1. CREAR TABLA AULAS
-- ============================================================

CREATE TABLE IF NOT EXISTS aulas (
    id_aula SERIAL PRIMARY KEY,
    nombre_aula VARCHAR(100) NOT NULL,
    codigo_aula VARCHAR(50),
    id_building INT NOT NULL REFERENCES edificios(id_building) ON DELETE CASCADE,
    planta VARCHAR(10) CHECK (planta IN ('baja', 'alta', 'sotano', 'azotea')),
    capacidad INT NOT NULL DEFAULT 0,
    tipo_aula VARCHAR(50),
    equipamiento JSONB DEFAULT '{}'::jsonb,
    disponible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. CREAR ÍNDICES PARA PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_aulas_building ON aulas(id_building);
CREATE INDEX IF NOT EXISTS idx_aulas_planta ON aulas(planta);
CREATE INDEX IF NOT EXISTS idx_aulas_disponible ON aulas(disponible);
CREATE INDEX IF NOT EXISTS idx_aulas_capacidad ON aulas(capacidad);

-- ============================================================
-- 3. MODIFICAR TABLA EVENTOS
-- ============================================================

-- Añadir columna de referencia a aulas
ALTER TABLE eventos 
ADD COLUMN IF NOT EXISTS id_aula INT REFERENCES aulas(id_aula);

-- Añadir columna de capacidad esperada
ALTER TABLE eventos 
ADD COLUMN IF NOT EXISTS capacidad_esperada INT DEFAULT 0;

-- Añadir columna de prioridad
ALTER TABLE eventos 
ADD COLUMN IF NOT EXISTS prioridad INT DEFAULT 1;

-- Añadir columna de fecha/hora de fin
ALTER TABLE eventos 
ADD COLUMN IF NOT EXISTS timedate_end TIMESTAMP;

-- ============================================================
-- 4. CREAR ÍNDICES PARA EVENTOS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_eventos_aula ON eventos(id_aula);
CREATE INDEX IF NOT EXISTS idx_eventos_aula_fecha ON eventos(id_aula, timedate_event);
CREATE INDEX IF NOT EXISTS idx_eventos_timedate ON eventos(timedate_event);
CREATE INDEX IF NOT EXISTS idx_eventos_timedate_end ON eventos(timedate_end);

-- ============================================================
-- 5. AÑADIR COMENTARIOS A LAS COLUMNAS
-- ============================================================

COMMENT ON TABLE aulas IS 'Tabla de aulas/salones disponibles en cada edificio';
COMMENT ON COLUMN aulas.nombre_aula IS 'Nombre descriptivo del aula (Ej: Aula 101, Laboratorio A)';
COMMENT ON COLUMN aulas.codigo_aula IS 'Código o identificador corto del aula (Ej: A-101, LAB-A)';
COMMENT ON COLUMN aulas.planta IS 'Ubicación vertical del aula en el edificio';
COMMENT ON COLUMN aulas.capacidad IS 'Número máximo de personas que puede albergar';
COMMENT ON COLUMN aulas.tipo_aula IS 'Tipo de aula: salon, laboratorio, auditorio, sala_juntas, etc.';
COMMENT ON COLUMN aulas.equipamiento IS 'JSON con equipamiento disponible: proyector, aire_acondicionado, computadoras, etc.';
COMMENT ON COLUMN aulas.disponible IS 'Indica si el aula está disponible para reservas (false si está en mantenimiento)';

COMMENT ON COLUMN eventos.id_aula IS 'Referencia al aula específica donde se realiza el evento';
COMMENT ON COLUMN eventos.capacidad_esperada IS 'Número de personas esperadas en el evento';
COMMENT ON COLUMN eventos.prioridad IS 'Nivel de prioridad del evento (1=baja, 5=alta)';
COMMENT ON COLUMN eventos.timedate_end IS 'Fecha y hora de finalización del evento';

-- ============================================================
-- 6. DATOS DE EJEMPLO (OPCIONAL - COMENTAR SI NO SE DESEA)
-- ============================================================

-- Descomentar las siguientes líneas para insertar datos de ejemplo

/*
-- Asumiendo que existe un edificio con id_building = 1
-- Aulas para un edificio de ejemplo

INSERT INTO aulas (nombre_aula, codigo_aula, id_building, planta, capacidad, tipo_aula, equipamiento) VALUES
('Aula 101', 'A-101', 1, 'baja', 30, 'salon', '{"proyector": true, "aire_acondicionado": true, "pizarron_digital": false}'::jsonb),
('Aula 102', 'A-102', 1, 'baja', 35, 'salon', '{"proyector": true, "aire_acondicionado": true, "pizarron_digital": true}'::jsonb),
('Aula 103', 'A-103', 1, 'baja', 25, 'salon', '{"proyector": true, "aire_acondicionado": false, "pizarron_digital": false}'::jsonb),
('Laboratorio de Computación', 'LAB-A', 1, 'baja', 30, 'laboratorio', '{"proyector": true, "aire_acondicionado": true, "computadoras": 30, "servidor": true}'::jsonb),
('Aula 201', 'A-201', 1, 'alta', 40, 'salon', '{"proyector": true, "aire_acondicionado": true, "pizarron_digital": true}'::jsonb),
('Aula 202', 'A-202', 1, 'alta', 35, 'salon', '{"proyector": true, "aire_acondicionado": false, "pizarron_digital": false}'::jsonb),
('Laboratorio de Física', 'LAB-B', 1, 'alta', 25, 'laboratorio', '{"proyector": true, "aire_acondicionado": true, "material_laboratorio": true}'::jsonb),
('Auditorio Principal', 'AUD-01', 1, 'baja', 150, 'auditorio', '{"proyector": true, "aire_acondicionado": true, "sistema_audio": true, "microfono": true, "escenario": true}'::jsonb),
('Sala de Juntas', 'SJ-01', 1, 'alta', 15, 'sala_juntas', '{"proyector": true, "aire_acondicionado": true, "videoconferencia": true, "pizarron_blanco": true}'::jsonb);

-- Mensaje informativo
DO $$
BEGIN
    RAISE NOTICE 'Se han insertado 9 aulas de ejemplo para el edificio con id_building=1';
    RAISE NOTICE 'Modifica los datos según tus necesidades o elimina estas líneas si no las necesitas';
END $$;
*/

-- ============================================================
-- 7. VERIFICACIÓN POST-MIGRACIÓN
-- ============================================================

-- Verificar que la tabla se creó correctamente
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'aulas') THEN
        RAISE NOTICE '✓ Tabla "aulas" creada correctamente';
    ELSE
        RAISE EXCEPTION '✗ Error: Tabla "aulas" no fue creada';
    END IF;

    -- Verificar que las columnas de eventos se añadieron
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'eventos' AND column_name = 'id_aula') THEN
        RAISE NOTICE '✓ Columna "eventos.id_aula" añadida correctamente';
    ELSE
        RAISE EXCEPTION '✗ Error: Columna "eventos.id_aula" no fue añadida';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'eventos' AND column_name = 'capacidad_esperada') THEN
        RAISE NOTICE '✓ Columna "eventos.capacidad_esperada" añadida correctamente';
    ELSE
        RAISE EXCEPTION '✗ Error: Columna "eventos.capacidad_esperada" no fue añadida';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'eventos' AND column_name = 'prioridad') THEN
        RAISE NOTICE '✓ Columna "eventos.prioridad" añadida correctamente';
    ELSE
        RAISE EXCEPTION '✗ Error: Columna "eventos.prioridad" no fue añadida';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'eventos' AND column_name = 'timedate_end') THEN
        RAISE NOTICE '✓ Columna "eventos.timedate_end" añadida correctamente';
    ELSE
        RAISE EXCEPTION '✗ Error: Columna "eventos.timedate_end" no fue añadida';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'MIGRACIÓN COMPLETADA EXITOSAMENTE';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Siguiente paso: Crear el router de aulas en el backend';
END $$;
