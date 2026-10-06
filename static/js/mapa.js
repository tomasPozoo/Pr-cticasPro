// static/js/mapa.js

var map;

function initMapa(ofertas) {
    // 1. Inicializar el mapa centrado en Santiago
    map = L.map('map').setView([-33.4489, -70.6693], 11);

    // 2. Cargar tiles de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // 3. Dibujar los marcadores en el mapa usando los datos recibidos
    if (Array.isArray(ofertas)) {
        ofertas.forEach(oferta => {
            var lat = parseFloat(oferta.latitud) || -33.4489;
            var lng = parseFloat(oferta.longitud) || -70.6693;

            var marker = L.marker([lat, lng]).addTo(map);
            marker.bindPopup(`
                <b>${oferta.titulo}</b><br>
                🏢 ${oferta.empresa_nombre}<br>
                <a href="${oferta.url_detalle}" class="text-blue-600 text-sm mt-1 inline-block">Ver detalle</a>
            `);
        });
    }
}

// Función que ejecuta premium.js cuando el permiso es válido
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