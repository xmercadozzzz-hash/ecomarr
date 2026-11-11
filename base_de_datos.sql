-- ============================================================
-- ECOMAR · estructura completa de la base de datos
-- ============================================================
-- No es obligatorio ejecutar este archivo: app.py crea estas
-- tablas solo al arrancar si no existen. Sirve como respaldo o
-- para crearlas a mano desde phpMyAdmin / MySQL Workbench.

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reportes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_lugar VARCHAR(150) NOT NULL,
    ubicacion VARCHAR(255),
    barrio VARCHAR(150) NULL,
    latitud DECIMAL(10, 7) NULL,
    longitud DECIMAL(10, 7) NULL,
    tipo_contaminacion VARCHAR(100),
    nivel_afectacion VARCHAR(30),
    descripcion TEXT,
    fotografia VARCHAR(255),
    fecha_reporte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT NULL,
    INDEX idx_reportes_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Copia de las fotos subidas (el disco del hosting se borra al reiniciar)
CREATE TABLE IF NOT EXISTS fotos_reportes (
    nombre VARCHAR(100) PRIMARY KEY,
    tipo VARCHAR(50),
    datos MEDIUMBLOB NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jornadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    lugar VARCHAR(255),
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    cupos INT NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'disponible',
    reporte_id INT NULL,
    prioridad TINYINT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS inscripciones_jornada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jornada_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unica_inscripcion (jornada_id, usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Para volver administrador a una cuenta ya registrada:
-- UPDATE usuarios SET rol = 'admin' WHERE email = 'tu-correo@ejemplo.com';
