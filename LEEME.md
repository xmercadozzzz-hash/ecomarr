# Ecomar · cómo desplegarlo

## En Render (Web Service)

| Campo | Valor |
|---|---|
| Language | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | Free |

La versión de Python (3.12) la toma del archivo `.python-version`.

### Variables de entorno (Environment)

| Variable | Qué poner |
|---|---|
| `SECRET_KEY` | Un texto largo inventado, por ejemplo `ecomar-2026-x8k2m9q` |
| `DB_HOST` | El host de tu MySQL en la nube (nunca `localhost`) |
| `DB_PORT` | El puerto que te da el proveedor (a veces no es 3306) |
| `DB_USER` | Usuario de la base de datos |
| `DB_PASSWORD` | Contraseña de la base de datos |
| `DB_NAME` | Nombre de la base de datos |
| `ADMIN_EMAIL` | Correo de la cuenta administradora (opcional) |
| `ADMIN_PASSWORD` | Contraseña de esa cuenta (opcional) |

Si tu proveedor te da una URL tipo `mysql://usuario:clave@host:puerto/base`,
puedes poner solo `DATABASE_URL` con esa URL en lugar de las cinco `DB_...`.

Las tablas se crean solas la primera vez que arranca la aplicación.
`base_de_datos.sql` tiene la misma estructura por si quieres crearlas a mano.

## En tu computador

```
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000. Sin variables de entorno usa XAMPP (`root` sin
contraseña y la base `ecomar`), igual que antes.

## Si algo falla

En Render abre la pestaña **Logs**. Los mensajes de la aplicación empiezan
con `ECOMAR:` y dicen qué variable o qué tabla dio problema.
