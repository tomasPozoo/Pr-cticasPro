
let modoActual = 'carta';

// Obtiene el token CSRF desde el DOM o Cookie
function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        return csrfInput.value;
    }
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Alterna entre modo 'carta' y modo 'revision'
function cambiarModo(modo) {
    modoActual = modo;
    const btnCarta = document.getElementById('btnModoCarta');
    const btnRevision = document.getElementById('btnModoRevision');
    const tituloResultado = document.getElementById('tituloResultado');

    if (modo === 'carta') {
        if (btnCarta) btnCarta.className = "py-2.5 text-xs font-bold rounded-lg transition bg-white text-blue-600 shadow-sm";
        if (btnRevision) btnRevision.className = "py-2.5 text-xs font-bold rounded-lg transition text-gray-600 hover:text-gray-900";
        if (tituloResultado) tituloResultado.innerText = "Carta de Presentación Generada";
    } else {
        if (btnRevision) btnRevision.className = "py-2.5 text-xs font-bold rounded-lg transition bg-white text-blue-600 shadow-sm";
        if (btnCarta) btnCarta.className = "py-2.5 text-xs font-bold rounded-lg transition text-gray-600 hover:text-gray-900";
        if (tituloResultado) tituloResultado.innerText = "Sugerencias y Análisis del CV";
    }
}

// Solicitud AJAX a la API de ProBot CV IA
async function generarContenidoIA(endpointUrl) {
    const carrera = document.getElementById('carrera')?.value || '';
    const puesto = document.getElementById('puesto_objetivo')?.value || '';
    const habilidades = document.getElementById('habilidades')?.value || '';
    const experiencia = document.getElementById('experiencia')?.value || '';

    if (!habilidades && !experiencia) {
        alert("Por favor completa tus habilidades o experiencia/proyectos para que la IA pueda ayudarte.");
        return;
    }

    const estadoVacio = document.getElementById('estadoVacio');
    const contenidoGenerado = document.getElementById('contenidoGenerado');
    const loaderIA = document.getElementById('loaderIA');
    const btnCopiar = document.getElementById('btnCopiar');

    // Estados UI
    if (estadoVacio) estadoVacio.classList.add('hidden');
    if (contenidoGenerado) contenidoGenerado.classList.add('hidden');
    if (loaderIA) loaderIA.classList.remove('hidden');
    if (btnCopiar) btnCopiar.classList.add('hidden');

    try {
        const response = await fetch(endpointUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                tipo: modoActual,
                carrera: carrera,
                puesto_objetivo: puesto,
                habilidades: habilidades,
                experiencia: experiencia
            })
        });

        const data = await response.json();

        if (loaderIA) loaderIA.classList.add('hidden');

        if (data.success) {
            if (contenidoGenerado) {
                contenidoGenerado.innerText = data.resultado;
                contenidoGenerado.classList.remove('hidden');
            }
            if (btnCopiar) btnCopiar.classList.remove('hidden');
        } else {
            alert(data.error || "Ocurrió un error al generar la respuesta.");
            if (estadoVacio) estadoVacio.classList.remove('hidden');
        }

    } catch (e) {
        if (loaderIA) loaderIA.classList.add('hidden');
        if (estadoVacio) estadoVacio.classList.remove('hidden');
        alert("Error de conexión con el servidor: " + e);
    }
}

// Copiar texto al portapapeles
function copiarResultado() {
    const contenidoGenerado = document.getElementById('contenidoGenerado');
    if (!contenidoGenerado) return;

    const texto = contenidoGenerado.innerText;
    navigator.clipboard.writeText(texto).then(() => {
        const btn = document.getElementById('btnCopiar');
        if (btn) {
            btn.innerText = "¡Copiado! ✓";
            setTimeout(() => {
                btn.innerText = "📋 Copiar";
            }, 2000);
        }
    });
}