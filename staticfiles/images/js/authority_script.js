document.addEventListener('DOMContentLoaded', function() {
    const selectUserSection = document.getElementById('select-user');
    const addUserSection = document.getElementById('add-user');
    const selectUserDropdown = document.getElementById('id_saas_username');
    const addUserDropdown = document.getElementById('id_add_new_user');
    const formUserId = document.getElementById('form-user-id');
    const currentUserIdDisplay = document.getElementById('current-user-id');
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.menu-checkbox');
    const newAccessSection = document.querySelector('.new-access-section');
    const newAccessTbody = document.querySelector('#new-access-table tbody');
    const authorityForm = document.getElementById('authorityForm');
    const clearSelectionBtn = document.getElementById('clear-selection');
    const toggleButtons = document.querySelectorAll('.toggle-btn');

    let currentUserId = formUserId.value || null;

    const defaultSubMenus = [
        // Replace with  menu:sub-menu 
        // { menu: 'Dashboard', submenu: 'View Dashboard' },
        // { menu: 'Settings', submenu: 'Basic Settings' }
    ];

    const updateSelectAllState = () => {
        const total = checkboxes.length;
        const checked = document.querySelectorAll('.menu-checkbox:checked').length;
        selectAllCheckbox.checked = total > 0 && checked === total;
        selectAllCheckbox.indeterminate = checked > 0 && checked < total;
    };

    const updateNewAccess = () => {
        newAccessTbody.innerHTML = '';
        checkboxes.forEach(checkbox => {
            if (checkbox.checked && checkbox.dataset.original === '0') {
                const row = checkbox.closest('tr');
                const menu = checkbox.dataset.menu;
                const submenuText = row.querySelector('td:nth-child(2)').textContent;
                const newRow = document.createElement('tr');
                newRow.innerHTML = `<td>${menu}</td><td>${submenuText}</td>`;
                newAccessTbody.appendChild(newRow);
            }
        });
        newAccessSection.style.display = newAccessTbody.children.length > 0 ? 'block' : 'none';
    };

    const loadUserAuthorityData = (userId) => {
        if (!userId) {
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
                checkbox.dataset.original = '0';
            });
            currentUserIdDisplay.textContent = 'None';
            updateNewAccess();
            updateSelectAllState();
            return;
        }

        currentUserIdDisplay.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

        fetch(`/authority/get_authority_data/${userId}/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
                checkbox.dataset.original = '0';
            });

            if (data.current_permissions && data.current_permissions.length > 0) {
                data.current_permissions.forEach(permission => {
                    const checkbox = document.querySelector(
                        `.menu-checkbox[data-menu="${permission.au_menu}"][data-submenu="${permission.au_submenu}"]`
                    );
                    if (checkbox) {
                        checkbox.checked = Boolean(permission.au_status);
                        checkbox.dataset.original = Boolean(permission.au_status) ? '1' : '0';
                    }
                });
            }

            const username = selectUserDropdown.querySelector(`option[value="${userId}"]`)?.textContent.trim() || 'Unknown User';
            currentUserIdDisplay.textContent = `${userId} - ${username}`;
            updateNewAccess();
            updateSelectAllState();
        })
        .catch(error => {
            console.error('Error:', error);
            currentUserIdDisplay.textContent = 'Error loading data';
            updateNewAccess();
            updateSelectAllState();
        });
    };

    const applyDefaultPermissions = () => {
        checkboxes.forEach(checkbox => {
            const isDefault = defaultSubMenus.some(
                def => def.menu === checkbox.dataset.menu && def.submenu === checkbox.dataset.submenu
            );
            if (isDefault) {
                checkbox.checked = true;
                checkbox.dataset.original = '0'; 
            } else {
                checkbox.checked = false;
                checkbox.dataset.original = '0';
            }
        });
        updateNewAccess();
        updateSelectAllState();
    };

    selectAllCheckbox.addEventListener('change', () => {
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        updateNewAccess();
        updateSelectAllState();
    });

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updateNewAccess();
            updateSelectAllState();
        });
    });

    selectUserDropdown.addEventListener('change', () => {
        const userId = selectUserDropdown.value;
        formUserId.value = userId;
        currentUserId = userId;
        loadUserAuthorityData(userId);
    });

    clearSelectionBtn.addEventListener('click', () => {
        selectUserDropdown.selectedIndex = 0;
        formUserId.value = '';
        currentUserId = null;
        loadUserAuthorityData(null);
    });

    addUserSection.addEventListener('submit', (e) => {
        e.preventDefault();
        const newUsername = addUserDropdown.value;
        if (!newUsername) {
            alert('Please select a user to add.');
            return;
        }

        const addButton = addUserSection.querySelector('.btn-add');
        addButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        addButton.disabled = true;

        const formData = new FormData();
        formData.append('add_new_user', newUsername);
        formData.append('add_new_user_submit', '1');
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        
        defaultSubMenus.forEach(def => {
            const checkbox = document.querySelector(
                `.menu-checkbox[data-menu="${def.menu}"][data-submenu="${def.submenu}"]`
            );
            if (checkbox) {
                formData.append('selected', checkbox.value);
            }
        });

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const userId = data.user_id;
                const username = data.username;

                const existingOption = selectUserDropdown.querySelector(`option[value="${userId}"]`);
                if (!existingOption) {
                    const newOption = document.createElement('option');
                    newOption.value = userId;
                    newOption.textContent = username;
                    selectUserDropdown.appendChild(newOption);
                }

                selectUserDropdown.value = userId;
                formUserId.value = userId;
                currentUserId = userId;
                currentUserIdDisplay.textContent = `${userId} - ${username}`;

                toggleButtons.forEach(b => b.classList.remove('active'));
                toggleButtons[0].classList.add('active');
                selectUserSection.style.display = 'block';
                addUserSection.style.display = 'none';
                addUserDropdown.selectedIndex = 0;

                
                applyDefaultPermissions();
            } else {
                alert('Error adding user: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error adding user:', error);
            alert('Error adding user.');
        })
        .finally(() => {
            addButton.innerHTML = 'Add User';
            addButton.disabled = false;
        });
    });

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            toggleButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectUserSection.style.display = btn.dataset.target === 'select-user' ? 'block' : 'none';
            addUserSection.style.display = btn.dataset.target === 'add-user' ? 'block' : 'none';

            if (btn.dataset.target === 'add-user') {
                selectUserDropdown.selectedIndex = 0;
                formUserId.value = '';
                currentUserId = null;
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                    checkbox.dataset.original = '0';
                });
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
                currentUserIdDisplay.textContent = 'None';
                updateNewAccess();
                updateSelectAllState();
            }
        });
    });

    if (currentUserId && selectUserDropdown) {
        selectUserDropdown.value = currentUserId;
        loadUserAuthorityData(currentUserId);
    } else {
        updateNewAccess();
        updateSelectAllState();
    }
});