document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('stockAdjustmentForm');
    
    form.addEventListener('submit', function(event) {
        const selectFields = form.querySelectorAll('select[required]');
        const quantityInput = form.querySelector('input[name="quantity"]');
        
        for (let select of selectFields) {
            if (!select.value) {
                event.preventDefault();
                alert(`Please select a valid option for ${select.labels[0].textContent.trim().replace('*', '')}.`);
                select.focus();
                return;
            }
        }

        if (!form.checkValidity()) {
            event.preventDefault();
            alert('Please fill in all required fields before submitting.');
            form.classList.add('was-validated');
            return;
        }

        if (parseFloat(quantityInput.value) === 0) {
            event.preventDefault();
            alert('Quantity cannot be zero.');
            quantityInput.focus();
            return;
        }

        if (!confirm('Are you sure you want to submit this stock adjustment?')) {
            event.preventDefault();
        }
    });

    const selectFields = document.querySelectorAll('select');
    selectFields.forEach(select => {
        select.addEventListener('change', function() {
            this.setAttribute('value', this.value);
        });
    });
});