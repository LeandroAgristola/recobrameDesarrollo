let formPendienteDeEnvio = null; // Variable global para recordar qué formulario quiere enviarse

document.addEventListener('DOMContentLoaded', function() {
    // Configurar el botón "Continuar" del modal una sola vez
    const btnConfirmar = document.getElementById('btnConfirmarJS');
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', function() {
            if (formPendienteDeEnvio) {
                // Enviamos el formulario manualmente, saltándonos la validación onsubmit
                formPendienteDeEnvio.submit();
            }
        });
    }
});

function validarFechasExpediente(form) {
    const inputCompra = form.querySelector('input[name="fecha_compra"]');
    const inputImpago = form.querySelector('input[name="fecha_impago"]');

    let fCompra = inputCompra ? inputCompra.value : null;
    let fImpago = inputImpago ? inputImpago.value : null;

    // 1. ERRORES BLOQUEANTES (Toast Rojo)
    if (fCompra && fImpago) {
        if (new Date(fCompra) > new Date(fImpago)) {
            mostrarToast("La fecha de compra no puede ser posterior a la de impago.", "error");
            if(inputImpago) {
                inputImpago.classList.add('is-invalid');
                inputImpago.focus();
            }
            return false; // Bloquea y no sigue
        }
    }

    // 2. ADVERTENCIAS (Modal Amarillo)
    let advertencia = "";
    
    if (!fCompra && !fImpago) {
        advertencia = "Estás guardando un expediente <b>SIN FECHAS</b>.<br>Se tratará como 'Deuda Simple' (exigible hoy).<br><br>¿Deseas continuar?";
    } 
    else if (!fCompra) {
        advertencia = "Falta la <b>FECHA DE COMPRA</b>.<br>¿Deseas guardar el registro así?";
    } 
    else if (!fImpago) {
        advertencia = "Falta la <b>FECHA DE IMPAGO</b>.<br>El sistema asumirá que la deuda venció hoy.<br><br>¿Deseas continuar?";
    }

    // Si hay advertencia, pausamos el envío y mostramos el Modal
    if (advertencia !== "") {
        const modalEl = document.getElementById('modalConfirmacionJS');
        const textoEl = document.getElementById('textoConfirmacionJS');
        
        if (modalEl && textoEl) {
            // Guardamos el formulario en la variable global
            formPendienteDeEnvio = form;
            
            // Ponemos el texto (acepta HTML para las negritas)
            textoEl.innerHTML = advertencia;
            
            // Mostramos el modal usando Bootstrap
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            
            return false; // IMPORTANTE: Detenemos el envío automático
        }
    }

    // Si no hubo errores ni advertencias, dejamos pasar el envío normal
    if (inputImpago) inputImpago.classList.remove('is-invalid');
    return true; 
}