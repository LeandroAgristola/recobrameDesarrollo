document.addEventListener('DOMContentLoaded', function() {
    // Buscamos los inputs dentro del modal de nuevo registro
    const modal = document.getElementById('modalNuevoRegistro');
    if (!modal) return;

    const inputNombre = modal.querySelector('input[name="deudor_nombre"]');
    const inputTelefono = modal.querySelector('input[name="deudor_telefono"]');
    const inputEmail = modal.querySelector('input[name="deudor_email"]');
    const inputDni = modal.querySelector('input[name="deudor_dni"]');
    
    // El ID de la empresa lo tomaremos de un atributo data que pondremos en el form
    const form = modal.querySelector('form');
    const empresaId = form.getAttribute('data-empresa-id');

    if (inputNombre) {
        inputNombre.addEventListener('blur', function() {
            const nombre = this.value.trim();
            
            if (nombre.length > 3) {
                fetch(`/crm/buscar-antecedentes/?nombre=${encodeURIComponent(nombre)}&empresa_id=${empresaId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Autocompletamos solo si los campos están vacíos
                            if (!inputTelefono.value) inputTelefono.value = data.datos.telefono;
                            if (!inputEmail.value) inputEmail.value = data.datos.email;
                            if (!inputDni.value) inputDni.value = data.datos.dni;
                            
                            // Notificación visual opcional (puedes usar tu sistema de toasts)
                            console.log("Datos recuperados de registros anteriores");
                        }
                    })
                    .catch(error => console.error('Error en autocompletado:', error));
            }
        });
    }
});