// ============================================================
// MAPA DE ZONAS REPORTADAS
// ============================================================

const mapaReportes = L.map("mapa-reportes").setView(
    [8.7575, -75.8896],
    13
);


// ============================================================
// MAPA BASE
// ============================================================

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
    }
).addTo(mapaReportes);


// ============================================================
// CARGAR REPORTES
// ============================================================

async function cargarReportes() {

    try {

        const respuesta = await fetch(
            "/api/reportes-publicos"
        );

        if (!respuesta.ok) {
            throw new Error(
                "No se pudieron cargar los reportes"
            );
        }

        const reportes = await respuesta.json();

        console.log("Reportes:", reportes);

        const marcadores = [];


        // ========================================================
        // RECORRER REPORTES
        // ========================================================

        reportes.forEach(function (reporte) {

            const latitud = parseFloat(
                reporte.latitud
            );

            const longitud = parseFloat(
                reporte.longitud
            );


            // No mostrar reportes sin coordenadas
            if (
                Number.isNaN(latitud) ||
                Number.isNaN(longitud)
            ) {
                return;
            }


            // ====================================================
            // MARCADOR
            // ====================================================

            const marcador = L.marker(
                [latitud, longitud]
            ).addTo(mapaReportes);


            // ====================================================
            // DATOS
            // ====================================================

            const zona =
                reporte.nombre_lugar ||
                "Zona reportada";

            const usuario =
                reporte.usuario_nombre ||
                "Usuario";

            const direccion =
                reporte.ubicacion ||
                "No registrada";

            const barrio =
                reporte.barrio ||
                "No registrado";

            const contaminacion =
                reporte.tipo_contaminacion ||
                "No registrada";

            const nivel =
                reporte.nivel_afectacion ||
                "No registrado";

            const descripcion =
                reporte.descripcion ||
                "Sin descripción";


            // ====================================================
            // COLOR DEL NIVEL
            // ====================================================

            let colorNivel = "#198754";

            const nivelTexto =
                nivel.toLowerCase();


            if (
                nivelTexto.includes("medio")
            ) {

                colorNivel = "#ffc107";

            } else if (
                nivelTexto.includes("alto")
            ) {

                colorNivel = "#fd7e14";

            } else if (
                nivelTexto.includes("critico") ||
                nivelTexto.includes("crítico")
            ) {

                colorNivel = "#dc3545";

            }


            // ====================================================
            // FOTO
            // ====================================================

            let foto = "";

            if (reporte.fotografia) {

                foto = `
                    <img
                        src="/static/uploads/${reporte.fotografia}"
                        alt="Foto del reporte"
                        style="
                            width:100%;
                            height:150px;
                            object-fit:cover;
                            border-radius:10px;
                            margin-top:10px;
                        "
                    >
                `;

            }


            // ====================================================
            // POPUP
            // ====================================================

            const popup = `
                <div
                    style="
                        width:280px;
                        font-family:Arial,sans-serif;
                    "
                >

                    <h5
                        style="
                            font-weight:bold;
                            margin-bottom:10px;
                        "
                    >
                        📍 ${zona}
                    </h5>


                    <div
                        style="
                            background:${colorNivel};
                            color:white;
                            padding:6px 10px;
                            border-radius:20px;
                            display:inline-block;
                            font-weight:bold;
                            margin-bottom:12px;
                        "
                    >
                        ${nivel}
                    </div>


                    <hr>


                    <p>
                        <strong>👤 Reportado por:</strong><br>
                        ${usuario}
                    </p>


                    <p>
                        <strong>📍 Dirección:</strong><br>
                        ${direccion}
                    </p>


                    <p>
                        <strong>🏘️ Barrio:</strong><br>
                        ${barrio}
                    </p>


                    <p>
                        <strong>⚠️ Contaminación:</strong><br>
                        ${contaminacion}
                    </p>


                    <p>
                        <strong>📝 Descripción:</strong><br>
                        ${descripcion}
                    </p>


                    ${foto}

                </div>
            `;


            marcador.bindPopup(
                popup
            );


            marcadores.push(
                marcador
            );

        });


        // ========================================================
        // AJUSTAR MAPA
        // ========================================================

        if (marcadores.length > 0) {

            const grupo =
                L.featureGroup(
                    marcadores
                );

            mapaReportes.fitBounds(
                grupo.getBounds(),
                {
                    padding: [40, 40]
                }
            );

        }


        // ========================================================
        // CONTADOR
        // ========================================================

        const contador =
            document.getElementById(
                "contador-reportes"
            );


        if (contador) {

            contador.textContent =
                `${marcadores.length} zona(s) reportada(s)`;

        }

    } catch (error) {

        console.error(
            "Error cargando reportes:",
            error
        );


        const contador =
            document.getElementById(
                "contador-reportes"
            );


        if (contador) {

            contador.textContent =
                "Error al cargar los reportes";

            contador.classList.remove(
                "bg-primary"
            );

            contador.classList.add(
                "bg-danger"
            );

        }

    }

}


// ============================================================
// INICIAR
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        cargarReportes();

    }
);