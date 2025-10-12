(function ($) {
    'use strict';

   
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

    const csrftoken = getCookie('csrftoken');
    const ajaxUrl = window.registrationAddUrl || '';

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            const safeMethod = /^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type);
            if (!safeMethod && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
    });

    $(function () {
       
        $('#customer-search-section').show();
        $('#customer-form-section, #registration-form-section').hide();

        
        function escapeHtml(text) {
            return $('<div/>').text(text).html();
        }

        function showMessage(msg) {
            $('#customer-search-results').html(`<p class="text-gray-600 text-sm">${msg}</p>`);
        }

        
        function doSearch() {
            const query = $('#customer-search-input').val().trim();
            if (!query) {
                showMessage('Please enter a search term.');
                return;
            }

            showMessage('Searching...');
            $.ajax({
                url: ajaxUrl,
                method: 'GET',
                data: { action: 'search_customer', q: query },
                dataType: 'json',
                success: function (response) {
                    const results = $('#customer-search-results');
                    results.empty();

                    if (response.customers && response.customers.length > 0) {
                        let html = '<ul class="space-y-2">';
                        response.customers.forEach(c => {
                            html += `
                                <li class="p-3 bg-white border rounded-md flex justify-between items-center">
                                    <div>
                                        <div class="font-medium">${escapeHtml(c.name)}</div>
                                        <div class="text-sm text-gray-600">Phone: ${escapeHtml(c.phone || 'N/A')} | Aadhaar: ${escapeHtml(c.aadhaar || 'N/A')}</div>
                                    </div>
                                    <button type="button" class="select-customer bg-blue-500 text-white px-3 py-1 rounded-md hover:bg-blue-600"
                                            data-id="${c.id}" data-name="${escapeHtml(c.name)}" data-phone="${escapeHtml(c.phone || '')}">
                                        Select
                                    </button>
                                </li>`;
                        });
                        html += '</ul>';
                        results.html(html);
                    } else {
                        results.html('<p class="text-gray-600 text-sm">No customers found. <a href="#" id="show-customer-form" class="text-blue-500 hover:underline">Add new customer</a>.</p>');
                    }
                },
                error: function () {
                    showMessage('Error searching customers. Please try again.');
                }
            });
        }

        $('#customer-search-btn').click(doSearch);
        $('#customer-search-input').keypress(function (e) {
            if (e.which === 13) {
                e.preventDefault();
                doSearch();
            }
        });

        
        $(document).on('click', '#show-customer-form', function (e) {
            e.preventDefault();
            $('#customer-search-section').hide();
            $('#customer-form-section').show();
            $('#registration-form-section').hide();
            $('#customer-form').find('input[type=text], input[type=email], textarea').val('');
        });

        
        $('#back-to-search-btn').click(() => {
            $('#customer-form-section').hide();
            $('#customer-search-section').show();
        });

        $('#back-to-customer-btn').click(() => {
            $('#registration-form-section').hide();
            $('#customer-search-section').show();
        });

        
        $(document).on('click', '.select-customer', function () {
            const id = $(this).data('id');
            const name = $(this).data('name');
            const phone = $(this).data('phone') || '';

            $('#hidden-customer-id').val(id);
            $('#display-customer-name').text(name);
            $('#display-customer-phone').text(phone || 'N/A');
            $('#selected-customer-info').show();
            $('#id_phone1').val(phone);

            $('#customer-search-section, #customer-form-section').hide();
            $('#registration-form-section').show();
        });

        
        $('#customer-form').submit(function (e) {
            e.preventDefault();

            const phone1 = $('#id_phone_1').val();
            const aadhaar = $('#id_aadhaar_card_no').val();

            if (!phone1 || !/^[0-9]{10}$/.test(phone1)) {
                alert('Please enter a valid 10-digit primary phone number.');
                return;
            }
            if (aadhaar && !/^[0-9]{12}$/.test(aadhaar)) {
                alert('Aadhaar number must be 12 digits.');
                return;
            }

            $.ajax({
                url: ajaxUrl,
                method: 'POST',
                data: $(this).serialize(),
                dataType: 'json',
                success: function (response) {
                    if (response.status === 'success') {
                        $('#hidden-customer-id').val(response.customer_id);
                        $('#display-customer-name').text(response.customer_name);
                        $('#display-customer-phone').text(response.customer_phone);
                        $('#selected-customer-info').show();
                        $('#id_phone1').val(response.customer_phone);
                        $('#customer-form-section').hide();
                        $('#registration-form-section').show();
                        alert('Customer added successfully! Please complete the registration.');
                    } else {
                        alert('Error: ' + JSON.stringify(response.errors));
                    }
                },
                error: function () {
                    alert('Error saving customer.');
                }
            });
        });

        
        $('#registration-form').submit(function (e) {
            e.preventDefault();
            const phone = $('#id_phone1').val();
            const customerId = $('#hidden-customer-id').val();

            if (!customerId) {
                alert('Please select or add a customer first.');
                return;
            }
            if (!/^[0-9]{10,15}$/.test(phone)) {
                alert('Enter a valid phone number (10–15 digits).');
                return;
            }

            $.ajax({
                url: ajaxUrl,
                method: 'POST',
                data: $(this).serialize(),
                dataType: 'json',
                success: function (response) {
                    if (response.status === 'success') {
                        alert('Registration added successfully!');
                        if (response.redirect) {
                            window.location.href = response.redirect;
                        } else {
                            location.reload();
                        }
                    } else {
                        alert('Error: ' + JSON.stringify(response.errors));
                    }
                },
                error: function () {
                    alert('Error saving registration.');
                }
            });
        });

              $('#customerModal').on('hidden.bs.modal', function () {
            $('#customer-search-section').show();
            $('#customer-form-section, #registration-form-section').hide();
            $('#selected-customer-info').hide();
            $('#customer-search-results').empty();
            $('#customer-search-input').val('');
            $('#hidden-customer-id').val('');
            $('#customer-form')[0].reset();
            $('#registration-form')[0].reset();
        });
    });

})(jQuery);
