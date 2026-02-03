document.addEventListener('DOMContentLoaded', function() {
    const buscador = document.getElementById('buscadorEmpresa');
    
    if (buscador) {
        buscador.addEventListener('keyup', function() {
            let filtro = this.value.toLowerCase();
            let items = document.querySelectorAll('.item-empresa');
            
            items.forEach(item => {
                let texto = item.innerText.toLowerCase();
                item.style.display = texto.includes(filtro) ? '' : 'none';
            });
        });
    }
});