/**
 * Validación de coherencia de fechas para expedientes
 */
function validarFechasExpediente(form) {
    // Buscamos los inputs dentro del formulario que se está enviando
    const inputCompra = form.querySelector('input[name="fecha_compra"]');
    const inputImpago = form.querySelector('input[name="fecha_impago"]');

    if (inputCompra && inputImpago) {
        const fCompra = inputCompra.value;
        const fImpago = inputImpago.value;

        if (fCompra && fImpago) {
            if (new Date(fCompra) > new Date(fImpago)) {
                // Invocamos tu sistema de Toasts configurado
                mostrarToast("La fecha de compra no puede ser posterior a la de impago.", "error");
                
                // Efecto visual en el campo
                inputImpago.classList.add('is-invalid');
                inputImpago.focus();

                return false; // Bloquea el envío
            }
        }
    }
    
    // Si llegamos aquí, todo está correcto
    if (inputImpago) inputImpago.classList.remove('is-invalid');
    return true; 
}