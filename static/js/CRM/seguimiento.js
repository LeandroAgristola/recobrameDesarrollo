// static/js/CRM/seguimiento.js

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
        document.getElementById('divFechaPromesa').classList.add('d-none'); // Ocultar fecha
        document.getElementById('inputFechaPromesa').value = "";
        
        const modal = new bootstrap.Modal(document.getElementById('modalEstadoTick'));
        modal.show();
    } else {
        // Desmarcar sin modal
        enviarActualizacion(expId, tipoAccion, false, null, null);
    }
}

// Detectar cambio en el select del modal para mostrar fecha si es PAGARA
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
});

function confirmarEstadoTick() {
    const select = document.getElementById('selectEstadoTick');
    const estado = select.value;
    const fechaPromesa = document.getElementById('inputFechaPromesa').value;

    if (!estado) {
        mostrarToast("Por favor selecciona un resultado.", 'warning');
        return;
    }

    // Validación: Si es PAGARA, la fecha es obligatoria
    if (estado === 'PAGARA' && !fechaPromesa) {
        mostrarToast("Debes indicar una fecha de compromiso.", 'warning');
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

// 2. MANEJO DE COMENTARIOS ESTANDARIZADOS (ONCHANGE)
function actualizarComentario(select, expId) {
    const valor = select.value;
    
    fetch('/crm/api/actualizar-comentario/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'expediente_id': expId,
            'comentario': valor
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status !== 'ok') mostrarToast("Error al guardar comentario", 'danger');
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarToast("Error de conexión", 'danger');
    });
}

// 3. LÓGICA DE AGENTE
function cambiarAgente(select, expId) {
    const nuevoAgenteId = select.value;
    
    // Feedback visual inmediato (deshabilitar mientras carga)
    select.disabled = true;

    fetch('/crm/api/actualizar-agente/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'expediente_id': expId,
            'agente_id': nuevoAgenteId
        })
    })
    .then(response => response.json())
    .then(data => {
        select.disabled = false;
        if (data.status === 'ok') {
            mostrarToast(`Agente asignado: ${data.agente_nombre}`, 'success');
        } else {
            mostrarToast("Error al asignar agente", 'danger');
        }
    })
    .catch(error => {
        select.disabled = false;
        console.error('Error:', error);
        mostrarToast("Error de conexión", 'danger');
    });
}

// 4. AJAX PRINCIPAL (Actualizado para mostrar Toast)
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
            // Actualizar UI
            const fechaSpan = document.getElementById(`fecha-ult-${expId}`);
            if (fechaSpan) fechaSpan.innerText = data.fecha_ultimo;

            if (nuevoEstado) {
                 const estadoSpan = document.getElementById(`estado-texto-${expId}`);
                 if (estadoSpan) estadoSpan.innerText = data.estado_legible;
            }
            
            // CORRECCION F. PAGO: Aseguramos que el ID exista y el dato venga
            const fechaPagoSpan = document.getElementById(`fecha-pago-${expId}`);
            if (fechaPagoSpan && data.fecha_promesa_legible) {
                fechaPagoSpan.innerText = data.fecha_promesa_legible;
                // Opcional: Agregar clase visual para resaltar
                fechaPagoSpan.classList.add('text-success', 'fw-bold');
            }

            // Notificación de éxito
            mostrarToast("Gestión guardada correctamente", 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarToast("Error al guardar la gestión", 'danger');
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