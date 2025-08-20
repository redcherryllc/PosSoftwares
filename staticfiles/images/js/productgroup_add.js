document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('product-group-form');
    form.addEventListener('submit', function (event) {
        let isValid = true;
        form.querySelectorAll('input, select').forEach(input => {
            if (!input.checkValidity()) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        if (!isValid) {
            event.preventDefault();
        }
    });

    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('input', function () {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
            }
        });
    });
});