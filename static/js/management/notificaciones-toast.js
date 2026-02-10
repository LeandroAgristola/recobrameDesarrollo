/**
 * Sistema de Notificaciones Toast (Estandarizado con App Empresas)
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar toasts que vienen del backend (Django messages)
    var toastElList = [].slice.call(document.querySelectorAll('.toast'))
    var toastList = toastElList.map(function (toastEl) {
        return new bootstrap.Toast(toastEl, { delay: 5000 });
    });
    toastList.forEach(toast => toast.show());
});

// Función para invocar toasts desde JS (AJAX) manteniendo el estilo del layout
function mostrarToast(mensaje, etiquetas) {
    // Contenedor principal definido en layout_management.html
    let toastContainer = document.querySelector('.toast-container');
    
    // Si no existe (raro si extendemos del layout, pero por seguridad), lo creamos igual que en el layout
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Determinar clase de color según la etiqueta (igual que Django tags)
    // success, error, warning, info
    let bgClass = 'bg-primary'; // Default
    let textClass = 'text-white';
    let icon = '';

    if (etiquetas === 'success') {
        bgClass = 'bg-success';
        icon = '<i class="fa-solid fa-check-circle me-2"></i>';
    } else if (etiquetas === 'error' || etiquetas === 'danger') {
        bgClass = 'bg-danger';
        icon = '<i class="fa-solid fa-triangle-exclamation me-2"></i>';
    } else if (etiquetas === 'warning') {
        bgClass = 'bg-warning';
        textClass = 'text-dark'; // Bootstrap warning suele ir mejor con texto oscuro
        icon = '<i class="fa-solid fa-circle-exclamation me-2"></i>';
    } else if (etiquetas === 'info') {
        bgClass = 'bg-info';
        icon = '<i class="fa-solid fa-circle-info me-2"></i>';
    }

    // Estructura HTML EXACTA a la de layout_management.html
    // Nota: Eliminamos estilos inline para confiar en tu CSS global (styleManagement.css)
    const toastHtml = `
        <div class="toast align-items-center ${textClass} ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${icon}${mensaje}
                </div>
                <button type="button" class="btn-close ${textClass === 'text-white' ? 'btn-close-white' : ''} me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Convertir string a elemento DOM
    const template = document.createElement('template');
    template.innerHTML = toastHtml.trim();
    const toastElement = template.content.firstChild;

    // Agregar al contenedor y mostrar
    toastContainer.appendChild(toastElement);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();

    // Limpiar del DOM al ocultarse
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}