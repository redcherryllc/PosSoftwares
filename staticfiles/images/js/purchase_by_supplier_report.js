document.querySelector('form').addEventListener('submit', function(e) {
            const startDate = document.getElementById('start_date').value;
            const endDate = document.getElementById('end_date').value;
            const today = new Date().toISOString().split('T')[0];

            if (!startDate || !endDate) {
                e.preventDefault();
                alert('Please select both start and end dates.');
                return;
            }

            if (startDate > endDate) {
                e.preventDefault();
                alert('Start date cannot be after end date.');
                return;
            }

            if (endDate > today) {
                e.preventDefault();
                alert('End date cannot be in the future.');
                return;
            }
        });

        function printReport() {
            window.print();
        }

        function exportToExcel() {
            const table = document.getElementById('purchaseTable');
            const wb = XLSX.utils.table_to_book(table, { sheet: "Purchase Report" });
            const filename = 'Purchase_by_Supplier_{{ start_date|date:"Y-m-d" }}_to_{{ end_date|date:"Y-m-d" }}.xlsx';
            XLSX.writeFile(wb, filename);
        }