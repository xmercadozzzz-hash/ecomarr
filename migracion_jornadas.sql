-- ECOMAR - estructura complementaria para Jornadas
-- La aplicación también intenta crear/actualizar estas estructuras automáticamente.

ALTER TABLE jornadas
    ADD COLUMN reporte_id INT NULL;

ALTER TABLE jornadas
    ADD COLUMN prioridad TINYINT NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS inscripciones_jornada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jornada_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unica_inscripcion (jornada_id, usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
