function printTable() {
    window.print();
}

function exportToExcel() {
    const table = document.getElementById('suppliersTable');
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (const row of rows) {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => `"${col.innerText.replace(/"/g, '""')}"`).join(',');
        csv.push(rowData);
    }
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'suppliers_export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}