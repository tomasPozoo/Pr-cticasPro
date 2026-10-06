function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function () {
    const selectRegion = document.getElementById('filtro-region');

    if (selectRegion) {
        selectRegion.addEventListener('change', function () {
            const regionSeleccionada = this.value;

            fetch('/api/verificar-region/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ region: regionSeleccionada })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.permitido && data.requiere_premium) {
                    // Si no tiene permiso, regresar el select a su región base y mostrar el modal
                    selectRegion.value = data.region_base;
                    const elRegionBase = document.getElementById('texto-region-base');
                    if (elRegionBase) elRegionBase.innerText = data.region_base;
                    
                    document.getElementById('modal-premium').classList.remove('hidden');
                } else {
                    // Si está permitido, mover el mapa
                    if (typeof filtrarOfertasPorRegion === 'function') {
                        filtrarOfertasPorRegion(regionSeleccionada);
                    }
                }
            })
            .catch(err => console.error("Error al verificar región:", err));
        });
    }
});

function cerrarModalPremium() {
    document.getElementById('modal-premium').classList.add('hidden');
}

// Redirigir a la vista de Checkout
function irAPagarSuscripcion() {
    window.location.href = '/suscripcion/checkout/';
}