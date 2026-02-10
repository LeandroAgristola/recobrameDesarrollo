/**
 * Inicialización de Popovers para CRM
 * Muestra Fecha y Estado al pasar el mouse por los ticks.
 */

document.addEventListener('DOMContentLoaded', function() {
    inicializarPopovers();
});

function inicializarPopovers() {
    // Seleccionamos todos los elementos con data-bs-toggle="popover"
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'hover', // Mostrar al pasar el mouse
            html: true,       // Permitir HTML en el contenido
            placement: 'top',
            customClass: 'crm-popover' // Clase para estilos personalizados si quieres
        });
    });
}