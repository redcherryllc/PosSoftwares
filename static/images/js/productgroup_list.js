document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function (event) {
            if (!confirm('Are you sure you want to delete this product group?')) {
                event.preventDefault();
            }
        });
    });
});