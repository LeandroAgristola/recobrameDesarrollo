/**
 * Lógica de Seguimiento CRM
 * Maneja ticks, estados, fechas de compromiso y actualización de popovers.
 */

let tickActual = null;
let expedienteIdActual = null;
let accionActual = null;

// 1. MANEJO DE TICKS Y MODAL
function manejarTick(checkbox, expId, tipoAccion) {
    if (checkbox.checked) {
        tickActual = checkbox;
        expedienteIdActual = expId;
        accionActual = tipoAccion;
        
        // Resetear modal
        document.getElementById('selectEstadoTick').value = "";
        document.getElementById('divFechaPromesa').classList.add('d-none');
        document.getElementById('inputFechaPromesa').value = "";
        
        const modal = new bootstrap.Modal(document.getElementById('modalEstadoTick'));
        modal.show();
    } else {
        // Al desmarcar, enviamos valor false
        enviarActualizacion(expId, tipoAccion, false, null, null);
    }
}

// Detectar cambio en el select del modal para lógica de "PAGARA"
document.addEventListener('DOMContentLoaded', function() {
    const selectEstado = document.getElementById('selectEstadoTick');
    if(selectEstado){
        selectEstado.addEventListener('change', function() {
            const divFecha = document.getElementById('divFechaPromesa');
            if (this.value === 'PAGARA') {
                divFecha.classList.remove('d-none');
            } else {
                divFecha.classList.add('d-none');
                document.getElementById('inputFechaPromesa').value = "";
            }
        });
    }
    // Inicializar popovers al cargar
    initPopovers();
});

function confirmarEstadoTick() {
    const select = document.getElementById('selectEstadoTick');
    const estado = select.value;
    const fechaPromesa = document.getElementById('inputFechaPromesa').value;

    if (!estado) {
        mostrarToast("Selecciona un resultado.", "warning");
        return;
    }

    if (estado === 'PAGARA' && !fechaPromesa) {
        mostrarToast("Indica la fecha de compromiso.", "warning");
        return;
    }

    const modalEl = document.getElementById('modalEstadoTick');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();

    enviarActualizacion(expedienteIdActual, accionActual, true, estado, fechaPromesa);
}

function cancelarEstadoTick() {
    if (tickActual) tickActual.checked = false;
}

// 2. AJAX PRINCIPAL
function enviarActualizacion(expId, accion, valor, nuevoEstado, fechaPromesa) {
    fetch('/crm/api/actualizar-seguimiento/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'expediente_id': expId,
            'tipo_accion': accion,
            'valor': valor,
            'nuevo_estado': nuevoEstado,
            'fecha_promesa': fechaPromesa
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // Actualizar Fecha Último Mensaje
            const fechaUltSpan = document.getElementById(`fecha-ult-${expId}`);
            if (fechaUltSpan) fechaUltSpan.innerText = data.fecha_ultimo;

            // Actualizar Estado General en la tabla
            const estadoSpan = document.getElementById(`estado-texto-${expId}`);
            if (estadoSpan) estadoSpan.innerText = data.estado_legible;
            
            // Actualizar Fecha Pago Promesa
            const fechaPagoSpan = document.getElementById(`fecha-pago-${expId}`);
            if (fechaPagoSpan) fechaPagoSpan.innerText = data.fecha_promesa_legible || "-";

            // --- ACTUALIZAR CONTENIDO DEL POPOVER DINÁMICAMENTE ---
            const tickContainer = tickActual ? tickActual.closest('[data-bs-toggle="popover"]') : null;
            if (tickContainer) {
                const nuevoContenido = `<strong>Fecha:</strong> ${data.fecha_ultimo}<br><strong>Estado:</strong> ${data.estado_tick_legible}`;
                tickContainer.setAttribute('data-bs-content', nuevoContenido);
                
                // Reinicializar el popover específico para que tome el nuevo contenido
                const pop = bootstrap.Popover.getInstance(tickContainer);
                if (pop) pop.dispose();
                new bootstrap.Popover(tickContainer);
            }

            mostrarToast("Gestión registrada correctamente", "success");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarToast("Error al procesar la solicitud", "danger");
    });
}

// 3. FUNCIONES DE APOYO
function initPopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.map(function (el) {
        return new bootstrap.Popover(el, { trigger: 'hover', html: true });
    });
}

function getCookie(name) {
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

// Función para Comentarios Estándar
function actualizarComentario(select, expId) {
    fetch('/crm/api/actualizar-comentario/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ 'expediente_id': expId, 'comentario': select.value })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'ok') mostrarToast("Comentario actualizado", "success");
    });
}

// Función para cambiar Agente
function cambiarAgente(select, expId) {
    fetch('/crm/api/actualizar-agente/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ 'expediente_id': expId, 'agente_id': select.value })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'ok') mostrarToast("Agente asignado", "success");
    });
}