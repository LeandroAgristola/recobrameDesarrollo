document.addEventListener('DOMContentLoaded', function() {
    
    // 1. VARIABLES
    const selectCaso = document.getElementById('id_tipo_caso');
    const divProducto = document.getElementById('div_producto');
    const selectModalidad = document.getElementById('id_modalidad');
    const divFijo = document.getElementById('div_fijo');
    const divTramos = document.getElementById('div_tramos');
    const formRegla = document.getElementById('formRegla');
    const addBtn = document.getElementById('add-tramo');
    const tableBody = document.getElementById('tramosBody');

    // Obtenemos el selector de producto (Asegúrate de ponerlo junto a tus otras variables arriba)
    const selectProducto = document.getElementById('id_tipo_producto');

    // === NUEVA LÓGICA: FILTRO DINÁMICO DE PRODUCTOS (OCULTAR) ===
    function actualizarFiltroProductos() {
        if (!selectCaso || !selectProducto) return;
        
        const caso = selectCaso.value;
        const options = selectProducto.options;
        // Los únicos productos que el sistema permite ceder
        const cesibles = ['', 'TODOS', 'SEQURA_MANUAL', 'AUTOFINANCIACION', 'SEQURA_PASS'];

        for (let i = 0; i < options.length; i++) {
            const val = options[i].value;
            
            // 1. Restauramos todas las opciones a su estado normal
            options[i].disabled = false; 
            options[i].hidden = false;   // La volvemos visible
            
            if (caso === 'IMPAGO') {
                // Si es Impago, OCULTAMOS exclusivamente Sequra Pass
                if (val === 'SEQURA_PASS') {
                    options[i].disabled = true;
                    options[i].hidden = true; // Desaparece de la lista
                    
                    if (selectProducto.value === val) selectProducto.value = '';
                }
            } else if (caso === 'CEDIDO') {
                // Si es Cedido, OCULTAMOS los que NO son cesibles
                if (!cesibles.includes(val)) {
                    options[i].disabled = true;
                    options[i].hidden = true; // Desaparece de la lista
                    
                    if (selectProducto.value === val) selectProducto.value = '';
                }
            }
        }
    }

    // Activamos el evento para que escuche cada vez que cambias de "Impago" a "Cedido"
    if (selectCaso && selectProducto) {
        selectCaso.addEventListener('change', actualizarFiltroProductos);
        actualizarFiltroProductos(); // Lo ejecutamos al cargar la página por si estamos editando
    }

    // FUNCIÓN PARA NOTIFICACIONES TOAST (ERROR)
    function lanzarError(mensaje) {
        const container = document.querySelector('.toast-container');
        if (!container) return;
        const id = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${id}" class="toast show border-start border-4 border-danger" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">
                <div class="toast-header border-0 bg-white">
                    <i class="fa-solid fa-circle-xmark text-danger me-2"></i>
                    <strong class="me-auto text-dark">Validación</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body pt-0 text-dark">${mensaje}</div>
            </div>`;
        container.insertAdjacentHTML('beforeend', toastHtml);
        bootstrap.Toast.getOrCreateInstance(document.getElementById(id)).show();
    }

    // 2. LÓGICA VISIBILIDAD
    function toggleCaso() {
        // Ya no ocultamos el divProducto, porque ahora Cedidos 
        // también puede ser por producto específico o "TODOS"
        if (divProducto) {
            divProducto.style.display = 'block'; 
        }
    }

    function toggleModalidad() {
        if (selectModalidad && selectModalidad.value === 'TRAMOS') {
            if(divFijo) divFijo.style.display = 'none';
            if(divTramos) divTramos.style.display = 'block';
        } else {
            if(divFijo) divFijo.style.display = 'block';
            if(divTramos) divTramos.style.display = 'none';
        }
    }

    if(selectCaso) selectCaso.addEventListener('change', toggleCaso);
    if(selectModalidad) selectModalidad.addEventListener('change', toggleModalidad);
    toggleCaso();
    toggleModalidad();

    // 3. FORMSET DINÁMICO
    const allInputs = document.querySelectorAll('input[type="hidden"]');
    let realTotalInput = null;
    allInputs.forEach(inp => { if(inp.name.endsWith('TOTAL_FORMS')) realTotalInput = inp; });

    if (addBtn && tableBody && realTotalInput) {
        const emptyFormTemplate = document.getElementById('empty-form').innerHTML;
        addBtn.addEventListener('click', function() {
            let formIdx = parseInt(realTotalInput.value);
            let newRowHtml = emptyFormTemplate.replace(/__prefix__/g, formIdx);
            tableBody.insertAdjacentHTML('beforeend', newRowHtml);
            realTotalInput.value = formIdx + 1;
        });

        tableBody.addEventListener('click', function(e) {
            const btn = e.target.closest('.btn-delete-row');
            if (btn) {
                const row = btn.closest('tr');
                const deleteCheckbox = row.querySelector('input[type="checkbox"]');
                if (deleteCheckbox) { 
                    deleteCheckbox.checked = true; 
                    row.style.display = 'none'; 
                } else { row.remove(); }
            }
        });
    }

    // 4. VALIDACIÓN DE ENVÍO
    if (formRegla) {
        formRegla.addEventListener('submit', function(e) {
            if (selectModalidad.value === 'FIJO') {
                const fijoInput = divFijo.querySelector('input');
                if (!fijoInput.value || fijoInput.value.trim() === "") {
                    e.preventDefault();
                    lanzarError("Debes indicar el porcentaje fijo.");
                    fijoInput.focus();
                }
            } else if (selectModalidad.value === 'TRAMOS') {
                const rows = tableBody.querySelectorAll('tr:not([style*="display: none"])');
                let valido = false;
                rows.forEach(row => {
                    const min = row.querySelector('input[name*="monto_minimo"]').value.trim();
                    const por = row.querySelector('input[name*="porcentaje"]').value.trim();
                    if (min !== "" && por !== "") valido = true;
                });
                if (!valido) {
                    e.preventDefault();
                    lanzarError("Completa al menos un tramo con Monto Mínimo y %.");
                }
            }
        });
    }

    // 5. LÓGICA MODAL ELIMINAR REGLA (CONEXIÓN)
    const modalEliminar = document.getElementById('modalEliminarRegla');
    if (modalEliminar) {
        modalEliminar.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const url = button.getAttribute('data-url');
            const nombre = button.getAttribute('data-nombre');
            modalEliminar.querySelector('#nombreReglaEliminar').textContent = nombre;
            modalEliminar.querySelector('#btnConfirmarEliminar').setAttribute('href', url);
        });
    }
});