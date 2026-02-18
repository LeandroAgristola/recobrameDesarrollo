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

// 2. Función para mostrar/ocultar la fila de filtros en la tabla ACTIVA
function toggleFiltros() {
    // 2.1 Detectar la pestaña activa
    const activeTabPane = document.querySelector('.tab-pane.active');
    if (!activeTabPane) return;

    // 2.2 Buscar los elementos SOLO dentro de esa pestaña activa
    // Usamos selectores genéricos para que funcione aunque los IDs se repitan en el HTML
    const fila = activeTabPane.querySelector('tr[id^="fila-filtros"]'); 
    const btnCheck = activeTabPane.querySelector('button[id^="btnAplicarCheck"]');
    const btnFiltro = activeTabPane.querySelector('button[id^="btnToggleFiltros"]');
    
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

// 3. LA FUNCIÓN CLAVE: Aplicar Filtros Dinámicos (Impagos, Cedidos, Pagados)
function aplicarFiltrosJS() {
    // 3.1 Detectar cuál es la pestaña (tab) activa en este momento
    const activeTabPane = document.querySelector('.tab-pane.active');
    if (!activeTabPane) return;

    // 3.2 Determinar el nombre de la pestaña basándose en el ID del contenedor
    let tabName = 'impagos'; // Por defecto
    if (activeTabPane.id.includes('cedido')) {
        tabName = 'cedidos';
    } else if (activeTabPane.id.includes('pagado')) {
        tabName = 'ha-pagado';
    }

    let params = new URLSearchParams(window.location.search);

    // 3.3 Limpiar parámetros anteriores (búsqueda, filtros y paginación)
    // Esto evita que al buscar en Cedidos se arrastren filtros viejos de Impagos
    const keysToDelete = [];
    params.forEach((value, key) => {
        if (key === 'q' || key.startsWith('f_') || key === 'tab' || key === 'page') {
            keysToDelete.push(key);
        }
    });
    keysToDelete.forEach(key => params.delete(key));

    // 3.4 Leer el buscador global SOLO de la pestaña activa
    const searchInput = activeTabPane.querySelector('.search-box input');
    if (searchInput && searchInput.value.trim() !== '') {
        params.set('q', searchInput.value.trim());
    }

    // 3.5 Leer los filtros de columna SOLO de la pestaña activa
    const filtrosColumna = activeTabPane.querySelectorAll('.filtro-columna');
    filtrosColumna.forEach(input => {
        if (input.type === 'checkbox') {
            if (input.checked) params.set(input.name, 'true');
        } else if (input.value.trim() !== '') {
            params.set(input.name, input.value.trim());
        }
    });

    // 3.6 Fijar la pestaña actual para que Django recargue exactamente donde estamos
    params.set('tab', tabName);

    // 3.7 Redirigir con la URL estructurada
    window.location.search = params.toString();
}