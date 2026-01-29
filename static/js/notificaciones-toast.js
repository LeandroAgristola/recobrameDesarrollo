document.addEventListener('DOMContentLoaded', function() {
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(el => {
        // Simple, directo y sin errores
        bootstrap.Toast.getOrCreateInstance(el).show();
    });
});