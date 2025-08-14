$(document).ready(function() {
            var table = $('#stockTable').DataTable({
                dom: 'Bfrtip',
                buttons: [
                    {
                        extend: 'excel',
                        text: '<i class="fas fa-file-excel"></i> Export to Excel',
                        className: 'btn buttons-excel',
                        title: 'Stock_Report'
                    },
                    {
                        extend: 'print',
                        text: '<i class="fas fa-print"></i> Print',
                        className: 'btn buttons-print',
                        title: '',
                        customize: function(win) {
                            var allData = table.rows({ search: 'applied' }).data();
                            var tableHtml = '<table border="1" style="width:100%; border-collapse: collapse;">' +
                                '<thead><tr>' +
                                '<th>Product ID</th>' +
                                '<th>Product Name</th>' +
                                '<th>Stock</th>' +
                                '<th>Total Sold Qty</th>' +
                                '<th>Current Month Sold</th>' +
                                '<th>Last 6M Sold</th>' +
                                '<th>Monthly Avg Demand</th>' +
                                '<th>Stocking (6M)</th>' +
                                '<th>Excess Stock</th>' +
                                '<th>Total PO Qty</th>' +
                                '<th>Current Month PO</th>' +
                                '<th>Last 6M PO</th>' +
                                '<th>Return Stock</th>' +
                                '</tr></thead><tbody>';
                            for (var i = 0; i < allData.length; i++) {
                                tableHtml += '<tr>' +
                                    '<td>' + allData[i][0].replace(/<a[^>]*>(.*?)<\/a>/, '$1') + '</td>' +
                                    '<td>' + allData[i][1] + '</td>' +
                                    '<td>' + allData[i][2].replace(/class="[^"]*"/, '') + '</td>' +
                                    '<td>' + allData[i][3] + '</td>' +
                                    '<td>' + allData[i][4] + '</td>' +
                                    '<td>' + allData[i][5] + '</td>' +
                                    '<td>' + allData[i][6] + '</td>' +
                                    '<td>' + allData[i][7] + '</td>' +
                                    '<td>' + allData[i][8].replace(/class="[^"]*"/, '') + '</td>' +
                                    '<td>' + allData[i][9] + '</td>' +
                                    '<td>' + allData[i][10] + '</td>' +
                                    '<td>' + allData[i][11] + '</td>' +
                                    '<td>' + allData[i][12].replace(/class="[^"]*"/, '') + '</td>' +
                                    '</tr>';
                            }
                            tableHtml += '</tbody></table>';
                            $(win.document.body).html(tableHtml);
                            $(win.document.body).css({
                                'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                                'padding': '20px',
                                'margin': '0 auto',
                                'width': '100%'
                            });
                            $(win.document.body).find('table').css({
                                'border': '1px solid #000',
                                'width': '100%',
                                'border-collapse': 'collapse'
                            });
                            $(win.document.body).find('th, td').css({
                                'border': '1px solid #000',
                                'padding': '8px',
                                'text-align': 'center'
                            });
                            $(win.document.body).find('th').css({
                                'background-color': '#343a40',
                                'color': '#fff'
                            });
                        }
                    }
                ],
                pageLength: 10,
                responsive: true,
                order: [[0, 'asc']],
                language: {
                    search: "Filter records:",
                    searchPlaceholder: "Search..."
                },
                columnDefs: [
                    { responsivePriority: 1, targets: 0 },
                    { responsivePriority: 2, targets: 1 },
                    { responsivePriority: 3, targets: 2 }
                ]
            });
        });