function toggleFiltros() {
    const fila = document.getElementById('fila-filtros');
    const btnCheck = document.getElementById('btnAplicarCheck');
    const btnFiltro = document.getElementById('btnToggleFiltros');
    
    if (fila) {
        if (fila.style.display === 'none' || fila.style.display === '') {
            // ABRIR FILTROS
            fila.style.display = 'table-row';
            if (btnCheck) btnCheck.style.display = 'inline-block'; // Muestra Check
            if (btnFiltro) btnFiltro.style.display = 'none';      // OCULTA EMBUDO
        } else {
            // CERRAR FILTROS
            fila.style.display = 'none';
            if (btnCheck) btnCheck.style.display = 'none';        // Oculta Check
            if (btnFiltro) btnFiltro.style.display = 'inline-block'; // MUESTRA EMBUDO
        }
    }
}

function aplicarFiltrosJS() {
    // 1. Obtener URL base
    const url = new URL(window.location.href);
    const params = new URLSearchParams(url.search);

    // 2. Buscador Global
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch && globalSearch.value.trim() !== '') {
        params.set('q', globalSearch.value.trim());
    } else {
        params.delete('q');
    }

    // 3. Obtener todos los inputs de la clase 'filtro-columna'
    const inputs = document.querySelectorAll('.filtro-columna');
    
    inputs.forEach(input => {
        if (input.type === 'checkbox') {
            if (input.checked) {
                params.set(input.name, 'true');
            } else {
                params.delete(input.name);
            }
        } else {
            if (input.value.trim() !== '') {
                params.set(input.name, input.value.trim());
            } else {
                params.delete(input.name);
            }
        }
    });

    // 4. Redirigir
    window.location.href = `${url.pathname}?${params.toString()}`;
}