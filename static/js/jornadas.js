/* =========================================
   JORNADAS · calendario + filtros
========================================= */

(function () {

    const datos = JSON.parse(
        document.getElementById("datos-jornadas").textContent
    );

    const esAdmin = datos.esAdmin;

    // las canceladas no se pintan en el calendario
    const jornadas = datos.jornadas.filter(function (j) {
        return j.estado !== "cancelada";
    });

    const COLORES = {
        4: "#dc3545",
        3: "#fd7e14",
        2: "#e0a800",
        1: "#19a974"
    };

    const MESES = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ];

    const grid = document.getElementById("calendario");
    const titulo = document.getElementById("mes-titulo");
    const items = document.querySelectorAll(".jornada-item");
    const chips = document.querySelectorAll(".chip");
    const vacio = document.getElementById("sin-jornadas");
    const vacioTexto = document.getElementById("sin-jornadas-texto");
    const listaTitulo = document.getElementById("lista-titulo");
    const botonQuitar = document.getElementById("quitar-dia");
    const inputFecha = document.getElementById("fecha");

    const textoVacioOriginal = vacioTexto.textContent.trim();


    function iso(y, m, d) {
        return y + "-" + String(m + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0");
    }

    function fechaLarga(f) {
        const p = f.split("-");
        return new Date(p[0], p[1] - 1, p[2]).toLocaleDateString("es-CO", {
            weekday: "long", day: "numeric", month: "long"
        });
    }


    const hoy = new Date();
    const hoyISO = iso(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());

    // agrupamos las jornadas por día
    const porDia = {};

    jornadas.forEach(function (j) {
        if (!porDia[j.fecha]) porDia[j.fecha] = [];
        porDia[j.fecha].push(j);
    });

    // mes inicial: hoy (admin) o el mes de la próxima jornada (usuario)
    let anio = hoy.getFullYear();
    let mes = hoy.getMonth();

    if (!esAdmin) {

        const futuras = Object.keys(porDia).filter(function (f) {
            return f >= hoyISO;
        }).sort();

        if (futuras.length && !porDia[hoyISO]) {
            const p = futuras[0].split("-");
            anio = parseInt(p[0], 10);
            mes = parseInt(p[1], 10) - 1;
        }
    }

    let seleccion = null;
    let prioFiltro = "todas";


    /* ---------- calendario ---------- */

    function dibujar() {

        titulo.textContent = MESES[mes] + " " + anio;
        grid.innerHTML = "";

        const offset = (new Date(anio, mes, 1).getDay() + 6) % 7;   // lunes primero
        const dias = new Date(anio, mes + 1, 0).getDate();

        for (let i = 0; i < offset; i++) {
            const v = document.createElement("div");
            v.className = "cal-vacio";
            grid.appendChild(v);
        }

        for (let d = 1; d <= dias; d++) {

            const f = iso(anio, mes, d);
            const lista = porDia[f] || [];
            const pasado = f < hoyISO;

            const b = document.createElement("button");
            b.type = "button";
            b.className = "cal-dia";
            b.textContent = d;

            if (f === hoyISO) b.classList.add("hoy");

            if (lista.length) {

                let max = 1;
                lista.forEach(function (j) { if (j.prioridad > max) max = j.prioridad; });

                b.classList.add("con-jornada");
                b.style.setProperty("--c", COLORES[max]);
                b.title = lista.length + (lista.length === 1 ? " jornada" : " jornadas");

                if (lista.length > 1) {
                    const c = document.createElement("span");
                    c.className = "cal-cuenta";
                    c.textContent = "×" + lista.length;
                    b.appendChild(c);
                }
            }

            if (f === seleccion) {
                b.classList.add(lista.length ? "sel" : "sel-vacio");
            }

            // el usuario solo puede tocar los días con jornada;
            // el admin puede tocar cualquier día que no haya pasado
            b.disabled = esAdmin ? pasado : !lista.length;

            b.addEventListener("click", function () {
                elegirDia(f);
            });

            grid.appendChild(b);
        }
    }

    function elegirDia(f) {

        if (esAdmin) {
            seleccion = f;
            if (inputFecha) inputFecha.value = f;
        } else {
            seleccion = (seleccion === f) ? null : f;
        }

        dibujar();
        filtrar();
    }


    /* ---------- filtros de la lista ---------- */

    function filtrar() {

        let visibles = 0;

        items.forEach(function (el) {

            const okDia = !seleccion || el.dataset.fecha === seleccion;
            const okPrio = prioFiltro === "todas" || el.dataset.prioridad === prioFiltro;

            const mostrar = okDia && okPrio;

            el.classList.toggle("d-none", !mostrar);

            if (mostrar) visibles++;
        });

        listaTitulo.textContent = seleccion
            ? "Jornadas del " + fechaLarga(seleccion)
            : "Todas las jornadas";

        botonQuitar.classList.toggle("d-none", !seleccion);

        vacio.classList.toggle("d-none", visibles > 0);

        if (visibles === 0 && items.length > 0) {
            vacioTexto.textContent = "No hay jornadas con ese filtro.";
        } else {
            vacioTexto.textContent = textoVacioOriginal;
        }
    }


    /* ---------- eventos ---------- */

    document.getElementById("mes-anterior").addEventListener("click", function () {
        mes--;
        if (mes < 0) { mes = 11; anio--; }
        dibujar();
    });

    document.getElementById("mes-siguiente").addEventListener("click", function () {
        mes++;
        if (mes > 11) { mes = 0; anio++; }
        dibujar();
    });

    botonQuitar.addEventListener("click", function () {
        seleccion = null;
        dibujar();
        filtrar();
    });

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
            chips.forEach(function (c) { c.classList.remove("activo"); });
            chip.classList.add("activo");
            prioFiltro = chip.dataset.prio;
            filtrar();
        });
    });


    /* ---------- solo admin: formulario ---------- */

    if (esAdmin) {

        const selReporte = document.getElementById("reporte_id");
        const selNivel = document.getElementById("nivel");
        const inTitulo = document.getElementById("titulo");
        const inLugar = document.getElementById("lugar");

        const NIVELES = { 4: "Crítico", 3: "Alto", 2: "Medio", 1: "Bajo" };

        function aplicarReporte() {

            const op = selReporte.options[selReporte.selectedIndex];
            const prio = op.dataset.prioridad;

            if (prio) {
                // la prioridad viene del reporte; el servidor la vuelve a calcular
                selNivel.value = NIVELES[prio];
                selNivel.disabled = true;
                inLugar.placeholder = op.dataset.lugar;
            } else {
                selNivel.disabled = false;
                inLugar.placeholder = "Punto de encuentro";
            }
        }

        selReporte.addEventListener("change", aplicarReporte);

        document.querySelectorAll(".btn-programar").forEach(function (btn) {

            btn.addEventListener("click", function () {

                selReporte.value = btn.dataset.reporte;
                aplicarReporte();

                const op = selReporte.options[selReporte.selectedIndex];

                if (!inTitulo.value) {
                    inTitulo.value = "Jornada de limpieza · " + op.dataset.lugar;
                }

                document.getElementById("form-jornada")
                    .scrollIntoView({ behavior: "smooth", block: "start" });

                (inputFecha.value ? document.getElementById("hora") : inputFecha).focus();
            });
        });

        // si escribe la fecha a mano, el calendario la sigue
        inputFecha.addEventListener("change", function () {

            if (!inputFecha.value) return;

            seleccion = inputFecha.value;

            const p = seleccion.split("-");
            anio = parseInt(p[0], 10);
            mes = parseInt(p[1], 10) - 1;

            dibujar();
            filtrar();
        });

        // el <select> deshabilitado no se envía: lo activamos al enviar
        // (el servidor ignora "nivel" cuando hay reporte)
        selReporte.form.addEventListener("submit", function () {
            selNivel.disabled = false;
        });
    }


    dibujar();
    filtrar();

})();
