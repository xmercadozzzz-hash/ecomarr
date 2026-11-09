document.addEventListener(
    "DOMContentLoaded",
    function () {

        const formulario =
            document.getElementById(
                "formulario-reporte"
            );


        if (!formulario) {

            console.error(
                "No se encontró el formulario."
            );

            return;
        }


        formulario.addEventListener(
            "submit",
            function (evento) {

                const latitud =
                    document.getElementById(
                        "latitud"
                    );

                const longitud =
                    document.getElementById(
                        "longitud"
                    );

                const ubicacion =
                    document.getElementById(
                        "ubicacion"
                    );


                // --------------------------------
                // VERIFICAR MAPA
                // --------------------------------

                if (
                    !latitud ||
                    !longitud ||
                    !latitud.value ||
                    !longitud.value
                ) {

                    evento.preventDefault();

                    alert(
                        "Primero debes seleccionar la zona afectada en el mapa."
                    );

                    return;
                }


                // --------------------------------
                // VERIFICAR UBICACIÓN
                // --------------------------------

                if (
                    !ubicacion ||
                    !ubicacion.value ||
                    ubicacion.value ===
                    "Obteniendo ubicación..."
                ) {

                    evento.preventDefault();

                    alert(
                        "Espera unos segundos mientras se obtiene la ubicación."
                    );

                    return;
                }


                console.log(
                    "Reporte listo para enviar."
                );

                console.log(
                    "Latitud:",
                    latitud.value
                );

                console.log(
                    "Longitud:",
                    longitud.value
                );

            }
        );

    }
);