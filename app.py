from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)

import mysql.connector
import datetime
import os
import uuid

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "clave-local-desarrollo")

# Ruta absoluta (más segura en Render)
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# BASE DE DATOS
# ============================================================

# TEMPORAL: solo imprime longitudes (no los valores). Borra estas 3 líneas
# cuando la conexión funcione.
# Esperado: USER 16, PASS 20, NAME 20
print("LEN USER:", len(os.environ.get("DB_USER", "")))
print("LEN PASS:", len(os.environ.get("DB_PASSWORD", "")))
print("LEN NAME:", len(os.environ.get("DB_NAME", "")))


def conectar_bd():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost").strip(),
        port=int(os.environ.get("DB_PORT", "3306").strip()),
        user=os.environ.get("DB_USER", "root").strip(),
        password=os.environ.get("DB_PASSWORD", "").strip(),
        database=os.environ.get("DB_NAME", "ecomar").strip(),
        connection_timeout=15,
    )


@app.errorhandler(mysql.connector.Error)
def error_base_de_datos(error):
    # Cualquier error de BD no capturado muestra esto en vez de un 500 feo
    app.logger.error("Error de base de datos: %s", error)
    return (
        "<h1>Servicio temporalmente no disponible</h1>"
        "<p>No pudimos conectar con la base de datos. "
        "Intenta de nuevo en unos minutos.</p>",
        503,
    )


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def archivo_permitido(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def usuario_logueado():
    return "usuario_id" in session


def es_admin():
    return session.get("rol") == "admin"


def cerrar_conexion(cursor, conexion):
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass
    try:
        if conexion:
            conexion.close()
    except Exception:
        pass


def a_decimal(valor):
    # Un campo vacío ("") rompe columnas DECIMAL; lo convertimos a None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def inicio():
    reportes_recientes = []
    conexion = cursor = None

    # Si la BD falla, la portada igual carga (también sirve al health check)
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                r.id, r.nombre_lugar, r.ubicacion, r.tipo_contaminacion,
                r.nivel_afectacion, r.descripcion, r.fotografia,
                r.fecha_reporte, u.nombre AS usuario_nombre
            FROM reportes r
            LEFT JOIN usuarios u ON r.usuario_id = u.id
            ORDER BY r.fecha_reporte DESC
            LIMIT 3
        """)
        reportes_recientes = cursor.fetchall()
    except mysql.connector.Error as error:
        app.logger.error("Inicio sin BD: %s", error)
    finally:
        cerrar_conexion(cursor, conexion)

    return render_template("index.html", reportes_recientes=reportes_recientes)


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("login"))


# ============================================================
# REGISTRO
# ============================================================

@app.route("/registro")
def registro():
    if usuario_logueado():
        return redirect(url_for("admin" if es_admin() else "perfil"))
    return render_template("registro.html")


@app.route("/crear-cuenta", methods=["POST"])
def crear_cuenta():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirmar_password = request.form.get("confirmar_password", "")

    if not nombre or not email or not password:
        flash("Todos los campos son obligatorios.", "danger")
        return redirect(url_for("registro"))

    if password != confirmar_password:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect(url_for("registro"))

    if len(password) < 6:
        flash("La contraseña debe tener mínimo 6 caracteres.", "danger")
        return redirect(url_for("registro"))

    conexion = conectar_bd()
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))

    if cursor.fetchone():
        cerrar_conexion(cursor, conexion)
        flash("Ya existe una cuenta con ese correo.", "warning")
        return redirect(url_for("registro"))

    cursor.execute(
        """
        INSERT INTO usuarios (nombre, email, password, rol)
        VALUES (%s, %s, %s, 'usuario')
        """,
        (nombre, email, generate_password_hash(password))
    )
    conexion.commit()
    usuario_id = cursor.lastrowid
    cerrar_conexion(cursor, conexion)

    session["usuario_id"] = usuario_id
    session["usuario_nombre"] = nombre
    session["usuario_email"] = email
    session["rol"] = "usuario"

    flash("Cuenta creada correctamente.", "success")
    return redirect(url_for("perfil"))


# ============================================================
# LOGIN
# ============================================================

@app.route("/login")
def login():
    if usuario_logueado():
        return redirect(url_for("admin" if es_admin() else "perfil"))
    return render_template("login.html")


@app.route("/iniciar-sesion", methods=["POST"])
def iniciar_sesion():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Debes ingresar el correo y la contraseña.", "danger")
        return redirect(url_for("login"))

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, nombre, email, password, rol
        FROM usuarios
        WHERE email = %s
        """,
        (email,)
    )
    usuario = cursor.fetchone()
    cerrar_conexion(cursor, conexion)

    if not usuario or not check_password_hash(usuario["password"], password):
        flash("El correo o la contraseña son incorrectos.", "danger")
        return redirect(url_for("login"))

    session["usuario_id"] = usuario["id"]
    session["usuario_nombre"] = usuario["nombre"]
    session["usuario_email"] = usuario["email"]
    session["rol"] = usuario["rol"]

    if usuario["rol"] == "admin":
        return redirect(url_for("admin"))

    return redirect(url_for("perfil"))


@app.route("/cerrar-sesion")
def cerrar_sesion():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("inicio"))


# ============================================================
# PERFIL
# ============================================================

@app.route("/perfil")
def perfil():
    if not usuario_logueado():
        return redirect(url_for("login"))

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, nombre, email, fecha_registro, rol
        FROM usuarios
        WHERE id = %s
        """,
        (session["usuario_id"],)
    )
    usuario = cursor.fetchone()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM reportes WHERE usuario_id = %s",
        (session["usuario_id"],)
    )
    total_reportes = cursor.fetchone()["total"]

    cerrar_conexion(cursor, conexion)

    return render_template(
        "perfil.html", usuario=usuario, total_reportes=total_reportes
    )


# ============================================================
# REPORTAR
# ============================================================

@app.route("/reportar")
def reportar():
    if not usuario_logueado():
        flash("Debes iniciar sesión para realizar un reporte.", "warning")
        return redirect(url_for("login"))
    return render_template("reportar.html")


@app.route("/crear-reporte", methods=["POST"])
def crear_reporte():
    if not usuario_logueado():
        return redirect(url_for("login"))

    nombre_lugar = request.form.get("nombre_lugar", "").strip()
    ubicacion = request.form.get("ubicacion", "").strip()
    latitud = a_decimal(request.form.get("latitud"))
    longitud = a_decimal(request.form.get("longitud"))
    tipo_contaminacion = request.form.get("tipo_contaminacion", "").strip()
    nivel_afectacion = request.form.get("nivel_afectacion", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    fotografia = request.files.get("fotografia")

    if not nombre_lugar:
        flash("Debes indicar el lugar.", "danger")
        return redirect(url_for("reportar"))

    if not ubicacion:
        flash("Debes indicar la ubicación.", "danger")
        return redirect(url_for("reportar"))

    nombre_fotografia = None

    if fotografia and fotografia.filename:

        if not archivo_permitido(fotografia.filename):
            flash("El formato de imagen no está permitido.", "danger")
            return redirect(url_for("reportar"))

        extension = fotografia.filename.rsplit(".", 1)[1].lower()
        nombre_fotografia = str(uuid.uuid4()) + "." + extension

        fotografia.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                secure_filename(nombre_fotografia)
            )
        )

    conexion = conectar_bd()
    cursor = conexion.cursor()

    cursor.execute(
        """
        INSERT INTO reportes
        (
            nombre_lugar, ubicacion, latitud, longitud,
            tipo_contaminacion, nivel_afectacion, descripcion,
            fotografia, usuario_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            nombre_lugar, ubicacion, latitud, longitud,
            tipo_contaminacion, nivel_afectacion, descripcion,
            nombre_fotografia, session["usuario_id"]
        )
    )
    conexion.commit()
    cerrar_conexion(cursor, conexion)

    flash("Reporte registrado correctamente.", "success")
    return redirect(url_for("reportes"))


# ============================================================
# REPORTES
# ============================================================

@app.route("/reportes")
def reportes():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.id, r.nombre_lugar, r.ubicacion, r.latitud, r.longitud,
            r.tipo_contaminacion, r.nivel_afectacion, r.descripcion,
            r.fotografia, r.fecha_reporte, u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u ON r.usuario_id = u.id
        ORDER BY r.fecha_reporte DESC
    """)
    lista = cursor.fetchall()
    cerrar_conexion(cursor, conexion)

    return render_template("reportes.html", reportes=lista)


# ============================================================
# MAPAS
# ============================================================

@app.route("/mapas")
def mapas():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.id, r.nombre_lugar, r.ubicacion, r.latitud, r.longitud,
            r.tipo_contaminacion, r.nivel_afectacion, r.descripcion,
            r.fotografia, r.fecha_reporte, u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u ON r.usuario_id = u.id
        WHERE r.latitud IS NOT NULL AND r.longitud IS NOT NULL
        ORDER BY r.fecha_reporte DESC
    """)
    lista = cursor.fetchall()
    cerrar_conexion(cursor, conexion)

    return render_template("mapas.html", reportes=lista)


# ============================================================
# APIs DE REPORTES PARA EL MAPA
# ============================================================

SQL_REPORTES_MAPA = """
    SELECT
        r.id, r.nombre_lugar, r.ubicacion, r.barrio, r.latitud,
        r.longitud, r.tipo_contaminacion, r.nivel_afectacion,
        r.descripcion, r.fotografia, r.fecha_reporte,
        u.nombre AS usuario_nombre
    FROM reportes r
    LEFT JOIN usuarios u ON r.usuario_id = u.id
    WHERE r.latitud IS NOT NULL AND r.longitud IS NOT NULL
    ORDER BY r.fecha_reporte DESC
"""


@app.route("/api/reportes")
def api_reportes():
    if not usuario_logueado():
        return jsonify({"error": "No autorizado"}), 401

    if not es_admin():
        return jsonify({"error": "No tienes permisos"}), 403

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(SQL_REPORTES_MAPA)
    datos = cursor.fetchall()
    cerrar_conexion(cursor, conexion)

    return jsonify(datos)


@app.route("/api/reportes-publicos")
def api_reportes_publicos():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(SQL_REPORTES_MAPA)
    datos = cursor.fetchall()
    cerrar_conexion(cursor, conexion)

    return jsonify(datos)


# ============================================================
# ELIMINAR REPORTE
# ============================================================

@app.route("/eliminar-reporte/<int:id>", methods=["POST"])
def eliminar_reporte(id):
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_admin():
        flash("No tienes permisos para eliminar reportes.", "danger")
        return redirect(url_for("reportes"))

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT fotografia FROM reportes WHERE id = %s", (id,))
    reporte = cursor.fetchone()

    if reporte and reporte["fotografia"]:
        ruta = os.path.join(
            app.config["UPLOAD_FOLDER"],
            secure_filename(reporte["fotografia"])
        )
        if os.path.exists(ruta):
            os.remove(ruta)

    cursor.execute("DELETE FROM reportes WHERE id = %s", (id,))
    conexion.commit()
    cerrar_conexion(cursor, conexion)

    flash("Reporte eliminado correctamente.", "success")
    return redirect(url_for("reportes"))


# ============================================================
# JORNADAS · UTILIDADES
# ============================================================
# Prioridad según el nivel de afectación: Crítico (4) > Alto (3) > Medio (2) > Bajo (1)

PRIORIDADES = {"crítico": 4, "critico": 4, "alto": 3, "medio": 2, "bajo": 1}

NOMBRES_PRIORIDAD = {4: "Crítico", 3: "Alto", 2: "Medio", 1: "Bajo"}

DIAS_SEMANA = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo"
]

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

ESTADOS_JORNADA = ("disponible", "completada", "cancelada")


def prioridad_desde_nivel(nivel):
    return PRIORIDADES.get((nivel or "").strip().lower(), 1)


def a_fecha(valor):
    if isinstance(valor, datetime.datetime):
        return valor.date()

    if isinstance(valor, datetime.date):
        return valor

    if isinstance(valor, str):
        try:
            return datetime.date.fromisoformat(valor[:10])
        except ValueError:
            return None

    return None


def a_hora(valor):
    # MySQL devuelve las columnas TIME como timedelta
    if isinstance(valor, datetime.timedelta):
        segundos = int(valor.total_seconds()) % 86400
        return datetime.time(segundos // 3600, (segundos % 3600) // 60)

    if isinstance(valor, datetime.time):
        return valor.replace(second=0, microsecond=0)

    if isinstance(valor, str):
        for formato in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.datetime.strptime(valor, formato).time()
            except ValueError:
                pass

    return None


def texto_fecha(fecha):
    return (
        f"{DIAS_SEMANA[fecha.weekday()]} "
        f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"
    )


def texto_hora(hora):
    h = hora.hour % 12 or 12
    sufijo = "a. m." if hora.hour < 12 else "p. m."
    return f"{h}:{hora.minute:02d} {sufijo}"


def normalizar_jornada(fila, ahora):
    fecha = a_fecha(fila["fecha"])
    hora = a_hora(fila["hora"]) or datetime.time(0, 0)

    if not fecha:
        return None

    prioridad = max(1, min(4, int(fila.get("prioridad") or 1)))
    cupos = int(fila.get("cupos") or 0)
    inscritos = int(fila.get("inscritos") or 0)

    vencida = datetime.datetime.combine(fecha, hora) < ahora

    return {
        "id": fila["id"],
        "titulo": fila["titulo"],
        "descripcion": fila.get("descripcion") or "",
        "lugar": fila.get("lugar") or "",
        "fecha": fecha.isoformat(),
        "fecha_texto": texto_fecha(fecha),
        "hora": hora.strftime("%H:%M"),
        "hora_texto": texto_hora(hora),
        "cupos": cupos,
        "inscritos": inscritos,
        "libres": max(cupos - inscritos, 0),
        "estado": fila.get("estado") or "disponible",
        "reporte_id": fila.get("reporte_id"),
        "prioridad": prioridad,
        "prioridad_nombre": NOMBRES_PRIORIDAD[prioridad],
        "inscrito": bool(fila.get("yo")),
        "vencida": vencida
    }


def ahora_local():
    # Render usa hora UTC; Colombia es UTC-5 (sin horario de verano)
    return datetime.datetime.utcnow() - datetime.timedelta(hours=5)


def preparar_tablas():
    """
    Crea / actualiza las tablas de jornadas si hace falta.
    Se puede ejecutar todas las veces que se quiera.
    """
    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute("""
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        columnas_nuevas = (
            ("reporte_id", "INT NULL"),
            ("prioridad", "TINYINT NOT NULL DEFAULT 1")
        )

        for nombre, definicion in columnas_nuevas:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'jornadas'
                AND COLUMN_NAME = %s
            """, (nombre,))

            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    f"ALTER TABLE jornadas ADD COLUMN {nombre} {definicion}"
                )

        # si "estado" fuera un ENUM antiguo, lo pasamos a texto
        cursor.execute("""
            SELECT DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'jornadas'
            AND COLUMN_NAME = 'estado'
        """)
        tipo = cursor.fetchone()

        if tipo and str(tipo[0]).lower() == "enum":
            cursor.execute("""
                ALTER TABLE jornadas
                MODIFY estado VARCHAR(20) NOT NULL DEFAULT 'disponible'
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inscripciones_jornada (
                id INT AUTO_INCREMENT PRIMARY KEY,
                jornada_id INT NOT NULL,
                usuario_id INT NOT NULL,
                fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unica_inscripcion (jornada_id, usuario_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        conexion.commit()

    except mysql.connector.Error as error:
        print("No se pudieron preparar las tablas de jornadas:", error)

    finally:
        cerrar_conexion(cursor, conexion)


# ============================================================
# JORNADAS · VISTA (admin y usuario)
# ============================================================

@app.route("/jornadas")
def jornadas():
    admin_vista = usuario_logueado() and es_admin()
    ahora = ahora_local()

    lista = []
    pendientes = []
    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        # mayor prioridad primero, y dentro de cada una, la más próxima
        cursor.execute(
            """
            SELECT
                j.id, j.titulo, j.descripcion, j.lugar, j.fecha, j.hora,
                j.cupos, j.estado, j.reporte_id, j.prioridad,
                (
                    SELECT COUNT(*) FROM inscripciones_jornada i
                    WHERE i.jornada_id = j.id
                ) AS inscritos,
                (
                    SELECT COUNT(*) FROM inscripciones_jornada i
                    WHERE i.jornada_id = j.id AND i.usuario_id = %s
                ) AS yo
            FROM jornadas j
            ORDER BY j.prioridad DESC, j.fecha ASC, j.hora ASC
            """,
            (session.get("usuario_id") or 0,)
        )

        for fila in cursor.fetchall():
            jornada = normalizar_jornada(fila, ahora)

            if not jornada:
                continue

            # el usuario solo ve jornadas disponibles que no han pasado
            if not admin_vista:
                if jornada["estado"] != "disponible" or jornada["vencida"]:
                    continue

            lista.append(jornada)

        # reportes que aún no tienen jornada (solo para el admin)
        if admin_vista:
            cursor.execute(
                """
                SELECT
                    r.id, r.nombre_lugar, r.ubicacion, r.barrio,
                    r.tipo_contaminacion, r.nivel_afectacion, r.fecha_reporte
                FROM reportes r
                WHERE NOT EXISTS (
                    SELECT 1 FROM jornadas j
                    WHERE j.reporte_id = r.id AND j.estado <> 'cancelada'
                )
                """
            )

            for r in cursor.fetchall():
                prioridad = prioridad_desde_nivel(r["nivel_afectacion"])
                fecha_reporte = a_fecha(r["fecha_reporte"])

                pendientes.append({
                    "id": r["id"],
                    "lugar": r["nombre_lugar"],
                    "ubicacion": r["barrio"] or r["ubicacion"] or "",
                    "tipo": r["tipo_contaminacion"] or "",
                    "prioridad": prioridad,
                    "prioridad_nombre": NOMBRES_PRIORIDAD[prioridad],
                    "fecha_reporte": (
                        fecha_reporte.isoformat() if fecha_reporte else ""
                    )
                })

            # críticos primero; a igual nivel, el reporte más antiguo
            pendientes.sort(key=lambda p: (-p["prioridad"], p["fecha_reporte"]))

    except mysql.connector.Error as error:
        app.logger.error("Error en jornadas: %s", error)
        flash("No se pudo consultar la base de datos.", "danger")

    finally:
        cerrar_conexion(cursor, conexion)

    datos = {
        "esAdmin": admin_vista,
        "jornadas": [
            {
                "id": j["id"],
                "fecha": j["fecha"],
                "prioridad": j["prioridad"],
                "estado": j["estado"],
                "vencida": j["vencida"]
            }
            for j in lista
        ]
    }

    return render_template(
        "jornadas.html",
        jornadas=lista,
        pendientes=pendientes,
        datos=datos,
        es_admin_vista=admin_vista,
        hoy=ahora.date().isoformat()
    )


# ============================================================
# CREAR JORNADA (solo admin)
# ============================================================

@app.route("/crear-jornada", methods=["POST"])
def crear_jornada():
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_admin():
        flash("Solo el administrador puede crear jornadas.", "danger")
        return redirect(url_for("jornadas"))

    titulo = request.form.get("titulo", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    lugar = request.form.get("lugar", "").strip()
    reporte_txt = request.form.get("reporte_id", "").strip()
    nivel_manual = request.form.get("nivel", "Bajo")

    fecha = a_fecha(request.form.get("fecha", ""))
    hora = a_hora(request.form.get("hora", ""))

    if not fecha or not hora:
        flash("Debes elegir el día y la hora de la jornada.", "danger")
        return redirect(url_for("jornadas"))

    if datetime.datetime.combine(fecha, hora) < ahora_local():
        flash("No puedes programar una jornada en una fecha que ya pasó.", "danger")
        return redirect(url_for("jornadas"))

    try:
        cupos = int(request.form.get("cupos", "0"))
    except ValueError:
        cupos = 0

    if cupos < 1:
        flash("Los cupos deben ser al menos 1.", "danger")
        return redirect(url_for("jornadas"))

    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        reporte_id = None
        prioridad = prioridad_desde_nivel(nivel_manual)

        # si la jornada atiende un reporte, la prioridad sale de ese reporte
        if reporte_txt.isdigit():
            cursor.execute(
                """
                SELECT id, nombre_lugar, barrio, ubicacion, nivel_afectacion
                FROM reportes
                WHERE id = %s
                """,
                (int(reporte_txt),)
            )
            reporte = cursor.fetchone()

            if not reporte:
                flash("El reporte seleccionado no existe.", "danger")
                return redirect(url_for("jornadas"))

            cursor.execute(
                """
                SELECT id FROM jornadas
                WHERE reporte_id = %s AND estado <> 'cancelada'
                LIMIT 1
                """,
                (reporte["id"],)
            )

            if cursor.fetchone():
                flash("Ese reporte ya tiene una jornada programada.", "warning")
                return redirect(url_for("jornadas"))

            reporte_id = reporte["id"]
            prioridad = prioridad_desde_nivel(reporte["nivel_afectacion"])

            if not lugar:
                lugar = reporte["nombre_lugar"] or ""
                detalle = reporte["barrio"] or reporte["ubicacion"]
                if detalle:
                    lugar = f"{lugar} · {detalle}"

        if not lugar:
            flash("Debes indicar el lugar de la jornada.", "danger")
            return redirect(url_for("jornadas"))

        if not titulo:
            titulo = f"Jornada de limpieza · {lugar}"

        cursor.execute(
            """
            INSERT INTO jornadas
            (
                titulo, descripcion, lugar, fecha, hora,
                cupos, estado, reporte_id, prioridad
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'disponible', %s, %s)
            """,
            (
                titulo, descripcion, lugar,
                fecha.isoformat(), hora.strftime("%H:%M:%S"),
                cupos, reporte_id, prioridad
            )
        )
        conexion.commit()

        flash(
            "Jornada programada correctamente "
            f"(prioridad {NOMBRES_PRIORIDAD[prioridad].lower()}).",
            "success"
        )

    except mysql.connector.Error as error:
        if conexion:
            conexion.rollback()
        app.logger.error("Error al crear jornada: %s", error)
        flash("No se pudo crear la jornada.", "danger")

    finally:
        cerrar_conexion(cursor, conexion)

    return redirect(url_for("jornadas"))


# ============================================================
# CAMBIAR ESTADO DE UNA JORNADA (solo admin)
# ============================================================

@app.route("/estado-jornada/<int:id>", methods=["POST"])
def estado_jornada(id):
    if not usuario_logueado() or not es_admin():
        flash("Solo el administrador puede cambiar el estado.", "danger")
        return redirect(url_for("jornadas"))

    estado = request.form.get("estado", "")

    if estado not in ESTADOS_JORNADA:
        flash("Estado no válido.", "danger")
        return redirect(url_for("jornadas"))

    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE jornadas SET estado = %s WHERE id = %s", (estado, id)
        )
        conexion.commit()
        flash(f"La jornada quedó como {estado}.", "success")

    except mysql.connector.Error as error:
        app.logger.error("Error al actualizar jornada: %s", error)
        flash("No se pudo actualizar la jornada.", "danger")

    finally:
        cerrar_conexion(cursor, conexion)

    return redirect(url_for("jornadas"))


# ============================================================
# ELIMINAR JORNADA (solo admin)
# ============================================================

@app.route("/eliminar-jornada/<int:id>", methods=["POST"])
def eliminar_jornada(id):
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_admin():
        flash("Solo el administrador puede eliminar jornadas.", "danger")
        return redirect(url_for("jornadas"))

    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE FROM inscripciones_jornada WHERE jornada_id = %s", (id,)
        )
        cursor.execute("DELETE FROM jornadas WHERE id = %s", (id,))
        conexion.commit()
        flash("Jornada eliminada correctamente.", "success")

    except mysql.connector.Error as error:
        app.logger.error("Error al eliminar jornada: %s", error)
        flash("No se pudo eliminar la jornada.", "danger")

    finally:
        cerrar_conexion(cursor, conexion)

    return redirect(url_for("jornadas"))


# ============================================================
# INSCRIBIRSE A UNA JORNADA (usuario)
# ============================================================

@app.route("/inscribirse-jornada/<int:id>", methods=["POST"])
def inscribirse_jornada(id):
    if not usuario_logueado():
        flash("Inicia sesión para inscribirte en una jornada.", "warning")
        return redirect(url_for("login"))

    if es_admin():
        flash(
            "El administrador gestiona las jornadas, no se inscribe en ellas.",
            "warning"
        )
        return redirect(url_for("jornadas"))

    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                j.id, j.fecha, j.hora, j.cupos, j.estado,
                (
                    SELECT COUNT(*) FROM inscripciones_jornada i
                    WHERE i.jornada_id = j.id
                ) AS inscritos
            FROM jornadas j
            WHERE j.id = %s
            """,
            (id,)
        )
        fila = cursor.fetchone()

        jornada = None

        if fila:
            fila["titulo"] = ""
            jornada = normalizar_jornada(fila, ahora_local())

        if not jornada or jornada["estado"] != "disponible" or jornada["vencida"]:
            flash("Esa jornada ya no está disponible.", "warning")

        elif jornada["libres"] <= 0:
            flash("Esa jornada ya no tiene cupos.", "warning")

        else:
            cursor.execute(
                """
                INSERT INTO inscripciones_jornada (jornada_id, usuario_id)
                VALUES (%s, %s)
                """,
                (id, session["usuario_id"])
            )
            conexion.commit()
            flash("¡Listo! Quedaste inscrito en la jornada.", "success")

    except mysql.connector.IntegrityError:
        flash("Ya estabas inscrito en esta jornada.", "info")

    except mysql.connector.Error as error:
        app.logger.error("Error al inscribirse: %s", error)
        flash("No se pudo completar la inscripción.", "danger")

    finally:
        cerrar_conexion(cursor, conexion)

    return redirect(url_for("jornadas"))


# ============================================================
# CANCELAR INSCRIPCIÓN (usuario)
# ============================================================

@app.route("/cancelar-inscripcion/<int:id>", methods=["POST"])
def cancelar_inscripcion(id):
    if not usuario_logueado():
        return redirect(url_for("login"))

    conexion = cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute(
            """
            DELETE FROM inscripciones_jornada
            WHERE jornada_id = %s AND usuario_id = %s
            """,
            (id, session["usuario_id"])
        )
        conexion.commit()
        flash("Cancelaste tu inscripción.", "success")

    except mysql.connector.Error as error:
        app.logger.error("Error al cancelar inscripción: %s", error)
        flash("No se pudo cancelar la inscripción.", "danger")

    finally:
        cerrar_conexion(cursor, conexion)

    return redirect(url_for("jornadas"))


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin")
def admin():
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_admin():
        flash("No tienes permisos para acceder.", "danger")
        return redirect(url_for("perfil"))

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.id, r.nombre_lugar, r.ubicacion, r.tipo_contaminacion,
            r.nivel_afectacion, r.descripcion, r.fotografia,
            r.fecha_reporte, u.nombre AS usuario_nombre,
            u.email AS usuario_email
        FROM reportes r
        LEFT JOIN usuarios u ON r.usuario_id = u.id
        ORDER BY r.fecha_reporte DESC
    """)
    lista_reportes = cursor.fetchall()

    cursor.execute("""
        SELECT id, nombre, email, fecha_registro, rol
        FROM usuarios
        ORDER BY fecha_registro DESC
    """)
    lista_usuarios = cursor.fetchall()

    cerrar_conexion(cursor, conexion)

    return render_template(
        "admin.html", reportes=lista_reportes, usuarios=lista_usuarios
    )


# ============================================================
# PREPARAR TABLAS DE JORNADAS
# ============================================================

preparar_tablas()


# ============================================================
# INICIAR APLICACIÓN (solo local; en Render lo ejecuta gunicorn)
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)