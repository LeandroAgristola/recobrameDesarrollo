// UNIFICADO: crm_list.js + toggleFiltros.js

// 1. Manejo del Buscador de la lista de empresas (la vista anterior)
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

// 2. Función para mostrar/ocultar la fila de filtros en la tabla de Impagos
function toggleFiltros() {
    const fila = document.getElementById('fila-filtros');
    const btnCheck = document.getElementById('btnAplicarCheck');
    const btnFiltro = document.getElementById('btnToggleFiltros');
    
    if (fila) {
        if (fila.style.display === 'none' || fila.style.display === '') {
            fila.style.display = 'table-row';
            if (btnCheck) btnCheck.style.display = 'inline-block';
            if (btnFiltro) btnFiltro.style.display = 'none';
        } else {
            fila.style.display = 'none';
            if (btnCheck) btnCheck.style.display = 'none';
            if (btnFiltro) btnFiltro.style.display = 'inline-block';
        }
    }
}

// 3. LA FUNCIÓN CLAVE: Aplicar Filtros de Impagos
function aplicarFiltrosJS() {
    const params = new URLSearchParams();
    
    // Capturar búsqueda global
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch && globalSearch.value.trim() !== '') {
        params.append('q', globalSearch.value.trim());
    }

    // Capturar todos los filtros de columna
    document.querySelectorAll('.filtro-columna').forEach(input => {
        if (input.type === 'checkbox') {
            if (input.checked) params.append(input.name, 'true');
        } else if (input.value.trim() !== '') {
            params.append(input.name, input.value.trim());
        }
    });

    // VITAL: Decirle al sistema que se quede en la pestaña impagos
    params.append('tab', 'impagos');

    // Recargar con los nuevos parámetros
    window.location.search = params.toString();
}