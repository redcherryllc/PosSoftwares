function printOrder(saleId) {
            fetch(`/api/get-sale-details/?sale_id=${saleId}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const sale = data.sale;
                    const items = data.items;
                    const currentTime = new Date(); 
    
                    const printWindow = window.open('', '_blank', 'width=300,height=400');
                    printWindow.document.write(`
                        <html>
                        <head>
                            <title>Receipt - ${sale.sale_no}</title>
                            <style>
                                body { 
                                    font-family: 'Courier New', monospace;
                                    width: 280px;
                                    padding: 10px;
                                    line-height: 1.2;
                                    font-size: 12px;
                                }
                                h2 { 
                                    text-align: center;
                                    font-size: 14px;
                                    margin: 0;
                                }
                                .header, .footer { 
                                    text-align: center;
                                    margin-bottom: 5px;
                                }
                                .item { 
                                    display: flex;
                                    justify-content: space-between;
                                    margin-bottom: 2px;
                                }
                                .item-name { 
                                    flex: 1;
                                    text-align: left;
                                    overflow: hidden;
                                    white-space: nowrap;
                                }
                                .item-qty, .item-amount { 
                                    width: 40px;
                                    text-align: right;
                                }
                                .total { 
                                    display: flex;
                                    justify-content: space-between;
                                    font-weight: bold;
                                    margin-top: 5px;
                                }
                                .paid-amount { 
                                    display: flex;
                                    justify-content: space-between;
                                    font-weight: bold;
                                    margin-top: 5px;
                                    font-size: 14px;
                                }
                                hr { 
                                    border: none;
                                    border-top: 1px dashed #000;
                                    margin: 5px 0;
                                }
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h2>Receipt</h2>
                                <p>${sale.business_unit_group_name || 'N/A'}</p>
                                <p>${sale.business_unit_name || 'N/A'}</p>
                                <p>${sale.branch_name || 'N/A'}</p>
                                <p>${sale.saas_customer_name || 'N/A'}</p>
                            </div>
                            <hr>
                            <p>Sale No: ${sale.sale_no}</p>
                            <p>Customer: ${sale.customer_name || 'N/A'}</p>
                            <p>Total Items: ${sale.total_items}</p>
                            <p>Date: ${currentTime.toLocaleString()}</p>
                            <hr>
                            <div>
                                ${items.map(item => `
                                    <div class="item">
                                        <span class="item-name">${item.product_name}</span>
                                        <span class="item-qty">x${item.qty}</span>
                                        <span class="item-amount">${item.total_amount.toFixed(2)}</span>
                                    </div>
                                `).join('')}
                            </div>
                            <hr>
                            <div class="total">
                                <span>Subtotal:</span>
                                <span>${(sale.total_amount - sale.tax_amount + sale.discount_amount).toFixed(2)}</span>
                            </div>
                            <div class="total">
                                <span>Discount:</span>
                                <span>${sale.discount_amount.toFixed(2)}</span>
                            </div>
                            <div class="total">
                                <span>Tax:</span>
                                <span>${sale.tax_amount.toFixed(2)}</span>
                            </div>
                            <hr>
                            <div class="total">
                                <span>Grand Total:</span>
                                <span>${sale.total_amount.toFixed(2)}</span>
                            </div>
                            <div class="paid-amount">
                                <span>Paid Amount:</span>
                                <span>${(sale.paid_amount || 0).toFixed(2)}</span>
                            </div>
                            <div class="footer">
                                <p>Thank You!</p>
                            </div>
                        </body>
                        </html>
                    `);
                    printWindow.document.close();
                    printWindow.print();
                    printWindow.close();
                } else {
                    alert('Failed to retrieve sale details.');
                }
            })
            .catch(error => {
                console.error('Error fetching sale details:', error);
                alert('A technical error occurred while printing.');
            });
        }