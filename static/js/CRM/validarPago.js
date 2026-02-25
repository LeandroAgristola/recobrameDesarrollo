/**
 * Valida el monto ingresado antes de enviar el formulario.
 * No bloquea pagos superiores a la deuda, pero lanza una advertencia.
 */
function validarPagoLocal(event, expId, deudaMax) {
    const inputMonto = document.getElementById(`input-monto-${expId}`);
    const errorDiv = document.getElementById(`error-pago-${expId}`);
    
    if (!inputMonto || !errorDiv) return true;

    const montoIngresado = parseFloat(inputMonto.value);
    
    // Resetear estados previos
    errorDiv.innerHTML = '';
    inputMonto.classList.remove('is-invalid');

    // Validación estricta: No permitir 0 o negativos
    if (montoIngresado <= 0) {
        event.preventDefault();
        errorDiv.innerHTML = `
            <div class="alert alert-warning d-flex align-items-center py-2 mb-3" role="alert">
                <i class="fa-solid fa-triangle-exclamation me-2"></i>
                <div class="small">El monto ingresado debe ser mayor a 0€.</div>
            </div>
        `;
        inputMonto.classList.add('is-invalid');
        inputMonto.focus();
        return false;
    }

    // Validación flexible: Advertencia si paga más que la deuda exigible
    // (Usamos un margen de 0.01 por posibles redondeos)
    if (montoIngresado > (deudaMax + 0.01)) {
        // Lanzamos un modal de confirmación del navegador
        const confirmar = confirm(`⚠️ ATENCIÓN:\n\nEl monto ingresado (${montoIngresado}€) es superior a la deuda pendiente actual (${deudaMax}€).\n\n¿Estás seguro de que deseas registrar este pago de todas formas (ej. cancelación total de la financiación)?`);
        
        if (!confirmar) {
            // Si el agente cancela la advertencia, detenemos el envío
            event.preventDefault(); 
            inputMonto.focus();
            return false;
        }
        // Si el agente hace clic en "Aceptar", no hacemos el preventDefault
        // y el formulario se envía al servidor con éxito.
    }

    return true;
}