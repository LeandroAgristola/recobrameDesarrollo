document.addEventListener("DOMContentLoaded", function() {
    
    // ==========================================
    // 1. INICIALIZAR POPOVERS
    // ==========================================
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'hover',
            html: true,
            customClass: 'crm-popover'
        })
    });

    // ==========================================
    // 2. ACTIVAR PESTAÑA CORRECTA (PERSISTENCIA)
    // ==========================================
    // Tomamos la variable global definida en el HTML
    const tabName = window.CRM_TAB_ACTIVA || 'impagos'; 
    const triggerEl = document.querySelector(`#${tabName}-tab`);
    if (triggerEl) {
        const tabInstance = new bootstrap.Tab(triggerEl);
        tabInstance.show();
    }

    // ==========================================
    // 3. MODALES AUTOMÁTICOS (RESTAURAR / CONCILIAR)
    // ==========================================
    const modalRestaurar = document.getElementById('modalRestaurarMasivo');
    const modalConciliar = document.getElementById('modalConciliacion');
    
    // Replicamos el if/elif de Django: Si existe en el DOM, lo abrimos.
    if (modalRestaurar) {
        new bootstrap.Modal(modalRestaurar).show();
    } else if (modalConciliar) {
        new bootstrap.Modal(modalConciliar).show();
    }

    // ==========================================
    // 4. LÓGICA PARA IMPORTAR EXCEL (Context-Aware)
    // ==========================================
    const botonesImportar = document.querySelectorAll('.btn-importar-contexto');
    const inputEstado = document.getElementById('inputEstadoCarga');
    const textoEstado = document.getElementById('textoEstadoCarga');

    botonesImportar.forEach(boton => {
        boton.addEventListener('click', function() {
            const estado = this.getAttribute('data-estado'); 
            const nombre = this.getAttribute('data-nombre'); 
            
            if(inputEstado) inputEstado.value = estado;
            if(textoEstado) {
                textoEstado.innerText = nombre;
                textoEstado.className = estado === 'CEDIDO' ? 'text-primary fw-bold' : 'text-danger fw-bold';
            }
        });
    });

    // ==========================================
    // 5. LÓGICA PARA NUEVO REGISTRO (Validación)
    // ==========================================
    const botonesNuevo = document.querySelectorAll('.btn-nuevo-contexto');
    const inputEstadoNuevo = document.getElementById('inputEstadoNuevo');
    const selectProducto = document.getElementById('id_tipo_producto');
    const alertaProducto = document.getElementById('alertaProductoCedido');
    const formNuevo = document.getElementById('formNuevoRegistro');
    const btnSubmitNuevo = document.getElementById('btnSubmitNuevoRegistro');

    let productosCedibles = [];
    if (formNuevo && formNuevo.getAttribute('data-tipos-cedidos')) {
        productosCedibles = formNuevo.getAttribute('data-tipos-cedidos').split(',').map(s => s.trim().toUpperCase());
    }

    function validarTipoProducto() {
        if (!selectProducto || !inputEstadoNuevo || !alertaProducto) return;
        
        const estado = inputEstadoNuevo.value;
        const productoActual = selectProducto.value.toUpperCase();
        
        if (estado === 'CEDIDO') {
            if (!productosCedibles.includes(productoActual)) {
                alertaProducto.style.display = 'block';
                if (btnSubmitNuevo) btnSubmitNuevo.disabled = true;
            } else {
                alertaProducto.style.display = 'none';
                if (btnSubmitNuevo) btnSubmitNuevo.disabled = false;
            }
        } else {
            alertaProducto.style.display = 'none';
            if (btnSubmitNuevo) btnSubmitNuevo.disabled = false;
        }
    }

    if (selectProducto) {
        selectProducto.addEventListener('change', validarTipoProducto);
    }

    botonesNuevo.forEach(boton => {
        boton.addEventListener('click', function() {
            if(inputEstadoNuevo) {
                inputEstadoNuevo.value = this.getAttribute('data-estado');
                validarTipoProducto();
            }
        });
    });

    // ==========================================
    // 6. LIMPIAR FORMULARIO AL CERRAR EL MODAL
    // ==========================================
    const modalNuevoRegistroEl = document.getElementById('modalNuevoRegistro');
    if (modalNuevoRegistroEl && formNuevo) {
        modalNuevoRegistroEl.addEventListener('hidden.bs.modal', function () {
            // 1. Resetea todos los inputs, selects y textareas a su estado original (vacío)
            formNuevo.reset(); 
            
            // 2. Apaga la alerta de seguridad por si había quedado encendida
            if (alertaProducto) alertaProducto.style.display = 'none';
            
            // 3. Vuelve a habilitar el botón verde por si había quedado bloqueado
            if (btnSubmitNuevo) btnSubmitNuevo.disabled = false;
        });
    }

    // ==========================================
    // 7. PERSISTENCIA DE PESTAÑAS (URL DINÁMICA)
    // ==========================================
    const todasLasPestanas = document.querySelectorAll('button[data-bs-toggle="tab"], button[data-bs-toggle="pill"]');
    
    todasLasPestanas.forEach(pestana => {
        pestana.addEventListener('shown.bs.tab', function (event) {
            let target = event.target.getAttribute('data-bs-target');
            if (target) {
                // Limpiamos el texto para que "#tab-cedidos" quede como "cedidos"
                let tabName = target.replace('#tab-', '').replace('#pills-', '');
                
                // Actualizamos la URL del navegador SIN recargar la página
                let nuevaUrl = new URL(window.location.href);
                nuevaUrl.searchParams.set('tab', tabName);
                window.history.replaceState({}, '', nuevaUrl);
                
                // Actualizamos nuestra variable global
                window.CRM_TAB_ACTIVA = tabName;
            }
        });
    });

    // ==========================================
    // 8. ACCIONES MASIVAS (CHECKBOXES)
    // ==========================================
    
    /**
     * Activa la lógica de casillas maestras para acciones masivas.
     * @param {string} tabPrefix - 'impagos' o 'cedidos'
     */
    function setupBulkActions(tabPrefix) {
        const selectAll = document.querySelector(`.select-all-${tabPrefix}`);
        const rowCheckboxes = document.querySelectorAll(`.row-checkbox-${tabPrefix}`);
        const bulkBar = document.getElementById(`bulk-action-bar-${tabPrefix}`);
        const countSpan = document.getElementById(`selected-count-${tabPrefix}`);

        if (!selectAll || !bulkBar) return;

        // Función para actualizar el contador y mostrar/ocultar la barra
        function updateUI() {
            const selectedCount = document.querySelectorAll(`.row-checkbox-${tabPrefix}:checked`).length;
            countSpan.innerText = selectedCount;
            
            if (selectedCount > 0) {
                bulkBar.classList.remove('d-none');
            } else {
                bulkBar.classList.add('d-none');
            }
        }

        // Evento: Click en el Checkbox Maestro (Seleccionar todo)
        selectAll.addEventListener('change', function() {
            rowCheckboxes.forEach(cb => {
                cb.checked = selectAll.checked;
            });
            updateUI();
        });

        // Evento: Click en los Checkboxes Individuales
        rowCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                // Si desmarco uno, desmarco el maestro
                if (!this.checked) {
                    selectAll.checked = false;
                }
                
                // Si marco todos individualmente, marco el maestro
                const allChecked = document.querySelectorAll(`.row-checkbox-${tabPrefix}:checked`).length === rowCheckboxes.length;
                if (allChecked) {
                    selectAll.checked = true;
                }
                
                updateUI();
            });
        });
    }

    // Inicializamos para ambas pestañas directamente
    setupBulkActions('impagos');
    setupBulkActions('cedidos');

}); // ESTA ES LA LLAVE QUE CIERRA TU ARCHIVO PRINCIPAL