let currentSaleItems = [];
let keypadInput = '';
let currentRegistrationId = null;
let currentServiceType = '';
let currentServiceId = 0;
let isRegistrationProcess = false;

document.addEventListener('DOMContentLoaded', function() {
   
    const selectedRoomIdFromTemplate = window.selectedRoomId ? String(window.selectedRoomId).trim() : '';
    console.log('Selected room ID from template:', selectedRoomIdFromTemplate);
    console.log('next_sale_no from template:', window.nextSaleNo);
    console.log('Current client date:', new Date().toLocaleDateString('en-CA'));
    console.log('Client timezone offset:', new Date().getTimezoneOffset());

    clearSale();

    $('#customer-search-section').hide();
    $('#customer-form-section').hide();
    $('#registration-form-section').hide();

    const customerSelect = $('select[name="customer_select"]');
    customerSelect.val(customerSelect.find('option:contains("Walking Customer")').val() || '');

    const roomSelect = $('select[name="room_select"]');
    if (selectedRoomIdFromTemplate) {
        console.log('Setting room_select to:', selectedRoomIdFromTemplate);
        
        const matchingOption = roomSelect.find('option').filter(function() {
            return String($(this).val()) === selectedRoomIdFromTemplate;
        });
        
        if (matchingOption.length > 0) {
            roomSelect.val(selectedRoomIdFromTemplate);
            currentServiceType = 'ROOM';
            currentServiceId = selectedRoomIdFromTemplate;
            console.log('Room selected:', roomSelect.find('option:selected').text());
        } else {
            console.warn('Room option not found in dropdown:', selectedRoomIdFromTemplate);
            roomSelect.val('');
            currentServiceType = '';
            currentServiceId = 0;
        }
    } else {
        console.log('No selected room ID, resetting room_select');
        roomSelect.val('');
        currentServiceType = '';
        currentServiceId = 0;
    }

    $('select[name="table_select"]').change(function() {
        const selectedValue = $(this).val();
        currentServiceType = selectedValue ? 'TABLE' : '';
        currentServiceId = selectedValue || 0;
        if (selectedValue) {
            $('select[name="room_select"]').val('');
            $('select[name="vehicle_select"]').val('');
        }
    });

    $('select[name="room_select"]').change(function() {
        const selectedValue = $(this).val();
        currentServiceType = selectedValue ? 'ROOM' : '';
        currentServiceId = selectedValue || 0;
        
        if (selectedValue) {
            $('select[name="table_select"]').val('');
            $('select[name="vehicle_select"]').val('');
            
            console.log('Room selected, updating session with room_id:', selectedValue);
            
            $.ajax({
                url: window.homeUrl,
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: {
                    room_id: selectedValue
                },
                success: function(response) {
                    console.log('Room selection updated in session:', selectedValue);
                },
                error: function(xhr, status, error) {
                    console.error('Error updating room selection:', xhr.status, error, xhr.responseText);
                    alert('Error updating room selection. Please try again.');
                }
            });
        } else {
            console.log('Room deselected, clearing session');
            $.ajax({
                url: window.homeUrl,
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                data: {
                    clear_room: '1'
                },
                success: function(response) {
                    console.log('Cleared room selection from session');
                },
                error: function(xhr, status, error) {
                    console.error('Error clearing room selection:', xhr.status, error);
                }
            });
        }
    });

    $('select[name="vehicle_select"]').change(function() {
        const selectedValue = $(this).val();
        currentServiceType = selectedValue ? 'VEHICLE' : '';
        currentServiceId = selectedValue || 0;
        if (selectedValue) {
            $('select[name="table_select"]').val('');
            $('select[name="room_select"]').val('');
        }
    });

    $('.nav-button.set-customer').click(function() {
        isRegistrationProcess = false;
        $('#customer-search-section').hide();
        $('#customer-form-section').show();
        $('#registration-form-section').hide();
        $('#show-registration-form-btn').hide();
        $('#customer-search-results').empty();
        $('#customer-search-input').val('');
        $('#customerModalLabel').text('Add New Customer');
    });

    $('.nav-button.register').click(function() {
        isRegistrationProcess = true;
        $('#customer-search-section').show();
        $('#customer-form-section').hide();
        $('#registration-form-section').hide();
        $('#customer-search-results').empty();
        $('#customer-search-input').val('');
        $('#customerModalLabel').text('Customer and Registration');
        
        const roomSelect = $('select[name="room_select"]');
        const selectedRoomId = roomSelect.val();
        if (selectedRoomId && $('#id_room').find(`option[value="${selectedRoomId}"]`).length > 0) {
            $('#id_room').val(selectedRoomId);
            console.log('Pre-selected room in registration form:', selectedRoomId);
        } else {
            $('#id_room').val('');
            console.log('No room pre-selected in registration form');
        }
    });

    console.log('Registration add URL:', window.registrationAddUrl);
    console.log('Add customer URL:', window.addCustomerUrl);
    console.log('Get customers URL:', window.getCustomersUrl);
    console.log('CSRF Token:', getCookie('csrftoken'));

    $('#customer-search-btn').click(function() {
        const query = $('#customer-search-input').val().trim();
        if (!query) {
            alert('Please enter a search term.');
            return;
        }

        $.ajax({
            url: window.registrationAddUrl,
            method: 'GET',
            data: { action: 'search_customer', q: query },
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                console.log('Search response:', response);
                const results = $('#customer-search-results');
                results.empty();
                if (response.status === 'success' && response.customers && response.customers.length > 0) {
                    results.append('<ul class="list-group">');
                    response.customers.forEach(function(customer) {
                        results.append(
                            `<li class="list-group-item pt-2" data-phone="${customer.phone || ''}">
                                ${customer.name} (Phone: ${customer.phone || 'N/A'}, Aadhaar: ${customer.aadhaar || 'N/A'})
                                <button class="btn btn-sm btn-primary float-end select-customer" data-id="${customer.id}" data-phone="${customer.phone || ''}" data-name="${customer.name}">Select</button>
                            </li>`
                        );
                    });
                    results.append('</ul>');
                } else {
                    results.append('<p>No customers found. <a href="#" id="show-customer-form">Add new customer</a>.</p>');
                }
            },
            error: function(xhr, status, error) {
                console.error('Customer search error:', xhr.status, error, xhr.responseText);
                alert(`Error searching customers: ${xhr.status} ${error}. Please check the console for details.`);
            }
        });
    });

    $(document).on('click', '#show-customer-form', function() {
        $('#customer-search-section').hide();
        $('#customer-form-section').show();
        $('#registration-form-section').hide();
        $('#show-registration-form-btn').show();
        $('#customerModalLabel').text('Add New Customer');
    });

    $(document).on('click', '#show-registration-form-btn', function() {
        const customerId = $('#id_customer_id').val();
        const customerName = $('#id_customer_name').val();
        const customerPhone = $('#id_phone_1').val();

        const registrationCustomerSelect = $('#id_customer');
        registrationCustomerSelect.append(`<option value="${customerId}">${customerName}</option>`);
        registrationCustomerSelect.val(customerId);
        $('#id_phone1').val(customerPhone);

        $('#customer-form-section').hide();
        $('#registration-form-section').show();
        $('#customerModalLabel').text('Add Registration');
        
        const roomSelect = $('select[name="room_select"]');
        const selectedRoomId = roomSelect.val();
        if (selectedRoomId && $('#id_room').find(`option[value="${selectedRoomId}"]`).length > 0) {
            $('#id_room').val(selectedRoomId);
            console.log('Pre-selected room in registration form:', selectedRoomId);
        } else {
            $('#id_room').val('');
            console.log('No room pre-selected in registration form');
        }
    });

    $(document).on('click', '.select-customer', function() {
        const customerId = $(this).data('id');
        const customerPhone = $(this).data('phone');
        const customerName = $(this).data('name');
        const registrationCustomerSelect = $('#id_customer');
        if (registrationCustomerSelect.find(`option[value="${customerId}"]`).length === 0) {
            registrationCustomerSelect.append(`<option value="${customerId}">${customerName}</option>`);
        }
        registrationCustomerSelect.val(customerId);
        $('#id_phone1').val(customerPhone);
        $('#customer-search-section').hide();
        $('#registration-form-section').show();
        $('#customerModalLabel').text('Add Registration');
        
        const roomSelect = $('select[name="room_select"]');
        const selectedRoomId = roomSelect.val();
        if (selectedRoomId && $('#id_room').find(`option[value="${selectedRoomId}"]`).length > 0) {
            $('#id_room').val(selectedRoomId);
            console.log('Pre-selected room in registration form:', selectedRoomId);
        } else {
            $('#id_room').val('');
            console.log('No room pre-selected in registration form');
        }
    });

    $('#customer-form').submit(function(e) {
        e.preventDefault();
        const formData = $(this).serialize();
        console.log('Form data being sent:', formData);
        const $form = $(this);
        const $submitBtn = $form.find('button[type="submit"]');
        $submitBtn.prop('disabled', true).text('Saving...');

        $.ajax({
            url: window.addCustomerUrl,
            method: 'POST',
            data: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                console.log('Add customer response:', response);
                if (response.success && response.customer && response.customer.customer_id && response.customer.customer_name) {
                    const customerSelect = $('select[name="customer_select"]');
                    customerSelect.append(`<option value="${response.customer.customer_id}">${response.customer.customer_name}</option>`);
                    customerSelect.val(response.customer.customer_id);
                    fetch(window.getCustomersUrl, {
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    })
                    .then(res => {
                        if (!res.ok) {
                            throw new Error(`HTTP error! Status: ${res.status}`);
                        }
                        return res.json();
                    })
                    .then(customers => {
                        customerSelect.empty().append('<option value="" disabled>👤 Customer</option>');
                        customers.forEach(customer => {
                            const isSelected = customer.customer_id === response.customer.customer_id ? 'selected' : '';
                            customerSelect.append(`<option value="${customer.customer_id}" ${isSelected}>${customer.customer_name}</option>`);
                        });
                    })
                    .catch(error => {
                        console.error('Error refreshing customers:', error);
                        alert('Error refreshing customer list. Please try again.');
                    });

                    if (isRegistrationProcess) {
                        const registrationCustomerSelect = $('#id_customer');
                        if (registrationCustomerSelect.find(`option[value="${response.customer.customer_id}"]`).length === 0) {
                            registrationCustomerSelect.append(`<option value="${response.customer.customer_id}">${response.customer.customer_name}</option>`);
                        }
                        registrationCustomerSelect.val(response.customer.customer_id);
                        $('#id_phone1').val(response.customer.phone_1 || '');
                        $('#customer-form-section').hide();
                        $('#registration-form-section').show();
                        $('#customerModalLabel').text('Add Registration');
                        
                        const roomSelect = $('select[name="room_select"]');
                        const selectedRoomId = roomSelect.val();
                        if (selectedRoomId && $('#id_room').find(`option[value="${selectedRoomId}"]`).length > 0) {
                            $('#id_room').val(selectedRoomId);
                            console.log('Pre-selected room in registration form:', selectedRoomId);
                        } else {
                            $('#id_room').val('');
                            console.log('No room pre-selected in registration form');
                        }
                    } else {
                        alert('Customer added successfully!');
                        $('#customerModal').modal('hide');
                        $form[0].reset();
                    }
                } else {
                    const errorMsg = response.error || 'Invalid response from server';
                    alert('Error adding customer: ' + errorMsg);
                }
                $submitBtn.prop('disabled', false).text('Save Customer');
            },
            error: function(xhr, status, error) {
                let errorMsg = 'Unknown error occurred';
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    errorMsg = errorData.error || errorData.errors || xhr.statusText || 'Unknown error';
                } catch (e) {
                    errorMsg = xhr.statusText || 'Unknown error';
                }
                console.error('Error adding customer:', {
                    status: xhr.status,
                    error: error,
                    responseText: xhr.responseText
                });
                alert(`Error adding customer: ${errorMsg}. Please check the console for details.`);
                $submitBtn.prop('disabled', false).text('Save Customer');
            }
        });
    });

    $('#registration-form').submit(function(e) {
        e.preventDefault();
        const formData = $(this).serialize();
        const roomId = $('#id_room').val(); 
        console.log('Registration form submitted with room_id:', roomId);
        console.log('Form data:', formData);

        $.ajax({
            url: window.registrationAddUrl,
            method: 'POST',
            data: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                console.log('Registration response:', response);
                if (response.status === 'success') {
                    alert('Registration completed successfully!');
                    currentRegistrationId = response.registration_id;

                    const customerSelect = $('select[name="customer_select"]');
                    customerSelect.empty().append('<option value="" disabled>👤 Customer</option>');
                    fetch(window.getCustomersUrl, {
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(customers => {
                        customers.forEach(customer => {
                            customerSelect.append(`<option value="${customer.customer_id}">${customer.customer_name}</option>`);
                        });
                        if (response.customer_id) {
                            customerSelect.val(response.customer_id);
                            console.log('Customer select updated to:', response.customer_id);
                        } else {
                            customerSelect.val(customerSelect.find('option:contains("Walking Customer")').val() || '');
                            console.log('Customer select set to default (Walking Customer)');
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching customers:', error);
                        alert('Error refreshing customer list. Please try again.');
                    });

                    const roomSelect = $('select[name="room_select"]');
                    let selectedRoomId = roomId || response.room_id; 
                    if (selectedRoomId) {
                        
                        selectedRoomId = String(selectedRoomId);
                        
                        if (roomSelect.find('option').filter(function() { 
                            return String($(this).val()) === selectedRoomId; 
                        }).length === 0) {
                            if (response.room_name && response.location) {
                                roomSelect.append(`<option value="${selectedRoomId}">${response.room_name} (${response.location})</option>`);
                                console.log('Added room to dropdown:', selectedRoomId, response.room_name, response.location);
                            } else {
                                fetch(`/api/rooms/${selectedRoomId}`, {
                                    headers: {
                                        'X-CSRFToken': getCookie('csrftoken')
                                    }
                                })
                                .then(res => {
                                    if (!res.ok) {
                                        throw new Error(`HTTP error! Status: ${res.status}`);
                                    }
                                    return res.json();
                                })
                                .then(room => {
                                    if (room.room_name && room.location) {
                                        roomSelect.append(`<option value="${selectedRoomId}">${room.room_name} (${room.location})</option>`);
                                        console.log('Fetched and added room to dropdown:', selectedRoomId, room.room_name, room.location);
                                    } else {
                                        console.warn('Room details missing in API response');
                                        alert('Room selected but details not available. Please check room configuration.');
                                        selectedRoomId = null; 
                                    }
                                })
                                .catch(error => {
                                    console.error('Error fetching room details:', error);
                                    alert('Error fetching room details. Please try again.');
                                    selectedRoomId = null; 
                                });
                            }
                        }
                        if (selectedRoomId) {
                            roomSelect.val(selectedRoomId);
                            currentServiceType = 'ROOM';
                            currentServiceId = selectedRoomId;
                            console.log('Room select updated to:', selectedRoomId, roomSelect.find('option:selected').text());

                            $.ajax({
                                url: window.homeUrl,
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                data: {
                                    room_id: selectedRoomId
                                },
                                success: function() {
                                    console.log('Session updated with room_id:', selectedRoomId);
                                },
                                error: function(xhr, status, error) {
                                    console.error('Error updating session with room_id:', xhr.status, error, xhr.responseText);
                                    alert('Error updating room selection. Please try again.');
                                }
                            });
                        }
                    } else {
                        console.warn('No room_id found in form or response');
                        roomSelect.val(''); 
                        currentServiceType = '';
                        currentServiceId = 0;
                        
                        $.ajax({
                            url: window.homeUrl,
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': getCookie('csrftoken')
                            },
                            data: {
                                clear_room: '1'
                            },
                            success: function() {
                                console.log('Cleared room selection from session');
                            },
                            error: function(xhr, status, error) {
                                console.error('Error clearing room selection:', xhr.status, error);
                            }
                        });
                    }

                    $('#customerModal').modal('hide');
                    $('#registration-form')[0].reset();
                    window.history.pushState({}, '', window.location.pathname);
                } else {
                    console.error('Registration failed:', response.errors || 'Unknown error');
                    alert('Error adding registration: ' + (response.errors ? JSON.stringify(response.errors) : 'Unknown error'));
                }
            },
            error: function(xhr, status, error) {
                console.error('Error adding registration:', xhr.status, error, xhr.responseText);
                alert('Error adding registration. Please try again.');
            }
        });
    });

    $('#customerModal').on('hidden.bs.modal', function() {
        $('#customer-search-section').hide();
        $('#customer-form-section').hide();
        $('#registration-form-section').hide();
        $('#customer-search-results').empty();
        $('#customer-search-input').val('');
        $('#id_customer').val('');
        $('#id_phone1').val('');
        $('#id_room').val('');
        $('#customerModalLabel').text('Customer and Registration');
        $('#customer-form')[0].reset();
        $('#registration-form')[0].reset();
        isRegistrationProcess = false;
    });

    updateSaleTotal();
    updateTime();
    filterItems('all');
    setInterval(updateTime, 1000);

    document.querySelector('.nav-button.mult').addEventListener('click', () => {
        if (keypadInput && currentSaleItems.length > 0) {
            const multiplier = parseInt(keypadInput);
            const lastItem = currentSaleItems[currentSaleItems.length - 1];
            lastItem.quantity = multiplier;
            keypadInput = '';
            updateSalesTable();
            updateSaleTotal();
        }
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function calculateSaleTotals() {
    let subtotal = 0;
    let totalTax = 0;
    let totalDiscount = 0;

    currentSaleItems.forEach(item => {
        const basePrice = item.price * item.quantity;
        const discountAmount = basePrice * (item.discount / 100);
        const taxableAmount = basePrice - discountAmount;
        const taxAmount = taxableAmount * (item.tax / 100);
        
        subtotal += basePrice;
        totalDiscount += discountAmount;
        totalTax += taxAmount;
    });

    return {
        subtotal: subtotal,
        tax: totalTax,
        discount: totalDiscount,
        grandTotal: subtotal - totalDiscount + totalTax
    };
}

function updateSaleTotal() {
    const totals = calculateSaleTotals();
    document.getElementById('saleTotal').textContent = `TOTAL: ${totals.grandTotal.toFixed(2)}`;
    document.getElementById('subtotal').textContent = `SUBTOTAL: ${totals.subtotal.toFixed(2)}`;
    document.getElementById('nonTax').textContent = `NON-TAX: ${(totals.subtotal - totals.tax).toFixed(2)}`;
    document.getElementById('taxTotal').textContent = `TAX: ${totals.tax.toFixed(2)}`;
    document.getElementById('discountTotal').textContent = `DISCOUNT: ${totals.discount.toFixed(2)}`;
}

function addItemToSale(productId, productName, salePrice) {
    fetch(`/api/products/?product_id=${productId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(products => {
            const product = products[0];
            const existingItem = currentSaleItems.find(item => item.id === productId);
            
            if (existingItem) {
                existingItem.quantity++;
            } else {
                currentSaleItems.push({
                    id: productId,
                    name: productName,
                    price: parseFloat(salePrice),
                    discount: parseFloat(product.discount || 0),
                    tax: parseFloat(product.tax || 0),
                    quantity: 1
                });
            }
            updateSalesTable();
            updateSaleTotal();
        })
        .catch(error => console.error('Error fetching product:', error));
}

function updateSalesTable() {
    const tbody = document.getElementById('salesTableBody');
    tbody.innerHTML = '';

    currentSaleItems.forEach((item, index) => {
        const basePrice = item.price * item.quantity;
        const discountAmount = basePrice * (item.discount / 100);
        const taxableAmount = basePrice - discountAmount;
        const taxAmount = taxableAmount * (item.tax / 100);
        const itemTotal = taxableAmount + taxAmount;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.name}</td>
            <td contenteditable="true" class="editable" data-index="${index}" data-field="quantity">${item.quantity}</td>
            <td contenteditable="true" class="editable" data-index="${index}" data-field="price">${item.price.toFixed(2)}</td>
            <td contenteditable="true" class="editable" data-index="${index}" data-field="discount">${item.discount.toFixed(1)}%</td>
            <td contenteditable="true" class="editable" data-index="${index}" data-field="tax">${item.tax.toFixed(1)}%</td>
            <td>${itemTotal.toFixed(2)}</td>
        `;
        tbody.appendChild(row);
    });

    document.querySelectorAll('.editable').forEach(cell => {
        cell.addEventListener('focus', function () {
            this.dataset.originalValue = this.textContent;
        });

        cell.addEventListener('blur', function () {
            const index = this.dataset.index;
            const field = this.dataset.field;
            let newValue = this.textContent.trim();

            if (field === 'discount' || field === 'tax') {
                newValue = parseFloat(newValue.replace('%', '')) || 0;
            } else {
                newValue = parseFloat(newValue) || 0;
            }

            if (field === 'quantity' && newValue >= 0) {
                currentSaleItems[index].quantity = newValue;
            } else if (field === 'price' && newValue >= 0) {
                currentSaleItems[index].price = newValue;
            } else if (field === 'discount' && newValue >= 0) {
                currentSaleItems[index].discount = newValue;
            } else if (field === 'tax' && newValue >= 0) {
                currentSaleItems[index].tax = newValue;
            } else {
                this.textContent = this.dataset.originalValue;
                return;
            }

            if (field === 'quantity' && newValue === 0) {
                currentSaleItems.splice(index, 1);
            }

            updateSalesTable();
            updateSaleTotal();
        });

        cell.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    });
}

function addToKeypad(value) {
    keypadInput += value;
}

function clearSale() {
    currentSaleItems = [];
    keypadInput = '';
    currentRegistrationId = null;
    currentServiceType = '';
    currentServiceId = 0;
    updateSalesTable();
    updateSaleTotal();
    $('select[name="table_select"]').val('');
    $('select[name="room_select"]').val('');
    $('select[name="vehicle_select"]').val('');
    $('select[name="customer_select"]').val($('select[name="customer_select"]').find('option:contains("Walking Customer")').val() || '');
    refreshNextSaleNo();
}

function incrementItem() {
    if (currentSaleItems.length > 0) {
        currentSaleItems[currentSaleItems.length - 1].quantity++;
        updateSalesTable();
        updateSaleTotal();
    }
}

function decrementItem() {
    if (currentSaleItems.length > 0) {
        const lastItem = currentSaleItems[currentSaleItems.length - 1];
        if (lastItem.quantity > 1) {
            lastItem.quantity--;
        } else {
            currentSaleItems.pop();
        }
        updateSalesTable();
        updateSaleTotal();
    }
}

function filterItems(groupId) {
    fetch(`/api/products/?group_id=${groupId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(products => {
            const posGrid = document.getElementById('posGrid');
            posGrid.innerHTML = '';

            if (products.length === 0) {
                posGrid.innerHTML = '<p>No products available.</p>';
                return;
            }

            products.forEach(product => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'pos-item';
                itemDiv.onclick = () => addItemToSale(product.product_id, product.product_name, product.sale_price);
                itemDiv.innerHTML = `
                    <img src="${product.product_image || ''}" alt="${product.product_name}" style="display: ${product.product_image ? 'block' : 'none'};">
                    <p>${product.product_name}</p>
                    <p>₹${product.sale_price}</p>
                `;
                posGrid.appendChild(itemDiv);
            });
        })
        .catch(error => console.error('Error filtering products:', error));
}

function completeSale(paymentMethod = 'DEFAULT') {
    if (currentSaleItems.length === 0) {
        alert('No items in sale!');
        return;
    }

    const totals = calculateSaleTotals();
    const customerSelect = document.querySelector('select[name="customer_select"]');
    const clientDate = new Date().toLocaleDateString('en-CA');
    const saleData = {
        items: currentSaleItems.map(item => ({
            ...item,
            item_total: (item.price * item.quantity * (1 - item.discount/100) * (1 + item.tax/100))
        })),
        subtotal: totals.subtotal,
        total_discount: totals.discount,
        total_tax: totals.tax,
        grand_total: totals.grandTotal,
        payment_method: paymentMethod,
        customer_id: customerSelect.value || null,
        registration_id: currentRegistrationId,
        service_type: currentServiceType,
        service_id: currentServiceId,
        sale_date: clientDate
    };

    fetch('/api/complete-sale/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(saleData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Sale completed successfully!');
            clearSale();
            window.history.pushState({}, '', window.location.pathname);
        } else {
            alert('Error completing sale: ' + JSON.stringify(data.errors));
        }
    })
    .catch(error => {
        console.error('Error completing sale:', error);
        alert('Error completing sale. Please try again.');
    });
}

function saveSale() {
    if (currentSaleItems.length === 0) {
        alert('No items to save!');
        return;
    }

    const totals = calculateSaleTotals();
    const customerSelect = document.querySelector('select[name="customer_select"]');
    const tableSelect = document.querySelector('select[name="table_select"]');
    const roomSelect = document.querySelector('select[name="room_select"]');
    const vehicleSelect = document.querySelector('select[name="vehicle_select"]');
    const clientDate = new Date().toLocaleDateString('en-CA');

    const customerId = customerSelect && customerSelect.selectedIndex > 0 ? customerSelect.value : null;
    const tableId = tableSelect && tableSelect.selectedIndex > 0 ? tableSelect.value : null;
    const roomId = roomSelect && roomSelect.selectedIndex > 0 ? roomSelect.value : null;
    const vehicleId = vehicleSelect && vehicleSelect.selectedIndex > 0 ? vehicleSelect.value : null;

    if (!customerId) {
        alert('Please select a customer before saving the sale.');
        return;
    }

    const saleData = {
        items: currentSaleItems,
        totals: {
            subtotal: totals.subtotal,
            discount: totals.discount,
            tax: totals.tax,
            grandTotal: totals.grandTotal
        },
        customer_id: customerId,
        table_id: tableId,
        room_id: roomId,
        vehicle_id: vehicleId,
        registration_id: currentRegistrationId,
        service_type: currentServiceType,
        service_id: currentServiceId,
        sale_date: clientDate
    };

    fetch('/api/save-sale/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(saleData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Sale saved successfully!');
            clearSale();
            window.history.pushState({}, '', window.location.pathname);
        } else {
            alert('Something went wrong while saving the sale. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error saving sale:', error);
        alert('A technical error occurred. Please contact support if the problem continues.');
    });
}

function printSale() {
    if (currentSaleItems.length === 0) {
        alert('No items to print!');
        return;
    }

    const totals = calculateSaleTotals();
    const customerName = document.querySelector('select[name="customer_select"]').selectedOptions[0]?.text || 'N/A';
    const clientDate = new Date().toLocaleDateString('en-CA');

    const receiptWindow = window.open('', '_blank', 'width=300,height=400');
    receiptWindow.document.write(`
        <html>
        <head>
            <title>Receipt</title>
            <style>
                body { font-family: Arial, sans-serif; width: 300px; padding: 10px; }
                h2 { text-align: center; }
                .item { display: flex; justify-content: space-between; }
                .total { font-weight: bold; margin-top: 10px; }
            </style>
        </head>
        <body>
            <h2>Receipt</h2>
            <p>Customer: ${customerName}</p>
            <p>Date: ${clientDate}</p>
            <p>Service Type: ${currentServiceType || 'N/A'}</p>
            <p>Service ID: ${currentServiceId || 'N/A'}</p>
            <hr>
            ${currentSaleItems.map(item => `
                <div class="item">
                    <span>${item.name} (x${item.quantity})</span>
                    <span>₹${(item.price * item.quantity * (1 - item.discount / 100) * (1 + item.tax / 100)).toFixed(2)}</span>
                </div>
            `).join('')}
            <hr>
            <div class="total">Subtotal: ₹${totals.subtotal.toFixed(2)}</div>
            <div class="total">Discount: ₹${totals.discount.toFixed(2)}</div>
            <div class="total">Tax: ₹${totals.tax.toFixed(2)}</div>
            <div class="total">Grand Total: ₹${totals.grandTotal.toFixed(2)}</div>
        </body>
        </html>
    `);
    receiptWindow.document.close();
    receiptWindow.print();
    receiptWindow.close();
}

function initiatePayment() {
    if (currentSaleItems.length === 0) {
        alert('No items in sale! Please add items before proceeding to payment.');
        return;
    }

    saveSaleForPayment()
        .then(data => {
            if (data && data.sale_id) {
                const url = `/process_payment/?sale_id=${data.sale_id}`;
                window.location.href = url;
            } else {
                alert('Failed to save sale. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error initiating payment:', error);
            alert('Error initiating payment. Please try again.');
        });
}

function saveSaleForPayment() {
    return new Promise((resolve, reject) => {
        if (currentSaleItems.length === 0) {
            alert('No items to save!');
            reject('No items');
            return;
        }

        const totals = calculateSaleTotals();
        const customerSelect = document.querySelector('select[name="customer_select"]');
        const tableSelect = document.querySelector('select[name="table_select"]');
        const roomSelect = document.querySelector('select[name="room_select"]');
        const vehicleSelect = document.querySelector('select[name="vehicle_select"]');
        const clientDate = new Date().toLocaleDateString('en-CA');

        const customerId = customerSelect && customerSelect.selectedIndex > 0 ? customerSelect.value : null;
        const tableId = tableSelect && tableSelect.selectedIndex > 0 ? tableSelect.value : null;
        const roomId = roomSelect && roomSelect.selectedIndex > 0 ? roomSelect.value : null;
        const vehicleId = vehicleSelect && vehicleSelect.selectedIndex > 0 ? vehicleSelect.value : null;

        if (!customerId) {
            alert('Please select a customer before proceeding to payment.');
            reject('No customer selected');
            return;
        }

        const saleData = {
            items: currentSaleItems,
            totals: {
                subtotal: totals.subtotal,
                discount: totals.discount,
                tax: totals.tax,
                grandTotal: totals.grandTotal
            },
            customer_id: customerId,
            table_id: tableId,
            room_id: roomId,
            vehicle_id: vehicleId,
            registration_id: currentRegistrationId,
            service_type: currentServiceType,
            service_id: currentServiceId,
            sale_date: clientDate
        };

        fetch('/api/save-sale/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(saleData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.sale_id) {
                resolve(data);
                window.history.pushState({}, '', window.location.pathname);
            } else {
                reject('Failed to save sale');
            }
        })
        .catch(error => {
            console.error('Error saving sale:', error);
            reject(error);
        });
    });
}

function refreshNextSaleNo() {
    const clientDate = new Date().toLocaleDateString('en-CA');
    fetch(`/api/next-sale-no/?target_date=${clientDate}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.status === 401 || response.status === 403) {
            alert('Session expired. Please log in again.');
            window.location.href = '/login/';
        }
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.next_sale_no) {
            document.querySelector('.sale-number').textContent = data.next_sale_no;
            console.log('Updated next_sale_no:', data.next_sale_no, 'Client date:', clientDate);
        } else {
            console.error('No next_sale_no in response:', data);
            alert('Failed to refresh sale number. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error fetching next_sale_no:', error);
        alert('Error fetching next sale number. Please check the console.');
    });
}

function toggleNav() {
    document.querySelector('.nav-buttons').classList.toggle('active');
    document.querySelector('.control-panel').classList.remove('active');
    document.querySelectorAll('.overlay').forEach(overlay => overlay.classList.toggle('active', document.querySelector('.nav-buttons').classList.contains('active')));
}

function toggleControlPanel() {
    document.querySelector('.control-panel').classList.toggle('active');
    document.querySelector('.nav-buttons').classList.remove('active');
    document.querySelectorAll('.overlay').forEach(overlay => overlay.classList.toggle('active', document.querySelector('.control-panel').classList.contains('active')));
}

function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
}

if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.pathname);
}