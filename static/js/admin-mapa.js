// ============================================================
// MAPA DE REPORTES - ADMINISTRADOR
// ============================================================

const mapaAdmin = L.map("mapa-admin").setView(
    [8.7575, -75.8896],
    13
);


// ============================================================
// MAPA BASE DE OPENSTREETMAP
// ============================================================

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
    }
).addTo(mapaAdmin);


// ============================================================
// CARGAR REPORTES DESDE LA BASE DE DATOS
// ============================================================

async function cargarReportesAdmin() {

    try {

        const respuesta = await fetch(
            "/api/reportes"
        );


        if (!respuesta.ok) {

            throw new Error(
                "No se pudieron cargar los reportes"
            );

        }


        const reportes = await respuesta.json();


        const contador =
            document.getElementById(
                "contador-reportes-admin"
            );


        if (contador) {

            contador.textContent =
                `${reportes.length} reportes`;

        }


        const marcadores = [];


        // ====================================================
        // CREAR MARCADORES
        // ====================================================

        reportes.forEach(function(reporte) {

            const latitud =
                parseFloat(reporte.latitud);

            const longitud =
                parseFloat(reporte.longitud);


            // Ignorar reportes sin coordenadas

            if (
                isNaN(latitud) ||
                isNaN(longitud)
            ) {

                return;

            }


            const marcador =
                L.marker(
                    [
                        latitud,
                        longitud
                    ]
                ).addTo(
                    mapaAdmin
                );


            // =================================================
            // FOTOGRAFÍA
            // =================================================

            let imagen = "";


            if (reporte.fotografia) {

                imagen = `
                    <img
                        src="/static/uploads/${reporte.fotografia}"
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


            // =================================================
            // INFORMACIÓN DEL REPORTE
            // =================================================

            const popup = `

                <div style="min-width:260px;">

                    <h5 class="fw-bold mb-3">
                        ${reporte.nombre_lugar || "Lugar reportado"}
                    </h5>


                    <p>
                        <strong>
                            Usuario:
                        </strong>

                        ${reporte.usuario_nombre || "Desconocido"}
                    </p>


                    <p>
                        <strong>
                            Tipo:
                        </strong>

                        ${reporte.tipo_contaminacion || "No registrado"}
                    </p>


                    <p>
                        <strong>
                            Nivel:
                        </strong>

                        ${reporte.nivel_afectacion || "No registrado"}
                    </p>


                    <p>
                        <strong>
                            Barrio:
                        </strong>

                        ${reporte.barrio || "No registrado"}
                    </p>


                    <p>
                        <strong>
                            Ubicación:
                        </strong>

                        ${reporte.ubicacion || "No registrada"}
                    </p>


                    <p>
                        <strong>
                            Descripción:
                        </strong>

                        ${reporte.descripcion || "Sin descripción"}
                    </p>


                    <p>
                        <strong>
                            Coordenadas:
                        </strong>

                        <br>

                        ${latitud.toFixed(6)},
                        ${longitud.toFixed(6)}

                    </p>


                    ${imagen}

                </div>

            `;


            marcador.bindPopup(
                popup
            );


            marcadores.push(
                marcador
            );

        });


        // ====================================================
        // CENTRAR EL MAPA EN LOS REPORTES
        // ====================================================

        if (marcadores.length > 0) {

            const grupo =
                L.featureGroup(
                    marcadores
                );


            mapaAdmin.fitBounds(
                grupo.getBounds(),
                {
                    padding: [
                        30,
                        30
                    ]
                }
            );

        }

    }

    catch (error) {

        console.error(
            "Error cargando reportes:",
            error
        );


        const contador =
            document.getElementById(
                "contador-reportes-admin"
            );


        if (contador) {

            contador.textContent =
                "Error cargando reportes";

        }

    }

}


// ============================================================
// INICIAR MAPA
// ============================================================

cargarReportesAdmin();