
// Variables globales para almacenar temporalmente el documento a borrar
let docTargetId = null;
let docTargetUrl = '';
let modalEliminarInstancia = null;

// 1. Esta función solo ABRE el modal y guarda los datos
function eliminarDocumento(docId, urlAction) {
    docTargetId = docId;
    docTargetUrl = urlAction;
    
    const modalEl = document.getElementById('modalConfirmarEliminarDoc');
    modalEliminarInstancia = new bootstrap.Modal(modalEl);
    modalEliminarInstancia.show();
}

// 2. Esta función EJECUTA el borrado real (Se llama desde el botón rojo del modal)
function ejecutarEliminacionDoc() {
    if (!docTargetId || !docTargetUrl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(docTargetUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // Borramos todos los elementos visuales del documento (en todos los modales/pestañas)
            const elementos = document.querySelectorAll(`.doc-item-${docTargetId}`);
            elementos.forEach(el => el.remove());
            
            // Cerramos el modal de confirmación
            modalEliminarInstancia.hide();
            
        } else {
            alert('Ocurrió un error al intentar eliminar el documento.');
            modalEliminarInstancia.hide();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error de conexión al servidor.');
        modalEliminarInstancia.hide();
    });
}