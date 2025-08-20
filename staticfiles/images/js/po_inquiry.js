document.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const startDate = urlParams.get('start_date');
            const endDate = urlParams.get('end_date');
            
            if (startDate) {
                document.getElementById('start_date').value = startDate;
            }
            if (endDate) {
                document.getElementById('end_date').value = endDate;
            }
            if (startDate || endDate) {
                filterTableByDate();
            }
        });

        function resetFilters() {
            const startDateInput = document.getElementById('start_date');
            const endDateInput = document.getElementById('end_date');
            if (startDateInput) startDateInput.value = '';
            if (endDateInput) endDateInput.value = '';
            window.location.href = window.location.pathname;
        }

        function filterTableByDate() {
            const startDate = document.getElementById('start_date')?.value;
            const endDate = document.getElementById('end_date')?.value;
            const rows = document.querySelectorAll('.po-row');
            let visibleCount = 0;

            rows.forEach(row => {
                const orderDate = row.getAttribute('data-order-date');
                if (startDate && endDate) {
                    if (orderDate >= startDate && orderDate <= endDate) {
                        row.classList.remove('hidden-row');
                        visibleCount++;
                    } else {
                        row.classList.add('hidden-row');
                    }
                } else if (startDate) {
                    if (orderDate >= startDate) {
                        row.classList.remove('hidden-row');
                        visibleCount++;
                    } else {
                        row.classList.add('hidden-row');
                    }
                } else if (endDate) {
                    if (orderDate <= endDate) {
                        row.classList.remove('hidden-row');
                        visibleCount++;
                    } else {
                        row.classList.add('hidden-row');
                    }
                } else {
                    row.classList.remove('hidden-row');
                    visibleCount++;
                }
            });

            const noResultsRow = document.getElementById('no-results-row');
            if (visibleCount === 0) {
                if (!noResultsRow) {
                    const tbody = document.getElementById('po-table-body');
                    if (tbody) {
                        const newRow = document.createElement('tr');
                        newRow.id = 'no-results-row';
                        newRow.innerHTML = '<td colspan="8" class="border p-2 text-center">No purchase orders found matching the date criteria.</td>';
                        tbody.appendChild(newRow);
                    }
                } else {
                    noResultsRow.classList.remove('hidden-row');
                }
            } else if (noResultsRow) {
                noResultsRow.classList.add('hidden-row');
            }
        }

        document.getElementById('dateFilterForm').addEventListener('submit', (e) => {
            e.preventDefault();
            filterTableByDate();
            const startDate = document.getElementById('start_date')?.value;
            const endDate = document.getElementById('end_date')?.value;
            const url = new URL(window.location);
            if (startDate) {
                url.searchParams.set('start_date', startDate);
            } else {
                url.searchParams.delete('start_date');
            }
            if (endDate) {
                url.searchParams.set('end_date', endDate);
            } else {
                url.searchParams.delete('end_date');
            }
            window.history.pushState({}, '', url);
        });

        function printTable() {
            window.print();
        }

        function exportToExcel() {
            const wb = XLSX.utils.book_new();
            const tableData = [];
            const headerRow = [];
            const headerCells = document.querySelectorAll('#purchase-order-table thead th');
            headerCells.forEach(cell => {
                if (!cell.classList.contains('no-print')) {
                    headerRow.push(cell.textContent.trim());
                }
            });
            tableData.push(headerRow);

            const rows = document.querySelectorAll('#purchase-order-table tbody tr:not(.hidden-row)');
            rows.forEach(row => {
                if (row.cells.length > 1) {
                    const dataRow = [];
                    Array.from(row.cells).forEach((cell, index) => {
                        if (!cell.classList.contains('no-print')) {
                            if ([2, 3, 4].includes(index) && cell.hasAttribute('data-value')) {
                                const value = cell.getAttribute('data-value');
                                dataRow.push(value === "" ? 0 : parseFloat(value));
                            } else if (index === 6) {
                                const value = cell.getAttribute('data-value');
                                dataRow.push(value === "" ? 0 : parseInt(value));
                            } else {
                                dataRow.push(cell.textContent.trim());
                            }
                        }
                    });
                    tableData.push(dataRow);
                }
            });

            const ws = XLSX.utils.aoa_to_sheet(tableData);
            const columnFormats = [
                {wch: 15}, // PO Number
                {wch: 30}, // Supplier
                {wch: 15}, // Total Amount
                {wch: 15}, // Paid Amount
                {wch: 15}, // Balance Due
                {wch: 15}, // Payment Status
                {wch: 15}  // Order Items Count
            ];
            ws['!cols'] = columnFormats;
            XLSX.utils.book_append_sheet(wb, ws, "Purchase Orders");
            XLSX.writeFile(wb, "purchase_order_inquiry.xlsx");
        }