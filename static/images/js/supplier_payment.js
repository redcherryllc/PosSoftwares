(function () {
            'use strict';
            var form = document.querySelector('.needs-validation');
            var submitButton = form.querySelector('button[type="submit"]');
            
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                } else {
                    submitButton.classList.add('submitting');
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    submitButton.disabled = true;
                }
                form.classList.add('was-validated');
            }, false);
        })();