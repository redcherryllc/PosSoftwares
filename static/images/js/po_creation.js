document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('purchaseOrderForm');
    const submitBtn = document.getElementById('submit-btn');

    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
            alert('Please fill in all required fields.');
            return;
        }

        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner"></i> Saving...';
    });

    const dateInput = document.getElementById('id_order_date');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    document.querySelectorAll('input:not([type="hidden"]), select').forEach(input => {
        if (!input.placeholder) {
            let fieldName = input.name
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/_/g, ' ')
                .replace(/^.*-/, '')
                .replace(/\b\w/g, c => c.toUpperCase());
            input.placeholder = `Enter ${fieldName}`;
        }
    });

    setupFormsetManagement();
});

function setupFormsetManagement() {
    const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
    const maxFormsInput = document.getElementById('id_form-MAX_NUM_FORMS');
    let formCount = parseInt(totalFormsInput.value);
    const maxForms = parseInt(maxFormsInput.value) || 100;

    checkEmptyState();

    document.getElementById('add-item-button').addEventListener('click', addNewItem);
    document.querySelectorAll('.empty-state .add-item-btn').forEach(button => {
        button.addEventListener('click', addNewItem);
    });

    function addNewItem() {
        if (formCount >= maxForms) {
            alert(`Maximum ${maxForms} items allowed.`);
            return;
        }

        const formsetContainer = document.getElementById('formset-container');
        const firstItem = formsetContainer.querySelector('.formset-item');

        if (!firstItem) {
            console.error('No template form found');
            return;
        }

        const newItem = firstItem.cloneNode(true);
        newItem.dataset.formIdx = formCount;

        const nameRegex = /(id|name)="form-\d+/g;
        newItem.innerHTML = newItem.innerHTML.replace(nameRegex, `$1="form-${formCount}`);

        newItem.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]), select').forEach(field => {
            field.value = field.type === 'number' ? '0' : '';
        });

        const itemNumber = newItem.querySelector('.item-number');
        if (itemNumber) {
            itemNumber.textContent = formCount + 1;
        }

        newItem.querySelector('.remove-item-btn').onclick = function() {
            removeItem(this);
        };

        formsetContainer.insertBefore(newItem, document.getElementById('add-item-button'));
        formCount++;
        totalFormsInput.value = formCount;
        checkEmptyState();
        newItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        newItem.animate([
            { opacity: 0, transform: 'translateY(20px)' },
            { opacity: 1, transform: 'translateY(0)' }
        ], { duration: 300, easing: 'ease-in-out' });
    }

    function removeItem(button) {
        const formItem = button.closest('.formset-item');
        const formsetContainer = document.getElementById('formset-container');
        let formCount = parseInt(totalFormsInput.value);
        const initialFormsCount = parseInt(document.getElementById('id_form-INITIAL_FORMS').value);

        if (formsetContainer.querySelectorAll('.formset-item').length <= 1) {
            formItem.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]), select').forEach(field => {
                field.value = field.type === 'number' ? '0' : '';
            });
            checkEmptyState();
            return;
        }

        const formIdx = parseInt(formItem.dataset.formIdx);
        if (formIdx < initialFormsCount) {
            const deleteField = formItem.querySelector('input[name$="-DELETE"]');
            if (deleteField) {
                deleteField.value = 'on';
                formItem.style.display = 'none';
            }
        } else {
            formItem.animate([
                { opacity: 1, transform: 'translateY(0)' },
                { opacity: 0, transform: 'translateY(20px)' }
            ], { duration: 300, easing: 'ease-in-out' }).onfinish = () => {
                formItem.remove();
                formCount--;
                totalFormsInput.value = formCount;

                const remainingItems = formsetContainer.querySelectorAll('.formset-item');
                remainingItems.forEach((item, idx) => {
                    const itemNumber = item.querySelector('.item-number');
                    if (itemNumber) {
                        itemNumber.textContent = idx + 1;
                    }
                });
                checkEmptyState();
            };
        }
    }

    function checkEmptyState() {
        const formsetContainer = document.getElementById('formset-container');
        const emptyState = document.getElementById('empty-state');
        const visibleItems = Array.from(formsetContainer.querySelectorAll('.formset-item'))
            .filter(item => item.style.display !== 'none');
        
        emptyState.style.display = visibleItems.length === 0 ? 'block' : 'none';
    }
}