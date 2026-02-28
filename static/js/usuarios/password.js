function togglePassword(inputId, iconId) {
    var pwdField = document.getElementById(inputId);
    var icon = document.getElementById(iconId);
    if (pwdField.type === "password") {
        pwdField.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        pwdField.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}

function copiarAlPortapapeles(inputId) {
    var copyText = document.getElementById(inputId);
    if (!copyText.value) return;

    // El input es readonly pero se puede seleccionar
    copyText.select();
    copyText.setSelectionRange(0, 99999); // Para dispositivos móviles

    navigator.clipboard.writeText(copyText.value).then(function () {
        // Feedback visual básico
        var originalColor = copyText.style.backgroundColor;
        copyText.style.backgroundColor = '#d1e7dd';
        setTimeout(function () {
            copyText.style.backgroundColor = originalColor;
        }, 500);
    });
}