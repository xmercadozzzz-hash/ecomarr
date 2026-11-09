from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)


import mysql.connector
import os
import uuid

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

app.secret_key = "ecomar-clave-secreta-2026"

UPLOAD_FOLDER = os.path.join(
    "static",
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif"
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# BASE DE DATOS
# ============================================================

def conectar_bd():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ecomar"
    )


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def archivo_permitido(nombre):

    return (
        "." in nombre
        and nombre.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def usuario_logueado():

    return "usuario_id" in session


def es_admin():

    return session.get("rol") == "admin"


def cerrar_conexion(cursor, conexion):

    try:
        cursor.close()
    except:
        pass

    try:
        conexion.close()
    except:
        pass


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def inicio():

    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            r.id,
            r.nombre_lugar,
            r.ubicacion,
            r.tipo_contaminacion,
            r.nivel_afectacion,
            r.descripcion,
            r.fotografia,
            r.fecha_reporte,
            u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u
            ON r.usuario_id = u.id
        ORDER BY r.fecha_reporte DESC
        LIMIT 3
    """)

    reportes_recientes = cursor.fetchall()

    cerrar_conexion(
        cursor,
        conexion
    )

    return render_template(
        "index.html",
        reportes_recientes=reportes_recientes
    )

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

        if es_admin():

            return redirect(
                url_for("admin")
            )

        return redirect(
            url_for("perfil")
        )

    return render_template(
        "registro.html"
    )


@app.route(
    "/crear-cuenta",
    methods=["POST"]
)
def crear_cuenta():

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    confirmar_password = request.form.get(
        "confirmar_password",
        ""
    )


    if not nombre or not email or not password:

        flash(
            "Todos los campos son obligatorios.",
            "danger"
        )

        return redirect(
            url_for("registro")
        )


    if password != confirmar_password:

        flash(
            "Las contraseñas no coinciden.",
            "danger"
        )

        return redirect(
            url_for("registro")
        )


    if len(password) < 6:

        flash(
            "La contraseña debe tener mínimo 6 caracteres.",
            "danger"
        )

        return redirect(
            url_for("registro")
        )


    conexion = conectar_bd()

    cursor = conexion.cursor()


    cursor.execute(
        """
        SELECT id
        FROM usuarios
        WHERE email = %s
        """,
        (email,)
    )

    usuario_existente = cursor.fetchone()


    if usuario_existente:

        cerrar_conexion(
            cursor,
            conexion
        )

        flash(
            "Ya existe una cuenta con ese correo.",
            "warning"
        )

        return redirect(
            url_for("registro")
        )


    password_segura = generate_password_hash(
        password
    )


    cursor.execute(
        """
        INSERT INTO usuarios
        (
            nombre,
            email,
            password,
            rol
        )
        VALUES
        (
            %s,
            %s,
            %s,
            'usuario'
        )
        """,
        (
            nombre,
            email,
            password_segura
        )
    )


    conexion.commit()

    usuario_id = cursor.lastrowid


    cerrar_conexion(
        cursor,
        conexion
    )


    session["usuario_id"] = usuario_id
    session["usuario_nombre"] = nombre
    session["usuario_email"] = email
    session["rol"] = "usuario"


    flash(
        "Cuenta creada correctamente.",
        "success"
    )


    return redirect(
        url_for("perfil")
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login")
def login():

    if usuario_logueado():

        if es_admin():

            return redirect(
                url_for("admin")
            )

        return redirect(
            url_for("perfil")
        )

    return render_template(
        "login.html"
    )


@app.route(
    "/iniciar-sesion",
    methods=["POST"]
)
def iniciar_sesion():

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    if not email or not password:

        flash(
            "Debes ingresar el correo y la contraseña.",
            "danger"
        )

        return redirect(
            url_for("login")
        )


    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )


    cursor.execute(
        """
        SELECT
            id,
            nombre,
            email,
            password,
            rol
        FROM usuarios
        WHERE email = %s
        """,
        (email,)
    )


    usuario = cursor.fetchone()


    cerrar_conexion(
        cursor,
        conexion
    )


    if not usuario:

        flash(
            "El correo o la contraseña son incorrectos.",
            "danger"
        )

        return redirect(
            url_for("login")
        )


    if not check_password_hash(
        usuario["password"],
        password
    ):

        flash(
            "El correo o la contraseña son incorrectos.",
            "danger"
        )

        return redirect(
            url_for("login")
        )


    session["usuario_id"] = usuario["id"]
    session["usuario_nombre"] = usuario["nombre"]
    session["usuario_email"] = usuario["email"]
    session["rol"] = usuario["rol"]


    if usuario["rol"] == "admin":

        return redirect(
            url_for("admin")
        )


    return redirect(
        url_for("perfil")
    )


# ============================================================
# CERRAR SESIÓN
# ============================================================

@app.route("/cerrar-sesion")
def cerrar_sesion():

    session.clear()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for("inicio")
    )


# ============================================================
# PERFIL
# ============================================================

@app.route("/perfil")
def perfil():

    if not usuario_logueado():

        return redirect(
            url_for("login")
        )


    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )


    cursor.execute(
        """
        SELECT
            id,
            nombre,
            email,
            fecha_registro,
            rol
        FROM usuarios
        WHERE id = %s
        """,
        (session["usuario_id"],)
    )


    usuario = cursor.fetchone()


    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM reportes
        WHERE usuario_id = %s
        """,
        (session["usuario_id"],)
    )


    resultado = cursor.fetchone()

    total_reportes = resultado["total"]


    cerrar_conexion(
        cursor,
        conexion
    )


    return render_template(
        "perfil.html",
        usuario=usuario,
        total_reportes=total_reportes
    )


# ============================================================
# REPORTAR
# ============================================================

@app.route("/reportar")
def reportar():

    if not usuario_logueado():

        flash(
            "Debes iniciar sesión para realizar un reporte.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reportar.html"
    )


# ============================================================
# GUARDAR REPORTE
# ============================================================

@app.route(
    "/crear-reporte",
    methods=["POST"]
)
def crear_reporte():

    if not usuario_logueado():

        return redirect(
            url_for("login")
        )


    nombre_lugar = request.form.get(
        "nombre_lugar",
        ""
    ).strip()

    ubicacion = request.form.get(
        "ubicacion",
        ""
    ).strip()

    latitud = request.form.get(
        "latitud"
    )

    longitud = request.form.get(
        "longitud"
    )

    tipo_contaminacion = request.form.get(
        "tipo_contaminacion",
        ""
    ).strip()

    nivel_afectacion = request.form.get(
        "nivel_afectacion",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()


    fotografia = request.files.get(
        "fotografia"
    )


    if not nombre_lugar:

        flash(
            "Debes indicar el lugar.",
            "danger"
        )

        return redirect(
            url_for("reportar")
        )


    if not ubicacion:

        flash(
            "Debes indicar la ubicación.",
            "danger"
        )

        return redirect(
            url_for("reportar")
        )


    nombre_fotografia = None


    if fotografia and fotografia.filename:

        if not archivo_permitido(
            fotografia.filename
        ):

            flash(
                "El formato de imagen no está permitido.",
                "danger"
            )

            return redirect(
                url_for("reportar")
            )


        extension = fotografia.filename.rsplit(
            ".",
            1
        )[1].lower()


        nombre_fotografia = (
            str(uuid.uuid4())
            + "."
            + extension
        )


        ruta = os.path.join(
            app.config["UPLOAD_FOLDER"],
            secure_filename(
                nombre_fotografia
            )
        )


        fotografia.save(
            ruta
        )


    conexion = conectar_bd()

    cursor = conexion.cursor()


    cursor.execute(
        """
        INSERT INTO reportes
        (
            nombre_lugar,
            ubicacion,
            latitud,
            longitud,
            tipo_contaminacion,
            nivel_afectacion,
            descripcion,
            fotografia,
            usuario_id
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            nombre_lugar,
            ubicacion,
            latitud,
            longitud,
            tipo_contaminacion,
            nivel_afectacion,
            descripcion,
            nombre_fotografia,
            session["usuario_id"]
        )
    )


    conexion.commit()


    cerrar_conexion(
        cursor,
        conexion
    )


    flash(
        "Reporte registrado correctamente.",
        "success"
    )


    return redirect(
        url_for("reportes")
    )


# ============================================================
# REPORTES
# ============================================================

@app.route("/reportes")
def reportes():

    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )


    cursor.execute(
        """
        SELECT
            r.id,
            r.nombre_lugar,
            r.ubicacion,
            r.latitud,
            r.longitud,
            r.tipo_contaminacion,
            r.nivel_afectacion,
            r.descripcion,
            r.fotografia,
            r.fecha_reporte,
            u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u
            ON r.usuario_id = u.id
        ORDER BY r.fecha_reporte DESC
        """
    )


    reportes = cursor.fetchall()


    cerrar_conexion(
        cursor,
        conexion
    )


    return render_template(
        "reportes.html",
        reportes=reportes
    )


# ============================================================
# MAPAS
# ============================================================

@app.route("/mapas")
def mapas():

    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )


    cursor.execute(
        """
        SELECT
            r.id,
            r.nombre_lugar,
            r.ubicacion,
            r.latitud,
            r.longitud,
            r.tipo_contaminacion,
            r.nivel_afectacion,
            r.descripcion,
            r.fotografia,
            r.fecha_reporte,
            u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u
            ON r.usuario_id = u.id
        WHERE r.latitud IS NOT NULL
        AND r.longitud IS NOT NULL
        ORDER BY r.fecha_reporte DESC
        """
    )


    reportes = cursor.fetchall()


    cerrar_conexion(
        cursor,
        conexion
    )


    return render_template(
        "mapas.html",
        reportes=reportes
    )

# ============================================================
# API DE REPORTES PARA EL MAPA DEL ADMIN
# ============================================================

@app.route("/api/reportes")
def api_reportes():

    if not usuario_logueado():

        return jsonify({
            "error": "No autorizado"
        }), 401

    if not es_admin():

        return jsonify({
            "error": "No tienes permisos"
        }), 403

    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            r.id,
            r.nombre_lugar,
            r.ubicacion,
            r.barrio,
            r.latitud,
            r.longitud,
            r.tipo_contaminacion,
            r.nivel_afectacion,
            r.descripcion,
            r.fotografia,
            r.fecha_reporte,
            u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u
            ON r.usuario_id = u.id
        WHERE r.latitud IS NOT NULL
        AND r.longitud IS NOT NULL
        ORDER BY r.fecha_reporte DESC
        """
    )

    reportes = cursor.fetchall()

    cerrar_conexion(
        cursor,
        conexion
    )

    return jsonify(reportes)
# ============================================================
# ELIMINAR REPORTE
# ============================================================

@app.route(
    "/eliminar-reporte/<int:id>",
    methods=["POST"]
)
def eliminar_reporte(id):

    if not usuario_logueado():

        return redirect(
            url_for("login")
        )


    if not es_admin():

        flash(
            "No tienes permisos para eliminar reportes.",
            "danger"
        )

        return redirect(
            url_for("reportes")
        )


    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )


    cursor.execute(
        """
        SELECT fotografia
        FROM reportes
        WHERE id = %s
        """,
        (id,)
    )


    reporte = cursor.fetchone()


    if reporte and reporte["fotografia"]:

        ruta = os.path.join(
            app.config["UPLOAD_FOLDER"],
            reporte["fotografia"]
        )

        if os.path.exists(ruta):

            os.remove(ruta)


    cursor.execute(
        """
        DELETE FROM reportes
        WHERE id = %s
        """,
        (id,)
    )


    conexion.commit()


    cerrar_conexion(
        cursor,
        conexion
    )


    flash(
        "Reporte eliminado correctamente.",
        "success"
    )


    return redirect(
        url_for("reportes")
    )


# ============================================================
# JORNADAS
# ============================================================

@app.route("/jornadas")
def jornadas():

    try:

        conexion = conectar_bd()

        cursor = conexion.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                titulo,
                descripcion,
                lugar,
                fecha,
                hora,
                cupos,
                estado
            FROM jornadas
            ORDER BY fecha ASC, hora ASC
            """
        )


        jornadas_data = cursor.fetchall()


        cerrar_conexion(
            cursor,
            conexion
        )

    except mysql.connector.Error:

        jornadas_data = []


    return render_template(
        "jornadas.html",
        jornadas=jornadas_data
    )


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin")
def admin():

    if not usuario_logueado():

        return redirect(
            url_for("login")
        )


    if not es_admin():

        flash(
            "No tienes permisos para acceder.",
            "danger"
        )

        return redirect(
            url_for("perfil")
        )


    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )


    cursor.execute(
        """
        SELECT
            r.id,
            r.nombre_lugar,
            r.ubicacion,
            r.tipo_contaminacion,
            r.nivel_afectacion,
            r.descripcion,
            r.fotografia,
            r.fecha_reporte,
            u.nombre AS usuario_nombre,
            u.email AS usuario_email
        FROM reportes r
        LEFT JOIN usuarios u
            ON r.usuario_id = u.id
        ORDER BY r.fecha_reporte DESC
        """
    )


    reportes = cursor.fetchall()


    cursor.execute(
        """
        SELECT
            id,
            nombre,
            email,
            fecha_registro,
            rol
        FROM usuarios
        ORDER BY fecha_registro DESC
        """
    )


    usuarios = cursor.fetchall()


    cerrar_conexion(
        cursor,
        conexion
    )


    return render_template(
        "admin.html",
        reportes=reportes,
        usuarios=usuarios
    )


# ============================================================
# CREAR JORNADA
# ============================================================

@app.route(
    "/crear-jornada",
    methods=["POST"]
)
def crear_jornada():

    if not usuario_logueado():

        return redirect(
            url_for("login")
        )


    if not es_admin():

        flash(
            "Solo el administrador puede crear jornadas.",
            "danger"
        )

        return redirect(
            url_for("jornadas")
        )


    titulo = request.form.get(
        "titulo",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()

    lugar = request.form.get(
        "lugar",
        ""
    ).strip()

    fecha = request.form.get(
        "fecha",
        ""
    )

    hora = request.form.get(
        "hora",
        ""
    )

    cupos = request.form.get(
        "cupos",
        "0"
    )


    conexion = conectar_bd()

    cursor = conexion.cursor()


    try:

        cursor.execute(
            """
            INSERT INTO jornadas
            (
                titulo,
                descripcion,
                lugar,
                fecha,
                hora,
                cupos,
                estado
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'disponible'
            )
            """,
            (
                titulo,
                descripcion,
                lugar,
                fecha,
                hora,
                cupos
            )
        )


        conexion.commit()


        flash(
            "Jornada creada correctamente.",
            "success"
        )


    except mysql.connector.Error as error:

        conexion.rollback()


        flash(
            f"No se pudo crear la jornada: {error}",
            "danger"
        )


    cerrar_conexion(
        cursor,
        conexion
    )


    return redirect(
        url_for("jornadas")
    )


# ============================================================
# ELIMINAR JORNADA
# ============================================================

@app.route(
    "/eliminar-jornada/<int:id>",
    methods=["POST"]
)
def eliminar_jornada(id):

    if not usuario_logueado():

        return redirect(
            url_for("login")
        )


    if not es_admin():

        flash(
            "Solo el administrador puede eliminar jornadas.",
            "danger"
        )

        return redirect(
            url_for("jornadas")
        )


    conexion = conectar_bd()

    cursor = conexion.cursor()


    cursor.execute(
        """
        DELETE FROM jornadas
        WHERE id = %s
        """,
        (id,)
    )


    conexion.commit()


    cerrar_conexion(
        cursor,
        conexion
    )


    flash(
        "Jornada eliminada correctamente.",
        "success"
    )


    return redirect(
        url_for("jornadas")
    )


    return jsonify(reportes)

@app.route("/api/reportes-publicos")
def api_reportes_publicos():

    conexion = conectar_bd()

    cursor = conexion.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            r.id,
            r.nombre_lugar,
            r.ubicacion,
            r.barrio,
            r.latitud,
            r.longitud,
            r.tipo_contaminacion,
            r.nivel_afectacion,
            r.descripcion,
            r.fotografia,
            r.fecha_reporte,
            u.nombre AS usuario_nombre
        FROM reportes r
        LEFT JOIN usuarios u
            ON r.usuario_id = u.id
        WHERE r.latitud IS NOT NULL
        AND r.longitud IS NOT NULL
        ORDER BY r.fecha_reporte DESC
    """)

    reportes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return jsonify(reportes)
# ============================================================
# INICIAR APLICACIÓN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )