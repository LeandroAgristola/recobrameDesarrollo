// UNIFICADO: crm_list.js + toggleFiltros.js + filtros_sheets.js

// 1. Buscador de empresas
document.addEventListener('DOMContentLoaded', function() {
    const buscadorEmpresa = document.getElementById('buscadorEmpresa');
    if (buscadorEmpresa) {
        buscadorEmpresa.addEventListener('keyup', function() {
            let filtro = this.value.toLowerCase();
            document.querySelectorAll('.item-empresa').forEach(item => {
                item.style.display = item.innerText.toLowerCase().includes(filtro) ? '' : 'none';
            });
        });
    }
});

// 2. Función para "Habilitar la edición de filtros"
function toggleFiltros() {
    const activeTabPane = document.querySelector('.tab-pane.active');
    if (!activeTabPane) return;

    const btnCheck = activeTabPane.querySelector('button[id^="btnAplicarCheck"]');
    const btnFiltro = activeTabPane.querySelector('button[id^="btnToggleFiltros"]');
    
    if (btnFiltro && btnCheck) {
        // Ocultamos el botón azul y mostramos el verde
        btnFiltro.style.display = 'none';
        btnCheck.style.display = 'inline-block';
        
        // MAGIA: Hacemos aparecer todos los iconos de embudo de las columnas
        const filterIcons = activeTabPane.querySelectorAll('.btn-column-filter');
        filterIcons.forEach(icon => {
            icon.style.display = 'inline-block';
        });
    }
}

// 3. LA FUNCIÓN CLAVE: Ejecutar los filtros seleccionados
function aplicarFiltrosJS() {
    const activeTabPane = document.querySelector('.tab-pane.active');
    if (!activeTabPane) return;

    let tabName = activeTabPane.id.includes('cedido') ? 'cedidos' : 'impagos';
    let params = new URLSearchParams(window.location.search);

    // 3.1 Limpiar TODOS los parámetros anteriores
    const keysToDelete = [];
    params.forEach((value, key) => {
        if (key === 'q' || key.startsWith('f_') || key === 'tab' || key === 'page') {
            keysToDelete.push(key);
        }
    });
    keysToDelete.forEach(key => params.delete(key));

    // 3.2 Buscar global
    const searchInput = activeTabPane.querySelector('.search-box input');
    if (searchInput && searchInput.value.trim() !== '') {
        params.set('q', searchInput.value.trim());
    }

    // 3.3 Leer TODOS los checkboxes marcados dentro de las ventanitas
    const checkboxes = activeTabPane.querySelectorAll('.filtro-sheet-cb:checked');
    checkboxes.forEach(cb => {
        params.append(cb.name, cb.value); // append permite enviar múltiples opciones a Django
    });

    // 3.4 Leer las ventanitas numéricas o de texto (Ej: Días min y max)
    const textInputs = activeTabPane.querySelectorAll('.filtro-sheet-input');
    textInputs.forEach(input => {
        if (input.value.trim() !== '') {
            params.set(input.name, input.value.trim());
        }
    });

    params.set('tab', tabName);
    window.location.search = params.toString();
}

// 4. Buscador interno de las ventanitas (Igual que Sheets)
function filtrarOpcionesMenu(inputId, listaId) {
    const filter = document.getElementById(inputId).value.toLowerCase();
    const items = document.getElementById(listaId).getElementsByClassName('dropdown-item-cb');
    
    for (let i = 0; i < items.length; i++) {
        let label = items[i].textContent || items[i].innerText;
        items[i].style.display = label.toLowerCase().indexOf(filter) > -1 ? "" : "none";
    }
}