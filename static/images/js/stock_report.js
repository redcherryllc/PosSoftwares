 document.getElementById('stock-report-form').addEventListener('submit', function() {
        const submitBtn = document.getElementById('submit-btn');
        const submitText = document.getElementById('submit-text');
        const loadingSpinner = document.getElementById('loading-spinner');
        
        submitBtn.disabled = true;
        submitText.classList.add('d-none');
        loadingSpinner.classList.remove('d-none');
    });