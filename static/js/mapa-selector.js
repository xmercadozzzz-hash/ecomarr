document.addEventListener("DOMContentLoaded", function () {

    const elementoMapa = document.getElementById("map");

    if (!elementoMapa) {
        console.error("No existe el elemento #map.");
        return;
    }

    // Coordenadas iniciales: Montería
    const mapa = L.map("map").setView(
        [8.7575, -75.8896],
        13
    );

    // OpenStreetMap
    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(mapa);


    let marcador = null;


    // -----------------------------------------
    // CUANDO EL USUARIO HACE CLIC EN EL MAPA
    // -----------------------------------------

    mapa.on("click", function (evento) {

        const latitud = evento.latlng.lat;
        const longitud = evento.latlng.lng;


        // -------------------------------------
        // CREAR MARCADOR
        // -------------------------------------

        if (!marcador) {

            marcador = L.marker(
                [latitud, longitud],
                {
                    draggable: true
                }
            ).addTo(mapa);

            marcador.bindPopup(
                "Zona afectada seleccionada"
            ).openPopup();


            // ---------------------------------
            // SI ARRASTRA EL MARCADOR
            // ---------------------------------

            marcador.on(
                "dragend",
                function (evento) {

                    const posicion =
                        evento.target.getLatLng();

                    actualizarSeleccion(
                        posicion.lat,
                        posicion.lng
                    );

                }
            );

        } else {

            // Mover marcador existente

            marcador.setLatLng([
                latitud,
                longitud
            ]);

            marcador.openPopup();
        }


        actualizarSeleccion(
            latitud,
            longitud
        );

    });


    // -----------------------------------------
    // ACTUALIZAR UBICACIÓN SELECCIONADA
    // -----------------------------------------

    function actualizarSeleccion(
        latitud,
        longitud
    ) {

        // Guardar coordenadas
        const latitudInput =
            document.getElementById("latitud");

        const longitudInput =
            document.getElementById("longitud");


        if (latitudInput) {

            latitudInput.value =
                latitud.toFixed(8);

        }


        if (longitudInput) {

            longitudInput.value =
                longitud.toFixed(8);

        }


        // Obtener dirección automáticamente

        if (
            typeof obtenerDireccion ===
            "function"
        ) {

            obtenerDireccion(
                latitud,
                longitud
            );

        } else {

            console.error(
                "No se encontró obtenerDireccion(). Revisa geolocalizacion.js."
            );

        }

    }


    // -----------------------------------------
    // HACER QUE LEAFLET RECALCULE EL MAPA
    // -----------------------------------------

    setTimeout(function () {

        mapa.invalidateSize();

    }, 300);

});