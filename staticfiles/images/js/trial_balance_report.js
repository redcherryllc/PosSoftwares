function printTable() {
            window.print();
        }

        function exportToExcel() {
            const wb = XLSX.utils.book_new();
            const tableData = [];
            const headerRow = [];
            
            
            const table = document.querySelector('#trial-balance-table:not(.hidden)') || 
                         document.querySelector('#trial-balance-table-tablet:not(.hidden)') ||
                         document.querySelector('#trial-balance-table');
            
            if (!table) {
               
                const cards = document.querySelectorAll('.md\\:hidden .bg-gray-50');
                if (cards.length > 0) {
                    tableData.push(['Account Code', 'Account Name', 'Account Type', 'Total Debits', 'Total Credits', 'Balance']);
                    
                    
                }
            } else {
                const headerCells = table.querySelectorAll('thead th');
                headerCells.forEach(cell => {
                    headerRow.push(cell.textContent.trim());
                });
                tableData.push(headerRow);
                
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    if (row.cells.length > 1) {
                        const dataRow = [];
                        Array.from(row.cells).forEach((cell, index) => {
                            if (index >= 3 && index <= 5 && cell.hasAttribute('data-value')) {
                                const value = cell.getAttribute('data-value');
                                dataRow.push(value === "" ? 0 : parseFloat(value));
                            } else {
                                dataRow.push(cell.textContent.trim());
                            }
                        });
                        tableData.push(dataRow);
                    }
                });
            }
            
            const ws = XLSX.utils.aoa_to_sheet(tableData);
            const columnFormats = [
                {wch: 15},
                {wch: 30},
                {wch: 15},
                {wch: 15},
                {wch: 15},
                {wch: 15}
            ];
            ws['!cols'] = columnFormats;
            XLSX.utils.book_append_sheet(wb, ws, "Trial Balance");
            XLSX.writeFile(wb, "trial_balance_report.xlsx");
        }