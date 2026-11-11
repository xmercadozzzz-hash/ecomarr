async function obtenerDireccion(latitud, longitud) {

    const ubicacionInput = document.getElementById("ubicacion");
    const barrioInput = document.getElementById("barrio");

    if (!ubicacionInput || !barrioInput) {
        console.error("No se encontraron los campos de ubicación.");
        return;
    }

    ubicacionInput.value = "Obteniendo ubicación...";
    barrioInput.value = "Obteniendo barrio...";

    try {

        const respuesta = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitud}&lon=${longitud}&zoom=18&addressdetails=1`,
            {
                headers: {
                    "Accept-Language": "es"
                }
            }
        );

        if (!respuesta.ok) {
            throw new Error("No se pudo consultar la ubicación.");
        }

        const datos = await respuesta.json();

        const direccion = datos.address || {};

        const barrio =
            direccion.neighbourhood ||
            direccion.suburb ||
            direccion.quarter ||
            direccion.residential ||
            direccion.village ||
            "No identificado";

        const ciudad =
            direccion.city ||
            direccion.town ||
            direccion.municipality ||
            direccion.village ||
            "No identificada";

        const calle =
            direccion.road ||
            direccion.pedestrian ||
            direccion.path ||
            "Ubicación seleccionada";

        const numero =
            direccion.house_number || "";

        let direccionCompleta = calle;

        if (numero) {
            direccionCompleta += ` ${numero}`;
        }

        if (ciudad) {
            direccionCompleta += `, ${ciudad}`;
        }

        ubicacionInput.value = direccionCompleta;
        barrioInput.value = barrio;

        console.log("Ubicación:", direccionCompleta);
        console.log("Barrio:", barrio);

    } catch (error) {

        console.error(
            "Error obteniendo ubicación:",
            error
        );

        ubicacionInput.value =
            `Coordenadas: ${latitud.toFixed(6)}, ${longitud.toFixed(6)}`;

        barrioInput.value =
            "No identificado";
    }
}