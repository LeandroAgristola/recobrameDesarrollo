document.addEventListener('DOMContentLoaded', function () {
    // 1. Ampliar la lista permitida de etiquetas para el Popover
    var myDefaultAllowList = bootstrap.Tooltip.Default.allowList;
    myDefaultAllowList.table = [];
    myDefaultAllowList.thead = [];
    myDefaultAllowList.tbody = [];
    myDefaultAllowList.tr = [];
    myDefaultAllowList.td = [];

    // 2. Inicializar Popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            sanitize: false // Importante para que renderice la tabla
        })
    })
});