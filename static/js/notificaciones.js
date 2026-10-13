// static/js/notificaciones.js

// Función global para cerrar un toast con animación
function cerrarToast(elemento) {
    if (!elemento) return;
    elemento.classList.add('opacity-0', 'translate-x-8');
    setTimeout(() => {
        elemento.remove();
    }, 300);
}

// Auto-eliminar las alertas flotantes tras 4.5 segundos
document.addEventListener('DOMContentLoaded', function () {
    const toasts = document.querySelectorAll('.toast-item');
    
    toasts.forEach(toast => {
        setTimeout(() => {
            cerrarToast(toast);
        }, 4500);
    });
});