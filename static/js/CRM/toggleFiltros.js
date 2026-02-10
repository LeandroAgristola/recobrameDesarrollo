 function toggleFiltros() {
            const fila = document.getElementById('fila-filtros-google');
            if (fila) {
                if (fila.style.display === 'none') {
                    fila.style.display = 'table-row';
                    // Opcional: enfocar el primer input
                    const primerInput = fila.querySelector('input');
                    if(primerInput) primerInput.focus();
                } else {
                    fila.style.display = 'none';
                }
            }
        }