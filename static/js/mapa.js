var map;
var todosLosMarcadores = [];

function initMapa(ofertas) {
    // 1. Inicializar el mapa centrado en Santiago (si no se ha creado aún)
    if (!map) {
        map = L.map('map').setView([-33.4489, -70.6693], 11);

        // Cargar tiles de Esri
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS'
        }).addTo(map);
    }

    // Limpiar marcadores previos si existen
    todosLosMarcadores.forEach(m => map.removeLayer(m));
    todosLosMarcadores = [];

    // 2. Dibujar y registrar los marcadores
    if (Array.isArray(ofertas)) {
        ofertas.forEach(oferta => {
            var lat = parseFloat(oferta.latitud) || -33.4489;
            var lng = parseFloat(oferta.longitud) || -70.6693;

            var marker = L.marker([lat, lng]);

            // IMPORTANTE: Guardamos la carrera en la propiedad del marcador
            marker.carrera = oferta.carrera || "";

            marker.bindPopup(`
                <b>${oferta.titulo}</b><br>
                🏢 ${oferta.empresa_nombre}<br>
                🎓 <small class="text-gray-600">${oferta.carrera || 'Carrera no especificada'}</small><br>
                <a href="${oferta.url_detalle}" class="text-blue-600 text-sm mt-1 inline-block font-semibold">Ver detalle</a>
            `);

            marker.addTo(map);
            
            // Guardamos la referencia en la lista global para poder filtrarlo
            todosLosMarcadores.push(marker);
        });
    }

    // Activar el filtro por carrera
    configurarFiltroCarrera();
}

// Escuchar cambios en el selector de carreras
function configurarFiltroCarrera() {
    const selectorCarrera = document.getElementById('filtro-carrera');
    if (!selectorCarrera || selectorCarrera.dataset.listener === "true") return;

    // Marcamos que ya tiene el evento activo para no duplicarlo
    selectorCarrera.dataset.listener = "true";

    selectorCarrera.addEventListener('change', function() {
        var carreraSeleccionada = this.value;

        todosLosMarcadores.forEach(function(marker) {
            if (carreraSeleccionada === "" || marker.carrera === carreraSeleccionada) {
                map.addLayer(marker); // Mostrar si coincide o si elige "Todas"
            } else {
                map.removeLayer(marker); // Ocultar si no coincide
            }
        });
    });
}

// Cambio de región por coordenadas
function filtrarOfertasPorRegion(regionNombre) {
    const select = document.getElementById('filtro-region');
    if (!select) return;

    const selectedOption = select.options[select.selectedIndex];
    const coordsAttr = selectedOption.getAttribute('data-coords');
    
    if (coordsAttr && map) {
        var coords = coordsAttr.split(',');
        map.setView([parseFloat(coords[0]), parseFloat(coords[1])], 11);
    }
}

// Geolocalización del navegador
function centrarMapa() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            if (map) {
                map.setView([position.coords.latitude, position.coords.longitude], 13);
            }
        }, function() {
            alert("No se pudo obtener la ubicación. Verifica los permisos de tu navegador.");
        });
    } else {
        alert("Tu navegador no soporta geolocalización.");
    }
}