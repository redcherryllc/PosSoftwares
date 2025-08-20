let currentSaleItems = [];
let keypadInput = '';

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
        .then(response => response.json())
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
    updateSalesTable();
    updateSaleTotal();
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
        .then(response => response.json())
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
                    <img src="${product.product_image || '/static/images/default.png'}" alt="${product.product_name}">
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
        customer_name: document.getElementById('customerName').value,
        timestamp: new Date().toISOString()
    };

    fetch('/api/complete-sale/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(saleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Sale completed successfully!');
            clearSale();
            document.getElementById('customerName').value = '';
        }
    })
    .catch(error => console.error('Error completing sale:', error));
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
        vehicle_id: vehicleId
    };

    fetch('/api/save-sale/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(saleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Sale saved successfully!');
            clearSale();
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
    saveSale()
        .then(saleId => {
            if (saleId) {
                const receiptWindow = window.open('', '_blank', 'width=300,height=400');
                const totals = calculateSaleTotals();
                const customerName = document.querySelector('select[name="customer_select"]').selectedOptions[0]?.text || 'N/A';

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
                        <p>Sale ID: ${saleId}</p>
                        <p>Customer: ${customerName}</p>
                        <p>Date: ${new Date().toLocaleString()}</p>
                        <hr>
                        ${currentSaleItems.map(item => `
                            <div class="item">
                                <span>${item.name} (x${item.quantity})</span>
                                <span>$${(item.price * item.quantity - (item.price * item.quantity * (item.discount / 100)) + (item.price * item.quantity * (item.tax / 100))).toFixed(2)}</span>
                            </div>
                        `).join('')}
                        <hr>
                        <div class="total">Subtotal: $${totals.subtotal.toFixed(2)}</div>
                        <div class="total">Discount: $${totals.discount.toFixed(2)}</div>
                        <div class="total">Tax: $${totals.tax.toFixed(2)}</div>
                        <div class="total">Grand Total: $${totals.grandTotal.toFixed(2)}</div>
                    </body>
                    </html>
                `);
                receiptWindow.document.close();
                receiptWindow.print();
                receiptWindow.close();
            }
        })
        .catch(error => {
            console.error('Error printing sale:', error);
        });
}

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

document.querySelector('.nav-button.save').addEventListener('click', saveSale);

document.querySelector('.nav-button.print').addEventListener('click', printSale);

document.querySelector('select[name="table_select"]').addEventListener('change', function() {
    const selected = this.options[this.selectedIndex].text;
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

function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
}
setInterval(updateTime, 1000);

document.addEventListener('DOMContentLoaded', () => {
    updateSaleTotal();
    updateTime();
    filterItems('all');
});






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
                alert('An error occurred while initiating payment. Please try again.');
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
                vehicle_id: vehicleId
            };
    
            fetch('/api/save-sale/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(saleData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.sale_id) {
                    clearSale(); 
                    resolve(data); 
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





document.addEventListener('DOMContentLoaded', () => {
    
    const customerForm = document.querySelector('#customerModal form');
    if (customerForm) {
        customerForm.addEventListener('submit', function (e) {
            e.preventDefault(); 

            const formData = new FormData(this);
            const addCustomerUrl = document.getElementById('customerModal').dataset.addCustomerUrl || '/add-customer/';

            fetch(addCustomerUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.customer) {
                   
                    const customerModalElement = document.getElementById('customerModal');
                    const customerModal = bootstrap.Modal.getInstance(customerModalElement) || new bootstrap.Modal(customerModalElement);
                    customerModal.hide();

                    
                    const customerSelect = document.querySelector('select[name="customer_select"]');
                    if (customerSelect) {
                        const newCustomer = data.customer;
                        const option = document.createElement('option');
                        option.value = newCustomer.customer_id;
                        option.textContent = newCustomer.customer_name;
                        if (newCustomer.customer_name === "Walking Customer") {
                            option.selected = true;
                        }
                        customerSelect.appendChild(option);
                        customerSelect.value = newCustomer.customer_id;

                        
                        customerForm.reset();
                    } else {
                        console.error('Customer select dropdown not found');
                    }

                    
                    alert('Customer added successfully!');
                } else {
                    alert('Failed to add customer: ' + (data.error || 'Please check the form fields.'));
                }
            })
            .catch(error => {
                console.error('Error adding customer:', error);
                alert('An error occurred while adding the customer. Please try again.');
            });
        });
    } else {
        console.error('Customer form not found');
    }

    
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
});        