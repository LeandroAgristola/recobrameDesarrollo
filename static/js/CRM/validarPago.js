/**
 * Valida que el monto ingresado no sea superior a la deuda actual
 * antes de enviar el formulario.
 */
function validarPagoLocal(event, expId, deudaMax) {
    const inputMonto = document.getElementById(`input-monto-${expId}`);
    const errorDiv = document.getElementById(`error-pago-${expId}`);
    
    if (!inputMonto || !errorDiv) return true;

    const montoIngresado = parseFloat(inputMonto.value);
    
    // Resetear estados previos
    errorDiv.innerHTML = '';
    inputMonto.classList.remove('is-invalid');

    // Validación: No permitir más de lo debido
    // (Usamos un margen de 0.01 por posibles redondeos en el float)
    if (montoIngresado > (deudaMax + 0.01)) {
        event.preventDefault(); // Detiene el envío del form
        
        errorDiv.innerHTML = `
            <div class="alert alert-danger d-flex align-items-center py-2 mb-3" role="alert">
                <i class="fa-solid fa-triangle-exclamation me-2"></i>
                <div class="small">
                    <strong> Monto excedido:</strong> El pago no puede ser mayor a ${deudaMax} €).
                </div>
            </div>
        `;
        
        inputMonto.classList.add('is-invalid');
        inputMonto.focus();
        return false;
    }

    // Validación: No permitir 0 o negativos
    if (montoIngresado <= 0) {
        event.preventDefault();
        errorDiv.innerHTML = `
            <div class="alert alert-warning py-2 small mb-3">
                Por favor, ingrese un monto superior a 0 €.
            </div>
        `;
        return false;
    }

    return true; // Todo correcto, se envía el formulario
}