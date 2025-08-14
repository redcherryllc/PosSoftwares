import json
import logging
from decimal import Decimal
from functools import wraps
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import CustomerForm
from .models import (
    SAASUsers, SAASCustomer, BusinessUnitGroup, BusinessUnit, Branch,
    ProductGroup, Products, SalesHeader, SalesLine, Customer,
    Tables, Rooms, Vehicle, ChartOfAccounts, JournalEntries, JournalEntryLine,Suppliers,InventoryHeader,InventoryLine,Warehouse,Category
)

from django.db.models.functions import Coalesce
from django.db.models import Sum, Count, Avg, Q, Case, When, DecimalField, ExpressionWrapper, F,FloatField
from .models import SAASUsers, BusinessUnit, Branch, PurchaseOrders, PurchaseOrderItems, Suppliers
from .forms import PurchaseOrderForm, PurchaseOrderItemFormSet, StockAdjustmentForm
import logging

from datetime import timedelta
import calendar
from .forms import StockReportForm, StockAdjustmentForm
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from datetime import date
from .forms import SupplierForm, EditSupplierForm, ProductForm, RoomForm, TableForm, VehicleForm, CustomerForm

from .forms import EditProductGroupForm
from dateutil import relativedelta 

from datetime import datetime
import traceback

from django.db.models import Count, Q, F, Case, When, Value, IntegerField
from django.utils.dateparse import parse_date

from .forms import ProductGroupForm
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.functions import Cast, Substr

from django.contrib.auth import logout




logger = logging.getLogger(__name__)

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        missing_keys = []
        if 'saas_user_id' not in request.session:
            missing_keys.append('saas_user_id')
        if 'business_unit_id' not in request.session:
            missing_keys.append('business_unit_id')
        if 'branch_id' not in request.session:
            missing_keys.append('branch_id')
        
        if missing_keys:
            logger.warning(f"Access denied to {view_func.__name__}. Missing session keys: {missing_keys}")
            messages.error(request, f"Please log in and select a business unit and branch. Missing: {', '.join(missing_keys)}")
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def get_business_unit_groups(request):
    saas_customer_id = request.GET.get('saas_customer_id')
    if saas_customer_id:
        try:
            groups = BusinessUnitGroup.objects.filter(saas_customer_id=saas_customer_id)
            data = [{'business_unit_group_id': group.business_unit_group_id, 'business_unit_group_name': group.business_unit_group_name}
                    for group in groups]
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.error(f"Error in get_business_unit_groups: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse([], safe=False)

def get_business_units(request):
    business_unit_group_id = request.GET.get('business_unit_group_id')
    if business_unit_group_id:
        try:
            units = BusinessUnit.objects.filter(business_unit_group_id=business_unit_group_id)
            data = [{'business_unit_id': unit.business_unit_id, 'business_unit_name': unit.business_unit_name}
                    for unit in units]
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.error(f"Error in get_business_units: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse([], safe=False)

def get_branches(request):
    business_unit_id = request.GET.get('business_unit_id')
    if business_unit_id:
        try:
            branches = Branch.objects.filter(business_unit_id=business_unit_id)
            data = [{'branch_id': branch.branch_id, 'branch_name': branch.branch_name}
                    for branch in branches]
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.error(f"Error in get_branches: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse([], safe=False)

def login_view(request):
    if request.method == 'POST':
        if 'username' in request.POST and 'saas_user_password' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('saas_user_password')

            try:
                user = SAASUsers.objects.get(
                    saas_username=username,
                    saas_user_password=password  
                )
                request.session['temp_saas_user_id'] = user.saas_user_id
                request.session.modified = True  
                business_units = BusinessUnit.objects.filter(
                    business_unit_group__saas_customer=user.saas_customer
                ).distinct()
                if not business_units.exists():
                    messages.error(request, "No Business Units assigned to this user.")
                    logger.warning(f"No business units for user {username}")
                    return render(request, 'login.html')
                return render(request, 'login.html', {
                    'step': 'select_units',
                    'business_units': business_units
                })
            except SAASUsers.DoesNotExist:
                messages.error(request, "Invalid username or password.")
                logger.warning(f"Failed login attempt for username {username}")
                return render(request, 'login.html')

        elif 'business_unit' in request.POST:
            business_unit_id = request.POST.get('business_unit')
            branch_id = request.POST.get('branch')
            temp_user_id = request.session.get('temp_saas_user_id')

            if not temp_user_id:
                messages.error(request, "Session expired. Please log in again.")
                logger.warning("Temp user ID missing during business unit selection")
                return redirect('login')

            try:
                user = SAASUsers.objects.get(saas_user_id=temp_user_id)
                business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
                branch = Branch.objects.get(branch_id=branch_id)

                user_business_units = BusinessUnit.objects.filter(
                    business_unit_group__saas_customer=user.saas_customer
                )
                if (business_unit in user_business_units and
                    branch.business_unit == business_unit):
                    request.session['saas_user_id'] = user.saas_user_id
                    request.session['saas_customer_id'] = user.saas_customer.saas_customer_id
                    request.session['business_unit_group_id'] = business_unit.business_unit_group.business_unit_group_id
                    request.session['business_unit_id'] = business_unit.business_unit_id
                    request.session['branch_id'] = branch.branch_id
                    request.session.modified = True  
                    del request.session['temp_saas_user_id']
                    request.session.modified = True  
                    messages.success(request, "Login successful!")
                    return redirect('admin_view')
                else:
                    messages.error(request, "Invalid selection hierarchy.")
                    logger.warning(f"Invalid hierarchy: user {user.saas_username}, business_unit {business_unit_id}, branch {branch_id}")
            except (SAASUsers.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
                messages.error(request, f"Error processing selection: {str(e)}")
                logger.error(f"Login error: {str(e)}")

    return render(request, 'login.html')



@login_required
def home_view(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        product_groups = ProductGroup.objects.filter(business_unit=business_unit)
        products = Products.objects.filter(business_unit=business_unit)
        tables = Tables.objects.filter(business_unit=business_unit)
        rooms = Rooms.objects.filter(business_unit=business_unit)
        vehicles = Vehicle.objects.filter(business_unit=business_unit)
        customers = Customer.objects.filter(business_unit=business_unit)
        customer_form = CustomerForm()
  
        today = timezone.now().date()
        
      
        today_sales_count = SalesHeader.objects.filter(
            business_unit_id=business_unit_id,
            sale_date=today
        ).count()
        
        date_str = today.strftime('%Y%m%d')
        next_seq_num = str(today_sales_count + 1).zfill(3)
        next_sale_no = f"{date_str}{next_seq_num}"

        context = {
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'product_groups': product_groups,
            'products': products,
            'tables': tables,
            'rooms': rooms,
            'vehicles': vehicles,
            'customers': customers,
            'customer_form': customer_form,
            'next_sale_no': next_sale_no,
        }
        return render(request, 'home.html', context)
    except Exception as e:
        logger.error(f"Error in home_view: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')


@csrf_exempt
def check_stock(request, product_id):
    try:
        product = Products.objects.get(product_id=product_id)
        return JsonResponse({'flag_stock_out': product.flag_stock_out})
    except Products.DoesNotExist:
        logger.error(f"Product not found: {product_id}")
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in check_stock: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_products(request):
    group_id = request.GET.get('group_id')
    product_id = request.GET.get('product_id')
    business_unit_id = request.session.get('business_unit_id')

    try:
        products = Products.objects.filter(business_unit_id=business_unit_id)
        if group_id and group_id != 'all':
            products = products.filter(product_group_id=group_id)
        if product_id:
            products = products.filter(product_id=product_id)

        product_list = [{
            'product_id': p.product_id,
            'product_name': p.product_name,
            'sale_price': float(p.sale_price),
            'product_image': p.product_image.url if p.product_image else None,
            'flag_stock_out': p.flag_stock_out,
            'discount': float(p.discount),
            'tax': float(p.tax)
        } for p in products]

        return JsonResponse(product_list, safe=False)
    except Exception as e:
        logger.error(f"Error in get_products: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    

@login_required
def update_stock_view(request, product_id):
    if request.method == 'POST':
        try:
            product = Products.objects.get(product_id=product_id)
            new_status = request.POST.get('flag_stock_out')
            if new_status not in ['Y', 'N']:
                return JsonResponse({'success': False, 'error': 'Invalid stock status'}, status=400)
            
            product.flag_stock_out = new_status
            product.save()
            return JsonResponse({'success': True, 'flag_stock_out': new_status})
        except ObjectDoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
        except Exception as e:
            logger.error(f"Error updating stock for product {product_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@csrf_exempt
def complete_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            sale_data = {
                'subtotal': float(data['subtotal']),
                'total_discount': float(data['total_discount']),
                'total_tax': float(data['total_tax']),
                'grand_total': float(data['grand_total']),
                'payment_method': data['payment_method'],
                'customer_name': data['customer_name'],
                'timestamp': data['timestamp']
            }

            return JsonResponse({
                'success': True,
                'sale_id': 'SALE123',  
                'totals': sale_data
            })
        except Exception as e:
            logger.error(f"Error in complete_sale: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


logger = logging.getLogger(__name__)

def logout_view(request):
    try:
        logout(request)  
        messages.success(request, "You have been logged out successfully.")
    except Exception as e:
        logger.error(f"Error in logout_view: {str(e)}")
        messages.error(request, f"Error logging out: {str(e)}")
    return redirect('login')

@login_required
@require_POST
def add_customer(request):
    try:
        saas_user_id = request.session.get('saas_user_id')
        business_unit_id = request.session.get('business_unit_id')

        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)

        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.business_unit = business_unit
            customer.create_by = user.saas_username
            customer.save()
            messages.success(request, "Customer added successfully!")
        else:
            messages.error(request, "Failed to add customer. Please check the form fields.")
            logger.warning(f"Invalid customer form: {form.errors}")
    except Exception as e:
        logger.error(f"Error in add_customer: {str(e)}")
        messages.error(request, f"Error: {str(e)}")

    return redirect('home')


logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def expense_entry(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

  
    if not all([saas_user_id, saas_customer_id, business_unit_group_id, business_unit_id, branch_id]):
        logger.warning("Missing session data in expense_entry: %s", {
            'saas_user_id': saas_user_id,
            'saas_customer_id': saas_customer_id,
            'business_unit_group_id': business_unit_group_id,
            'business_unit_id': business_unit_id,
            'branch_id': branch_id
        })
        messages.error(request, "Incomplete session data. Please log in again.")
        return redirect('login')


    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

   
    expense_categories = Category.objects.filter(
        business_unit_id=business_unit_id,
        category_type='LEDGERTYPE'
    ).order_by('category_name')


    payment_accounts = ChartOfAccounts.objects.filter(
        business_unit=business_unit,
        account_type__iexact='Asset'
    ).order_by('account_name')

    logger.info(f"Found {expense_categories.count()} expense categories and {payment_accounts.count()} payment accounts for business unit {business_unit.business_unit_id}")

    if not payment_accounts.exists():
        logger.warning(f"No payment accounts found for business unit {business_unit.business_unit_id}")
        messages.warning(request, "No payment accounts available. Please contact the administrator to set up payment accounts.")

    context = {
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'expense_categories': expense_categories,
        'payment_accounts': payment_accounts,
    }

    if request.method == 'POST':
        try:
          
            with transaction.atomic():
                expense_category_id = request.POST.get('expense_category')
                payment_account_id = request.POST.get('payment_account')
                amount = request.POST.get('amount')
                expense_date = request.POST.get('expense_date')
                description = request.POST.get('description')
                reference = request.POST.get('reference', '')

                
                missing_fields = []
                if not expense_category_id:
                    missing_fields.append("expense category")
                if not payment_account_id:
                    missing_fields.append("payment account")
                if not amount:
                    missing_fields.append("amount")
                if not expense_date:
                    missing_fields.append("expense date")
                if not description:
                    missing_fields.append("description")
                if missing_fields:
                    logger.warning(f"Missing fields in expense_entry: {missing_fields}")
                    messages.error(request, f"Missing required fields: {', '.join(missing_fields)}.")
                    return render(request, 'ledger.html', context)

              
                try:
                    amount = Decimal(amount)
                    if amount <= 0:
                        messages.error(request, "Amount must be greater than zero.")
                        return render(request, 'ledger.html', context)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid amount format: {amount}")
                    messages.error(request, "Invalid amount format.")
                    return render(request, 'ledger.html', context)

              
                try:
                    expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Invalid expense date format: {expense_date}")
                    messages.error(request, "Invalid expense date format.")
                    return render(request, 'ledger.html', context)

                
                try:
                    expense_category = Category.objects.get(
                        category_id=expense_category_id,
                        business_unit_id=business_unit_id,
                        category_type='LEDGERTYPE'
                    )
                except Category.DoesNotExist:
                    logger.error(f"Invalid expense category: {expense_category_id}")
                    messages.error(request, "Selected expense category is invalid.")
                    return render(request, 'ledger.html', context)

                try:
                    payment_account = ChartOfAccounts.objects.get(
                        account_id=payment_account_id,
                        business_unit=business_unit,
                        account_type__iexact='Asset'
                    )
                except ChartOfAccounts.DoesNotExist:
                    logger.error(f"Invalid payment account: {payment_account_id}")
                    messages.error(request, "Selected payment account is invalid.")
                    return render(request, 'ledger.html', context)

           
                try:
                    default_expense_account = ChartOfAccounts.objects.get(
                        business_unit=business_unit,
                        account_type__in=['Expense', 'Operating Expense'],
                        account_name=expense_category.category_name
                    )
                except ChartOfAccounts.DoesNotExist:
                    logger.error(f"No matching expense account for category: {expense_category.category_name}")
                    messages.error(request, "No matching expense account for the selected category.")
                    return render(request, 'ledger.html', context)

          
                current_date = timezone.now().date()
                current_time = timezone.now()

                journal_entry = JournalEntries.objects.create(
                    business_unit=business_unit,
                    journal_entry_date=expense_date,
                    description=f"Expense: {description}",
                    reference=reference or f"EXP_{current_date.strftime('%Y%m%d')}",
                    create_dt=current_date,
                    create_tm=current_time,
                    create_by=user.saas_username,
                    create_remarks="Expense entry via POS",
                    update_dt=current_date,
                    update_tm=current_time,
                    update_by=user.saas_username,
                    update_marks="Initial expense entry"
                )

               
                JournalEntryLine.objects.create(
                    business_unit=business_unit,
                    journal_entry=journal_entry,
                    account=default_expense_account,
                    debit=amount,
                    credit=Decimal('0.00'),
                    create_dt=current_date,
                    create_tm=current_time,
                    create_by=user.saas_username,
                    create_remarks=f"Debit for expense: {description}",
                    update_dt=current_date,
                    update_tm=current_time,
                    update_by=user.saas_username,
                    update_marks="Initial entry"
                )

            
                JournalEntryLine.objects.create(
                    business_unit=business_unit,
                    journal_entry=journal_entry,
                    account=payment_account,
                    debit=Decimal('0.00'),
                    credit=amount,
                    create_dt=current_date,
                    create_tm=current_time,
                    create_by=user.saas_username,
                    create_remarks=f"Credit for payment: {description}",
                    update_dt=current_date,
                    update_tm=current_time,
                    update_by=user.saas_username,
                    update_marks="Initial entry"
                )

             
                default_expense_account.account_balance += amount
                default_expense_account.update_dt = current_date
                default_expense_account.update_tm = current_time
                default_expense_account.update_by = user.saas_username
                default_expense_account.update_marks = f"Expense recorded: {description}"
                default_expense_account.save(update_fields=['account_balance', 'update_dt', 'update_tm', 'update_by', 'update_marks'])

                payment_account.account_balance -= amount
                payment_account.update_dt = current_date
                payment_account.update_tm = current_time
                payment_account.update_by = user.saas_username
                payment_account.update_marks = f"Payment for expense: {description}"
                payment_account.save(update_fields=['account_balance', 'update_dt', 'update_tm', 'update_by', 'update_marks'])

                messages.success(request, f"Expense recorded successfully: {description}")
                return redirect('expense_list')

        except Exception as e:
            logger.error(f"Error in expense_entry POST: {str(e)}")
            messages.error(request, f"Error recording expense: {str(e)}")
           
            return render(request, 'ledger.html', context)

    return render(request, 'ledger.html', context)






@login_required
def get_sale_details(request):
    sale_id = request.GET.get('sale_id')
    if not sale_id:
        logger.warning("No sale_id provided in get_sale_details")
        return JsonResponse({'success': False, 'error': 'No sale_id provided'})

    try:
        sale = SalesHeader.objects.select_related('customer', 'business_unit', 'branch', 'table', 'room', 'vehicle')\
            .annotate(total_items=Count('salesline'))\
            .get(sale_id=sale_id)
        items = SalesLine.objects.filter(sale=sale).select_related('product')

        saas_customer_id = request.session.get('saas_customer_id')
        if saas_customer_id:
            saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
            saas_customer_name = saas_customer.saas_customer_name
        else:
            saas_customer_name = None

        
        paid_amount, balance, _ = calculate_payment_details(sale)

        sale_data = {
            'sale_no': sale.sale_no,
            'customer_name': sale.customer.customer_name if sale.customer else None,
            'sale_date': sale.sale_date.isoformat(),
            'total_amount': float(sale.total_amount),
            'discount_amount': float(sale.discount_amount),
            'tax_amount': float(sale.tax_amount),
            'business_unit_group_name': sale.business_unit.business_unit_group.business_unit_group_name if sale.business_unit and sale.business_unit.business_unit_group else None,
            'business_unit_name': sale.business_unit.business_unit_name if sale.business_unit else None,
            'branch_name': sale.branch.branch_name if sale.branch else None,
            'saas_customer_name': saas_customer_name,
            'total_items': sale.total_items,
            'paid_amount': float(paid_amount or 0),  
        }
        items_data = [
            {
                'product_name': item.product.product_name,
                'qty': item.qty,
                'total_amount': float(item.total_amount),
            } for item in items
        ]

        return JsonResponse({
            'success': True,
            'sale': sale_data,
            'items': items_data,
        })
    except SalesHeader.DoesNotExist:
        logger.error(f"Sale not found: {sale_id}")
        return JsonResponse({'success': False, 'error': 'Sale not found'})
    except SAASCustomer.DoesNotExist:
        logger.error(f"SAAS Customer not found for session saas_customer_id: {saas_customer_id}")
        return JsonResponse({'success': False, 'error': 'SAAS Customer not found in session'})
    except Exception as e:
        logger.error(f"Error in get_sale_details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
@login_required
@transaction.atomic
def save_sale(request):
    try:
        
        saas_user_id = request.session.get('saas_user_id')
        business_unit_id = request.session.get('business_unit_id')
        branch_id = request.session.get('branch_id')

        
        if not all([saas_user_id, business_unit_id, branch_id]):
            logger.warning("Missing session data: %s", {
                'saas_user_id': saas_user_id,
                'business_unit_id': business_unit_id,
                'branch_id': branch_id
            })
            return JsonResponse({'success': False, 'error': 'Incomplete session data. Please log in again.'})

        
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)

        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON data in request body")
            return JsonResponse({'success': False, 'error': 'Invalid request data format.'})

        items = data.get('items', [])
        customer_id = data.get('customer_id')
        table_id = data.get('table_id')
        room_id = data.get('room_id')
        vehicle_id = data.get('vehicle_id')

        
        if not items:
            logger.warning("No items provided for the sale")
            return JsonResponse({'success': False, 'error': 'No items provided for the sale.'})

        
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        
        customer = Customer.objects.get(customer_id=customer_id) if customer_id else None
        table = Tables.objects.get(table_id=table_id) if table_id else None
        room = Rooms.objects.get(room_id=room_id) if room_id else None
        vehicle = Vehicle.objects.get(vehicle_id=vehicle_id) if vehicle_id else None

        
        default_warehouse = Warehouse.objects.filter(branch=branch).first()
        if not default_warehouse:
            logger.error("No warehouse found for branch %s", branch.branch_id)
            return JsonResponse({'success': False, 'error': 'No warehouse found for this branch.'})

        
        beverage_groups = ['Water', 'Soft Drinks', 'Beverages', 'Canned Drinks', 'Bottled Water']

        
        for item in items:
            try:
                product = Products.objects.get(product_id=item['id'])
                is_beverage = False
                if product.product_group and product.product_group.product_name in beverage_groups:
                    is_beverage = True

                if is_beverage:
                    quantity = item.get('quantity', 0)
                    if not isinstance(quantity, (int, float)) or quantity <= 0:
                        logger.error("Invalid quantity for product %s: %s", product.product_id, quantity)
                        return JsonResponse({'success': False, 'error': f"Invalid quantity for product {product.product_name}."})
                    if product.stock < quantity:
                        logger.error("Insufficient stock for product %s. Available: %s, Requested: %s",
                                     product.product_name, product.stock, quantity)
                        return JsonResponse({
                            'success': False,
                            'error': f"Insufficient stock for product {product.product_name}. Available: {product.stock}, Requested: {quantity}"
                        })
            except Products.DoesNotExist:
                logger.error("Product not found: %s", item.get('id'))
                return JsonResponse({'success': False, 'error': f"Product ID {item.get('id')} not found."})
            except KeyError as e:
                logger.error("Missing required item field: %s", str(e))
                return JsonResponse({'success': False, 'error': f"Missing required field in item: {str(e)}."})


        total_amount = 0
        total_discount = 0
        total_tax = 0
        for item in items:
            price = item.get('price', 0)
            quantity = item.get('quantity', 0)
            discount = item.get('discount', 0)
            tax = item.get('tax', 0)

            if not all(isinstance(x, (int, float)) for x in [price, quantity, discount, tax]):
                logger.error("Invalid numeric values in item: %s", item)
                return JsonResponse({'success': False, 'error': 'Invalid numeric values in item data.'})

            base_price = price * quantity
            discount_amount = base_price * (discount / 100)
            taxable_amount = base_price - discount_amount
            tax_amount = taxable_amount * (tax / 100)

            total_amount += taxable_amount + tax_amount
            total_discount += discount_amount
            total_tax += tax_amount

        
        sale_header = SalesHeader.objects.create(
            business_unit=business_unit,
            branch=branch,
            customer=customer,
            table=table,
            room=room,
            vehicle=vehicle,
            total_amount=total_amount,
            discount_amount=total_discount,
            tax=total_tax,
            tax_amount=total_tax,
            payment_method='NONE',
            payment_status='Unpaid',
            sale_no=f"SALE-{SalesHeader.objects.count() + 1}",
            create_by=user.saas_username,
            create_remarks="Created from POS"
        )

        
        beverage_items = [
            item for item in items
            if Products.objects.get(product_id=item['id']).product_group and
               Products.objects.get(product_id=item['id']).product_group.product_name in beverage_groups
        ]

        inventory_header = None
        if beverage_items:
            
            net_value = sum(
                item['quantity'] * Products.objects.get(product_id=item['id']).unit_cost
                for item in beverage_items
            )
            inventory_header = InventoryHeader.objects.create(
                business_unit=business_unit,
                branch=branch,
                warehouse=default_warehouse,
                grnno='',  
                ref_type='SALES',
                ref_dt=timezone.now().date(),
                ref_no=sale_header.sale_no,
                net_value=-net_value, 
                create_by=user.saas_username,
                create_remarks=f"Created from sale {sale_header.sale_no}"
            )

        
        for item in items:
            product = Products.objects.get(product_id=item['id'])
            price = item['price']
            quantity = item['quantity']
            discount = item['discount']
            tax = item['tax']

            base_price = price * quantity
            discount_amount = base_price * (discount / 100)
            taxable_amount = base_price - discount_amount
            tax_amount = taxable_amount * (tax / 100)

            
            SalesLine.objects.create(
                sale=sale_header,
                business_unit=business_unit,
                branch=branch,
                customer=customer,
                product=product,
                qty=quantity,
                price=price,
                total_amount=taxable_amount + tax_amount,
                discount_amount=discount_amount,
                tax=tax,
                tax_amount=tax_amount,
                create_by=user.saas_username,
                create_remarks="Created from POS"
            )

            
            is_beverage = product.product_group and product.product_group.product_name in beverage_groups
            if is_beverage:
                
                product.stock -= quantity
                product.save()

                
                InventoryLine.objects.create(
                    business_unit=business_unit,
                    branch=branch,
                    warehouse=default_warehouse,
                    inventory=inventory_header,
                    product=product,
                    inventory_line_type='SALES',
                    qty=-quantity,  
                    price=price,
                    unit_cost=product.unit_cost,
                    uom=product.uom,
                    total_value=quantity * price,
                    total_cost=quantity * product.unit_cost,
                    create_by=user.saas_username,
                    create_remarks=f"Sales transaction for sale {sale_header.sale_no}"
                )

        logger.info("Sale created successfully: sale_id=%s", sale_header.sale_id)
        return JsonResponse({'success': True, 'sale_id': sale_header.sale_id})

    except SAASUsers.DoesNotExist:
        logger.error("User not found: saas_user_id=%s", saas_user_id)
        return JsonResponse({'success': False, 'error': 'User not found. Please log in again.'})
    except BusinessUnit.DoesNotExist:
        logger.error("Business unit not found: business_unit_id=%s", business_unit_id)
        return JsonResponse({'success': False, 'error': 'Business unit not found.'})
    except Branch.DoesNotExist:
        logger.error("Branch not found: branch_id=%s", branch_id)
        return JsonResponse({'success': False, 'error': 'Branch not found.'})
    except Customer.DoesNotExist:
        logger.error("Customer not found: customer_id=%s", customer_id)
        return JsonResponse({'success': False, 'error': 'Customer not found.'})
    except Exception as e:
        logger.error("Error in save_sale: %s", str(e), exc_info=True)
        return JsonResponse({'success': False, 'error': f"An error occurred: {str(e)}"})
    



logger = logging.getLogger(__name__)

def calculate_payment_details(sale):
    """Calculate paid_amount and balance for a sale."""
    try:
        paid_amount_query = JournalEntryLine.objects.filter(
            journal_entry__reference=sale.sale_no,
            journal_entry__business_unit=sale.business_unit,
            debit__gt=0
        ).select_related('journal_entry', 'account')

        paid_amount = paid_amount_query.aggregate(total_paid=Sum('debit'))['total_paid'] or Decimal('0.00')
        
        # Ensure paid_amount does not exceed total_amount
        paid_amount = min(paid_amount, sale.total_amount)
        balance = sale.total_amount - paid_amount
        
        if balance < 0:
            logger.warning(
                f"Negative balance detected for Sale {sale.sale_no}: "
                f"total_amount={sale.total_amount:.2f}, paid_amount={paid_amount:.2f}, balance={balance:.2f}"
            )
            balance = Decimal('0.00')
            paid_amount = sale.total_amount

        payment_details = [
            {
                'journal_entry_id': jel.journal_entry.journal_entry_id,
                'reference': jel.journal_entry.reference,
                'business_unit_id': jel.journal_entry.business_unit.business_unit_id,
                'debit': jel.debit,
                'credit': jel.credit,
                'account_type': jel.account.account_type,
                'account_name': jel.account.account_name,
                'create_remarks': jel.create_remarks
            } for jel in paid_amount_query
        ]

        all_entries = JournalEntryLine.objects.filter(
            journal_entry__reference=sale.sale_no,
            journal_entry__business_unit=sale.business_unit
        ).select_related('journal_entry', 'account')
        all_payment_details = [
            {
                'journal_entry_id': jel.journal_entry.journal_entry_id,
                'reference': jel.journal_entry.reference,
                'business_unit_id': jel.journal_entry.business_unit.business_unit_id,
                'debit': jel.debit,
                'credit': jel.credit,
                'account_type': jel.account.account_type,
                'account_name': jel.account.account_name,
                'create_remarks': jel.create_remarks
            } for jel in all_entries
        ]

        logger.debug(
            f"Calculate Payment - Sale {sale.sale_no}: "
            f"total_amount={sale.total_amount:.2f}, paid_amount={paid_amount:.2f}, "
            f"balance={balance:.2f}, payment_details={payment_details}, all_entries={all_payment_details}"
        )

        account_types = list(set(jel['account_type'] for jel in all_payment_details))
        logger.debug(f"Calculate Payment - Sale {sale.sale_no}: account_types={account_types}")

        return paid_amount, balance, payment_details
    except Exception as e:
        logger.error(f"Error calculating payment details for Sale {sale.sale_no}: {str(e)}")
        return Decimal('0.00'), sale.total_amount, []

@login_required
def process_payment(request):
    saas_user_id = request.session.get('saas_user_id')
    if not saas_user_id:
        logger.warning("No saas_user_id in process_payment")
        messages.error(request, "User not logged in.")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_username = user.saas_username
    except SAASUsers.DoesNotExist:
        logger.error(f"User not found: {saas_user_id}")
        messages.error(request, "User not found.")
        return redirect('login')

    sale_id = request.GET.get('sale_id')
    if not sale_id:
        logger.warning("Missing sale_id in process_payment")
        messages.error(request, "Missing sale_id.")
        return redirect('view_order')

    try:
        sale = SalesHeader.objects.get(sale_id=sale_id)
        total_amount = sale.total_amount
        business_unit_id = sale.business_unit.business_unit_id

        if sale.payment_status == 'Paid':
            logger.warning(f"Sale already paid: {sale_id}")
            messages.error(request, "This sale has already been paid.")
            return redirect('view_order')

        if not sale.business_unit:
            logger.error(f"No business unit for sale: {sale_id}")
            messages.error(request, "Sale has no associated business unit.")
            return redirect('view_order')

        paid_amount, balance, payment_details = calculate_payment_details(sale)

        logger.debug(
            f"Process Payment - Sale {sale.sale_no}: "
            f"total_amount={total_amount:.2f}, paid_amount={paid_amount:.2f}, "
            f"balance={balance:.2f}, business_unit_id={business_unit_id}, payment_details={payment_details}"
        )

        payment_accounts = Category.objects.filter(
            category_type='PAYMENT_TYPE',
            business_unit_id=business_unit_id
        ).values('category_id', 'category_name', 'category_value')

        if not payment_accounts:
            logger.warning(f"No payment accounts for business unit: {sale.business_unit}")
            messages.warning(request, "No payment methods available. Please contact the administrator.")
            return redirect('view_order')

        context = {
            'sale': sale,
            'total_amount': total_amount,
            'balance': balance,
            'paid_amount': paid_amount,
            'payment_accounts': payment_accounts,
            'username': saas_username,
        }
        logger.debug(
            f"Process Payment - Sale {sale.sale_no}: Context sent to payment.html: "
            f"total_amount={total_amount:.2f}, balance={balance:.2f}, paid_amount={paid_amount:.2f}, "
            f"sale_no={sale.sale_no}, payment_accounts={list(context['payment_accounts'])}"
        )
        return render(request, 'payment.html', context)
    except SalesHeader.DoesNotExist:
        logger.error(f"Sale not found: {sale_id}")
        messages.error(request, "Sale not found.")
        return redirect('view_order')
    except Exception as e:
        logger.error(f"Error in process_payment: {str(e)}")
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('view_order')

@login_required
@transaction.atomic
@require_POST
def confirm_payment(request):
    saas_user_id = request.session.get('saas_user_id')
    if not saas_user_id:
        logger.warning("No saas_user_id in confirm_payment")
        messages.error(request, "User not logged in.")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_username = user.saas_username
    except SAASUsers.DoesNotExist:
        logger.error(f"User not found: {saas_user_id}")
        messages.error(request, "User not found.")
        return redirect('login')

    sale_id = request.POST.get('sale_id')
    total_amount = request.POST.get('total_amount')
    net_amount = request.POST.get('net_amount')
    payment_method_id = request.POST.get('payment_method')
    card_no = request.POST.get('card_no', '')
    remarks = request.POST.get('remarks', '')

    logger.debug(
        f"Confirm Payment - Received POST data: sale_id={sale_id}, total_amount={total_amount}, "
        f"net_amount={net_amount}, payment_method_id={payment_method_id}, card_no='{card_no}', remarks='{remarks}'"
    )

    if not all([sale_id, total_amount, net_amount, payment_method_id]):
        missing = [field for field, value in [
            ('sale_id', sale_id), ('total_amount', total_amount),
            ('net_amount', net_amount), ('payment_method', payment_method_id)
        ] if not value]
        logger.warning(f"Missing fields in confirm_payment: {missing}")
        messages.error(request, f"Missing required fields: {', '.join(missing)}.")
        return redirect('process_payment')

    try:
        sale = SalesHeader.objects.get(sale_id=sale_id)
        total_amount = Decimal(total_amount)
        net_amount = Decimal(net_amount)

        paid_amount, current_balance, payment_details = calculate_payment_details(sale)

        logger.debug(
            f"Confirm Payment - Sale {sale.sale_no}: "
            f"total_amount={total_amount:.2f}, paid_amount={paid_amount:.2f}, "
            f"current_balance={current_balance:.2f}, net_amount={net_amount:.2f}, "
            f"business_unit_id={sale.business_unit.business_unit_id}, payment_details={payment_details}"
        )

        if net_amount <= 0:
            logger.warning(f"Invalid net_amount: {net_amount}")
            messages.error(request, "Payment amount must be greater than zero.")
            return redirect('process_payment')

        if net_amount > current_balance:
            logger.warning(f"Net amount {net_amount} exceeds balance {current_balance}")
            messages.error(request, "Payment amount cannot exceed remaining balance.")
            return redirect('process_payment')

        if sale.payment_status == 'Paid':
            logger.warning(f"Sale already paid: {sale_id}")
            messages.error(request, "This sale has already been paid.")
            return redirect('process_payment')

        if not sale.business_unit:
            logger.error(f"No business unit for sale: {sale_id}")
            messages.error(request, "Sale has no associated business unit.")
            return redirect('process_payment')

        def get_account(account_type, account_code, account_name):
            try:
                account = ChartOfAccounts.objects.get(
                    business_unit=sale.business_unit,
                    account_code=account_code
                )
                if account.account_type != account_type or account.account_name != account_name:
                    raise ValueError(
                        f"Account mismatch: '{account_code}' exists but has type='{account.account_type}' "
                        f"and name='{account.account_name}' (expected type='{account_type}', name='{account_name}')"
                    )
                return account
            except ChartOfAccounts.DoesNotExist:
                raise ValueError(f"Required account not found: {account_name} ({account_code}) for business unit {sale.business_unit}")

        try:
            payment_category = Category.objects.get(
                category_id=payment_method_id,
                category_type='PAYMENT_TYPE',
                business_unit_id=sale.business_unit.business_unit_id
            )
            account_name = payment_category.category_name.upper()
            payment_account = ChartOfAccounts.objects.get(
                account_name=account_name,
                business_unit=sale.business_unit
            )
        except Category.DoesNotExist:
            logger.error(f"Invalid payment method category: {payment_method_id}")
            messages.error(request, "Invalid payment method selected.")
            return redirect('process_payment')
        except ChartOfAccounts.DoesNotExist:
            logger.error(f"No ChartOfAccounts entry for payment method: {account_name}")
            messages.error(request, f"No account found for payment method: {account_name}.")
            return redirect('process_payment')

        sales_account = get_account('Revenue', 'REV_001', 'Sales Revenue')
        tax_account = get_account('Liability', 'LIAB_001', 'Tax Payable')

        current_date = timezone.now().date()
        current_time = timezone.now()

        new_paid_amount = paid_amount + net_amount
        payment_status = 'Paid' if new_paid_amount >= sale.total_amount else 'Partially Paid'

        tax_rate = Decimal('0.10')
        tax_amount = net_amount * tax_rate / (1 + tax_rate)
        revenue_amount = net_amount - tax_amount

        payment_remarks = f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment received for Sale No: {sale.sale_no}"
        update_marks = f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment of {net_amount:.2f} processed on {current_date}"
        if card_no or remarks:
            payment_remarks += f"; Card No: {card_no or 'N/A'}; Remarks: {remarks or 'None'}"
            update_marks += f"; Card No: {card_no or 'N/A'}; Remarks: {remarks or 'None'}"

        logger.debug(f"Confirm Payment - Sale {sale.sale_no}: payment_remarks='{payment_remarks}', update_marks='{update_marks}'")

        sale.payment_method = payment_category.category_name
        sale.payment_status = payment_status
        sale.update_dt = current_date
        sale.update_tm = current_time
        sale.update_by = saas_username
        sale.update_marks = update_marks
        sale.save(update_fields=['payment_method', 'payment_status', 'update_dt', 'update_tm', 'update_by', 'update_marks'])

        journal_entry = JournalEntries.objects.create(
            business_unit=sale.business_unit,
            journal_entry_date=current_date,
            description=f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment for Sale No: {sale.sale_no}",
            card_no=card_no or '',
            remarks=remarks or '',
            reference=sale.sale_no,
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=payment_remarks,
            update_dt=current_date,
            update_tm=current_time,
            update_by='',
            update_marks=''
        )

        payment_line = JournalEntryLine.objects.create(
            business_unit=sale.business_unit,
            journal_entry=journal_entry,
            account=payment_account,
            debit=net_amount,
            credit=Decimal('0.00'),
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=payment_remarks,
            update_dt=current_date,
            update_tm=current_time,
            update_by='',
            update_marks=''
        )

        JournalEntryLine.objects.create(
            business_unit=sale.business_unit,
            journal_entry=journal_entry,
            account=sales_account,
            debit=Decimal('0.00'),
            credit=revenue_amount,
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=f"Sales revenue for Sale No: {sale.sale_no}",
            update_dt=current_date,
            update_tm=current_time,
            update_by='',
            update_marks=''
        )

        JournalEntryLine.objects.create(
            business_unit=sale.business_unit,
            journal_entry=journal_entry,
            account=tax_account,
            debit=Decimal('0.00'),
            credit=tax_amount,
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=f"Tax payable for Sale No: {sale.sale_no}",
            update_dt=current_date,
            update_tm=current_time,
            update_by='',
            update_marks=''
        )

        for account, amount, remark in [
            (payment_account, net_amount, f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment of Sale No: {sale.sale_no}"),
            (sales_account, -revenue_amount, f"Revenue of Sale No: {sale.sale_no}"),
            (tax_account, -tax_amount, f"Tax payable of Sale No: {sale.sale_no}")
        ]:
            if amount != 0:
                account.account_balance += amount
                account.update_dt = current_date
                account.update_tm = current_time
                account.update_by = saas_username
                account.update_marks = f"Updated balance for {remark}"
                account.save(update_fields=['account_balance', 'update_dt', 'update_tm', 'update_by', 'update_marks'])

        saved_payment = JournalEntryLine.objects.filter(
            journal_entry__reference=sale.sale_no,
            journal_entry__business_unit=sale.business_unit,
            debit=net_amount,
            create_remarks=payment_remarks
        ).first()
        if saved_payment:
            logger.debug(
                f"Confirm Payment - Sale {sale.sale_no}: Payment saved successfully, "
                f"journal_entry_line_id={saved_payment.journal_entry_line_id}, create_remarks='{saved_payment.create_remarks}'"
            )
        else:
            logger.error(
                f"Confirm Payment - Sale {sale.sale_no}: Failed to verify saved payment for {net_amount:.2f}, "
                f"payment_remarks='{payment_remarks}'"
            )
            messages.error(request, f"Payment processing issue for Sale No: {sale.sale_no}. Please try again.")
            return redirect('process_payment')

        logger.debug(
            f"Confirm Payment - Sale {sale.sale_no}: Payment of {net_amount:.2f}, "
            f"new_paid_amount={new_paid_amount:.2f}, payment_status={payment_status}, "
            f"tax_amount={tax_amount:.2f}, revenue_amount={revenue_amount:.2f}"
        )

        messages.success(
            request,
            f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment of {net_amount:.2f} "
            f"for Sale No: {sale.sale_no} processed successfully."
        )
        return redirect('view_order')
    except SalesHeader.DoesNotExist:
        logger.error(f"Sale not found: {sale_id}")
        messages.error(request, "Sale not found.")
        return redirect('process_payment')
    except ValueError as e:
        logger.error(f"Account error in confirm_payment: {str(e)}")
        messages.error(request, f"Account error: {str(e)}")
        return redirect('process_payment')
    except Exception as e:
        logger.error(f"Error in confirm_payment: {str(e)}")
        messages.error(request, f"Error confirming payment: {str(e)}")
        return redirect('process_payment')

@login_required
def payment_view(request):
    saas_user_id = request.session.get('saas_user_id')
    if not saas_user_id:
        logger.warning("No saas_user_id in payment_view")
        messages.error(request, "User not logged in.")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_username = user.saas_username
        
        sale_id = request.GET.get('sale_id')
        if not sale_id:
            logger.warning("Missing sale_id in payment_view")
            messages.error(request, "Missing sale_id.")
            return redirect('home')

        sale = SalesHeader.objects.get(sale_id=sale_id)
        paid_amount, balance, payment_details = calculate_payment_details(sale)
        
        business_unit_id = sale.business_unit.business_unit_id
        payment_accounts = Category.objects.filter(
            category_type='PAYMENT_TYPE',
            business_unit_id=business_unit_id
        ).values('category_id', 'category_name', 'category_value')

        context = {
            'sale': sale,
            'sale_total': sale.total_amount,
            'sale_id': sale_id,
            'username': saas_username,
            'payment_accounts': payment_accounts,
            'paid_amount': paid_amount,
            'balance': balance,
        }
        logger.debug(
            f"Payment View - Sale {sale.sale_no}: "
            f"total_amount={sale.total_amount:.2f}, paid_amount={paid_amount:.2f}, "
            f"balance={balance:.2f}, payment_accounts={list(payment_accounts)}"
        )
        return render(request, 'payment.html', context)
    except SalesHeader.DoesNotExist:
        logger.error(f"Sale not found: {sale_id}")
        messages.error(request, "Sale not found.")
        return redirect('home')
    except SAASUsers.DoesNotExist:
        logger.error(f"User not found: {saas_user_id}")
        messages.error(request, "User not found.")
        return redirect('login')
    except Exception as e:
        logger.error(f"Error in payment_view: {str(e)}")
        messages.error(request, f"Error loading payment view: {str(e)}")
        return redirect('home')

@login_required
def view_order(request):
    business_unit_id = request.session.get('business_unit_id')
    if not business_unit_id:
        logger.warning("No business_unit_id in session")
        messages.error(request, "Business unit not found. Please log in again.")
        return redirect('home')

    try:
        today = timezone.now().date()

        unpaid_sales = SalesHeader.objects.filter(
            business_unit_id=business_unit_id,
            payment_status__in=['Unpaid', 'Partially Paid']
        ).filter(
            Q(payment_status='Unpaid', sale_date=today) |
            Q(payment_status='Partially Paid', update_dt=today)
        ).select_related('customer', 'business_unit', 'branch', 'table', 'room', 'vehicle')\
         .annotate(total_items=Count('salesline'))\
         .annotate(
            status_priority=Case(
                When(payment_status='Unpaid', then=Value(1)),
                When(payment_status='Partially Paid', then=Value(2)),
                output_field=IntegerField(),
            )
        ).order_by('-sale_no', 'status_priority', F('update_dt').desc(nulls_last=True), '-sale_date')

        sales_data = []
        for sale in unpaid_sales:
            paid_amount, balance, payment_details = calculate_payment_details(sale)
            sale.paid_amount = paid_amount
            sale.balance = balance

            logger.debug(
                f"View Order - Sale {sale.sale_no}: "
                f"total_amount={sale.total_amount:.2f}, paid_amount={paid_amount:.2f}, "
                f"balance={balance:.2f}, business_unit_id={sale.business_unit.business_unit_id}, "
                f"update_dt={sale.update_dt}, sale_date={sale.sale_date}, "
                f"update_marks={sale.update_marks}, payment_details={payment_details}"
            )

            sales_data.append({
                'sale_no': sale.sale_no,
                'total_amount': float(sale.total_amount),
                'paid_amount': float(sale.paid_amount),
                'balance': float(sale.balance),
                'payment_status': sale.payment_status,
                'update_dt': sale.update_dt,
                'sale_date': sale.sale_date
            })

        context = {
            'unpaid_sales': unpaid_sales,
        }
        logger.debug(
            f"View Order: Context sent to view_order.html: unpaid_sales={sales_data}"
        )
        return render(request, 'view_order.html', context)

    except Exception as e:
        logger.error(f"Error in view_order: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('home')

@login_required
def sale_inquiry(request):
    business_unit_id = request.session.get('business_unit_id')
    if not business_unit_id:
        logger.warning("No business_unit_id in session")
        messages.error(request, "Business unit not found. Please log in again.")
        return redirect('home')

    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        payment_status = request.GET.getlist('payment_status')

        unpaid_sales = SalesHeader.objects.filter(
            business_unit_id=business_unit_id,
            payment_status__in=['Unpaid', 'Partially Paid', 'Paid']
        ).select_related('customer', 'business_unit', 'branch', 'table', 'room', 'vehicle')\
         .annotate(total_items=Count('salesline'))\
         .annotate(
             sale_no_numeric=Cast(
                 Substr('sale_no', 6),
                 output_field=IntegerField()
             )
         ).order_by('-sale_no_numeric')

        if payment_status:
            unpaid_sales = unpaid_sales.filter(payment_status__in=payment_status)

        if start_date:
            start_date = parse_date(start_date)
            if start_date:
                unpaid_sales = unpaid_sales.filter(
                    Q(payment_status='Partially Paid', update_dt__gte=start_date) |
                    Q(payment_status__in=['Unpaid', 'Paid'], sale_date__gte=start_date)
                )
        if end_date:
            end_date = parse_date(end_date)
            if end_date:
                unpaid_sales = unpaid_sales.filter(
                    Q(payment_status='Partially Paid', update_dt__lte=end_date) |
                    Q(payment_status__in=['Unpaid', 'Paid'], sale_date__lte=end_date)
                )

        sales_data = []
        for sale in unpaid_sales:
            paid_amount, balance, payment_details = calculate_payment_details(sale)
            sale.paid_amount = paid_amount
            sale.balance = balance

            logger.debug(
                f"Sale Inquiry - Sale {sale.sale_no}: "
                f"total_amount={sale.total_amount:.2f}, paid_amount={paid_amount:.2f}, "
                f"balance={balance:.2f}, business_unit_id={sale.business_unit.business_unit_id}, "
                f"update_dt={sale.update_dt}, update_marks={sale.update_marks}, "
                f"payment_details={payment_details}"
            )

            sales_data.append({
                'sale_no': sale.sale_no,
                'total_amount': float(sale.total_amount),
                'paid_amount': float(sale.paid_amount),
                'balance': float(sale.balance),
                'payment_status': sale.payment_status,
                'update_dt': sale.update_dt
            })

        context = {
            'unpaid_sales': unpaid_sales,
            'start_date': start_date,
            'end_date': end_date,
            'payment_status': payment_status,
        }
        logger.debug(
            f"Sale Inquiry: Context sent to sale_inquiry.html: "
            f"unpaid_sales={sales_data}, payment_status={payment_status}"
        )

        return render(request, 'sale_inquiry.html', context)

    except Exception as e:
        logger.error(f"Error in sale_inquiry: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('home')

@login_required
def sale_detail(request, sale_id):
    try:
        sale = SalesHeader.objects.select_related(
            'customer', 'business_unit', 'branch', 'table', 'room', 'vehicle'
        ).get(sale_id=sale_id, business_unit_id=request.session.get('business_unit_id'))

        sale_lines = SalesLine.objects.select_related('product').filter(sale_id=sale_id)

        paid_amount, balance, payment_details = calculate_payment_details(sale)
        sale.paid_amount = paid_amount
        sale.balance = balance

        context = {
            'sale': sale,
            'sale_lines': sale_lines,
        }

        logger.debug(
            f"Sale Detail - Sale {sale.sale_no}: "
            f"total_amount={sale.total_amount:.2f}, paid_amount={paid_amount:.2f}, "
            f"balance={balance:.2f}, items_count={sale_lines.count()}"
        )

        return render(request, 'sale_detail.html', context)

    except SalesHeader.DoesNotExist:
        logger.error(f"Sale with ID {sale_id} not found or unauthorized access.")
        messages.error(request, "Sale not found or you do not have access.")
        return redirect('sale_inquiry')
    except Exception as e:
        logger.error(f"Error in sale_detail: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('sale_inquiry')
        
@login_required
def customer_bills(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        sales = SalesHeader.objects.filter(
            business_unit_id=business_unit_id
        ).select_related('customer').order_by('customer__customer_id', 'sale_no')

        bills_data = []
        for sale in sales:
            paid_amount, balance, payment_details = calculate_payment_details(sale)
            bills_data.append({
                'customer_id': sale.customer.customer_id,
                'customer_name': sale.customer.customer_name,
                'sale_no': sale.sale_no,
                'total_amount': float(sale.total_amount),
                'paid_amount': float(paid_amount),
                'balance': float(balance),
            })

        context = {
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'bills': bills_data,
        }
        logger.debug(f"Customer Bills: Context sent to customer_bills.html: bills={bills_data}, username={user.saas_username}, business_unit={business_unit}")
        return render(request, 'customer_bills.html', context)
    except Exception as e:
        logger.error(f"Error in customer_bills: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')

@login_required
def customer_summary(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        sales = SalesHeader.objects.filter(
            business_unit_id=business_unit_id
        ).select_related('customer').values(
            'customer__customer_id',
            'customer__customer_name'
        ).annotate(
            total_amount=Sum('total_amount')
        )

        summary_data = []
        for customer in sales:
            customer_sales = SalesHeader.objects.filter(
                business_unit_id=business_unit_id,
                customer__customer_id=customer['customer__customer_id']
            )
            total_paid = Decimal('0.000')
            for sale in customer_sales:
                paid_amount, _, _ = calculate_payment_details(sale)
                total_paid += paid_amount
            total_balance = customer['total_amount'] - total_paid
            summary_data.append({
                'customer_id': customer['customer__customer_id'],
                'customer_name': customer['customer__customer_name'],
                'total_amount': float(customer['total_amount']),
                'paid_amount': float(total_paid),
                'balance': float(total_balance),
            })

        context = {
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'summary': summary_data,
        }
        logger.debug(f"Customer Summary: Context sent to customer_summary.html: summary={summary_data}, username={user.saas_username}, business_unit={business_unit}")
        return render(request, 'customer_summary.html', context)
    except Exception as e:
        logger.error(f"Error in customer_summary: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')





@login_required
def expense_list(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    if not all([saas_user_id, saas_customer_id, business_unit_group_id, business_unit_id, branch_id]):
        logger.warning("Missing session data in expense_list: %s", {
            'saas_user_id': saas_user_id,
            'saas_customer_id': saas_customer_id,
            'business_unit_group_id': business_unit_group_id,
            'business_unit_id': business_unit_id,
            'branch_id': branch_id
        })
        messages.error(request, "Incomplete session data. Please log in again.")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

    
    expenses = JournalEntries.objects.filter(
        business_unit=business_unit,
        description__startswith="Expense:"
    ).order_by('-journal_entry_date')

    context = {
        'username': user.saas_username,
        'business_unit': business_unit,
        'expenses': expenses,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'branch': branch,

    }

    return render(request, 'expense_list.html', context)



def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        required_keys = [
            'saas_user_id',
            'saas_customer_id',
            'business_unit_group_id',
            'business_unit_id',
            'branch_id'
        ]
        missing_keys = [key for key in required_keys if key not in request.session]
        
        if missing_keys:
            logger.warning(f"Access denied to {view_func.__name__}. Missing session keys: {missing_keys}")
            messages.error(request, f"Please log in and select a business unit and branch. Missing: {', '.join(missing_keys)}")
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def general_ledger_report(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Session data not found in general_ledger_report: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

    start_date_str = request.GET.get('start_date', '2025-01-01')
    end_date_str = request.GET.get('end_date', '2025-04-01')

    logger.info(f"general_ledger_report: Received date parameters: start_date={start_date_str}, end_date={end_date_str}")

    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Date parameters cannot be empty")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
    except ValueError as e:
        logger.warning(f"general_ledger_report: Invalid date format or range: {str(e)}, start_date={start_date_str}, end_date={end_date_str}")
        messages.error(request, f"Invalid date format or range: {str(e)}. Using default dates (2025-01-01 to 2025-04-01).")
        start_date = datetime(2025, 1, 1).date()
        end_date = datetime(2025, 4, 1).date()

    try:
        entries = JournalEntries.objects.filter(
            business_unit=business_unit,
            journal_entry_date__range=[start_date, end_date]
        ).select_related('business_unit').prefetch_related(
            'journalentryline_set__account'
        ).order_by('journal_entry_date', 'journal_entry_id')

        logger.info(f"general_ledger_report: Retrieved {entries.count()} journal entries for business_unit {business_unit.business_unit_id} "
                    f"from {start_date} to {end_date}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'entries': entries,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'general_ledger_report.html', context)
    except Exception as e:
        logger.error(f"general_ledger_report: Error generating report: {str(e)}")
        messages.error(request, f"Error generating report: {str(e)}")
        return render(request, 'general_ledger_report.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'entries': [],
        })



logger = logging.getLogger(__name__)

@login_required
def trial_balance_report(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"trial_balance_report: Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

    
    start_date_str = request.GET.get('start_date', '2025-01-01')
    end_date_str = request.GET.get('end_date', '2025-04-01')
    logger.info(f"trial_balance_report: Received start_date: {start_date_str}, end_date: {end_date_str}")

    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Start date and end date cannot be empty")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
    except ValueError as e:
        logger.warning(f"trial_balance_report: Invalid date format or range: {str(e)}, start_date={start_date_str}, end_date={end_date_str}")
        messages.error(request, f"Invalid date format or range: {str(e)}. Using default dates (2025-01-01 to 2025-04-01).")
        start_date = datetime(2025, 1, 1).date()
        end_date = datetime(2025, 4, 1).date()

    try:
        accounts = ChartOfAccounts.objects.filter(
            business_unit=business_unit
        ).annotate(
            total_debits=Sum(
                'journalentryline__debit',
                filter=Q(journalentryline__journal_entry__journal_entry_date__gte=start_date) &
                       Q(journalentryline__journal_entry__journal_entry_date__lte=end_date)
            ),
            total_credits=Sum(
                'journalentryline__credit',
                filter=Q(journalentryline__journal_entry__journal_entry_date__gte=start_date) &
                       Q(journalentryline__journal_entry__journal_entry_date__lte=end_date)
            ),
            balance=Case(
                When(account_type__in=['Asset', 'Expense'], then=Sum('journalentryline__debit') - Sum('journalentryline__credit')),
                default=Sum('journalentryline__credit') - Sum('journalentryline__debit'),
                output_field=DecimalField(),
                filter=Q(journalentryline__journal_entry__journal_entry_date__gte=start_date) &
                       Q(journalentryline__journal_entry__journal_entry_date__lte=end_date)
            )
        ).filter(Q(total_debits__gt=0) | Q(total_credits__gt=0)).order_by('account_code')

        logger.info(f"trial_balance_report: Retrieved {accounts.count()} accounts for business_unit {business_unit.business_unit_id} from {start_date} to {end_date}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'accounts': accounts,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'trial_balance_report.html', context)
    except Exception as e:
        logger.error(f"trial_balance_report: Error generating report: {str(e)}")
        messages.error(request, f"Error generating report: {str(e)}")
        return render(request, 'trial_balance_report.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'accounts': [],
        })




logger = logging.getLogger(__name__)

@login_required
def balance_sheet(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"balance_sheet: Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

   
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    
    date_filter = {}
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            date_filter['update_dt__gte'] = start_date
        except ValueError:
            messages.error(request, "Invalid start date format. Please use YYYY-MM-DD.")
            start_date = None
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            date_filter['update_dt__lte'] = end_date
        except ValueError:
            messages.error(request, "Invalid end date format. Please use YYYY-MM-DD.")
            end_date = None

    try:
        required_fields = ['account_name', 'account_balance', 'account_type', 'business_unit', 
                          'account_code', 'create_by', 'create_remarks', 'update_dt', 'update_tm', 
                          'update_by', 'update_marks']
        from django.apps import apps
        chart_model = apps.get_model('pos', 'ChartOfAccounts')  
        missing_fields = [field for field in required_fields if not hasattr(chart_model, field)]
        if missing_fields:
            raise ValueError(f"Missing required fields in ChartOfAccounts model: {missing_fields}")

       
        assets = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Asset',
            account_balance__isnull=False,
            **date_filter
        ).exclude(account_balance=0).values('account_name', 'account_balance')

        liabilities = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Liability',
            account_balance__isnull=False,
            **date_filter
        ).exclude(account_balance=0).values('account_name', 'account_balance')

        total_assets = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Asset',
            account_balance__isnull=False,
            **date_filter
        ).aggregate(total=Sum('account_balance'))['total'] or Decimal('0.00')

        total_liabilities = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Liability',
            account_balance__isnull=False,
            **date_filter
        ).aggregate(total=Sum('account_balance'))['total'] or Decimal('0.00')

        if any(asset['account_balance'] < 0 for asset in assets):
            logger.warning(f"balance_sheet: Negative balances found in Asset accounts for {business_unit.business_unit_id}")
        if any(liability['account_balance'] < 0 for liability in liabilities):
            logger.warning(f"balance_sheet: Negative balances found in Liability accounts for {business_unit.business_unit_id}")

        total_equity = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Equity',
            account_balance__isnull=False,
            **date_filter
        ).aggregate(total=Sum('account_balance'))['total'] or Decimal('0.00')

        required_equity = total_assets - total_liabilities

        with transaction.atomic():
            if abs(required_equity - total_equity) > Decimal('0.01'):
                logger.warning(f"Equity imbalance: Expected {required_equity}, Found {total_equity}")
                adjustment = required_equity - total_equity
                current_date = datetime.now().date()
                equity_account, created = ChartOfAccounts.objects.get_or_create(
                    business_unit=business_unit,
                    account_type='Equity',
                    account_name='Equity Adjustment',
                    defaults={
                        'account_code': 'EQ-ADJ',
                        'account_balance': adjustment,
                        'create_by': user.saas_username,
                        'create_remarks': 'Auto-created for balance sheet equity adjustment'
                    }
                )
                if not created:
                    equity_account.account_balance += adjustment
                    equity_account.account_code = 'EQ-ADJ'
                    equity_account.update_dt = current_date
                    equity_account.update_tm = current_date
                    equity_account.update_by = user.saas_username
                    equity_account.update_marks = 'Adjusted for balance sheet equity'
                    equity_account.save()
                    equity_account.refresh_from_db()
                    logger.info(f"Equity Adjustment account balance after update: {equity_account.account_balance}")
                logger.info(f"Adjusted equity by {adjustment} for {business_unit.business_unit_id}")

            total_equity = ChartOfAccounts.objects.filter(
                business_unit=business_unit,
                account_type__iexact='Equity',
                account_balance__isnull=False,
                **date_filter
            ).aggregate(total=Sum('account_balance'))['total'] or Decimal('0.00')

            equity = ChartOfAccounts.objects.filter(
                business_unit=business_unit,
                account_type__iexact='Equity',
                account_balance__isnull=False,
                **date_filter
            ).exclude(account_balance=0).values('account_name', 'account_balance')

            total_liabilities_equity = total_liabilities + total_equity

            imbalance = abs(total_assets - total_liabilities_equity)
            if imbalance > Decimal('0.01'):
                logger.error(f"balance_sheet: Accounting equation imbalance persists after adjustment for {business_unit.business_unit_id}: "
                             f"Assets={total_assets}, Liabilities+Equity={total_liabilities_equity}, Imbalance={imbalance}")
                messages.warning(request, f"Warning: Balance sheet is unbalanced by {imbalance:.2f}. Please check account data.")
            else:
                logger.info(f"balance_sheet: Accounting equation balanced for {business_unit.business_unit_id}")

        logger.info(f"balance_sheet: {business_unit.business_unit_id} => "
                    f"Assets={total_assets} ({len(assets)} accounts), "
                    f"Liabilities={total_liabilities} ({len(liabilities)} accounts), "
                    f"Equity={total_equity} ({len(equity)} accounts), "
                    f"Liabilities+Equity={total_liabilities_equity}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities_equity,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
            'start_date': start_date,
            'end_date': end_date,
        }
        return render(request, 'balance_sheet.html', context)
    except Exception as e:
        logger.error(f"balance_sheet: Error generating balance sheet: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, "Error generating balance sheet. Please try again.")
        return render(request, 'balance_sheet.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'assets': [],
            'liabilities': [],
            'equity': [],
            'total_assets': Decimal('0.00'),
            'total_liabilities': Decimal('0.00'),
            'total_equity': Decimal('0.00'),
            'total_liabilities_equity': Decimal('0.00'),
            'start_date': None,
            'end_date': None,
        })



logger = logging.getLogger(__name__)

@login_required
def income_statement(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"income_statement: Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

   
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
   
    date_filter = {}
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            date_filter['update_dt__gte'] = start_date
        except ValueError:
            messages.error(request, "Invalid start date format. Please use YYYY-MM-DD.")
            start_date = None
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            date_filter['update_dt__lte'] = end_date
        except ValueError:
            messages.error(request, "Invalid end date format. Please use YYYY-MM-DD.")
            end_date = None

    try:
        required_fields = ['account_name', 'account_balance', 'account_type', 'business_unit', 
                          'account_code', 'create_by', 'create_remarks', 'update_dt', 'update_tm', 
                          'update_by', 'update_marks']
        from django.apps import apps
        chart_model = apps.get_model('pos', 'ChartOfAccounts') 
        missing_fields = [field for field in required_fields if not hasattr(chart_model, field)]
        if missing_fields:
            raise ValueError(f"Missing required fields in ChartOfAccounts model: {missing_fields}")

        revenue = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Revenue',
            account_balance__isnull=False,
            **date_filter
        ).exclude(account_balance=0).values('account_name', 'account_balance')

        expenses = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Expense',
            account_balance__isnull=False,
            **date_filter
        ).exclude(account_balance=0).values('account_name', 'account_balance')

        total_revenue = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Revenue',
            account_balance__isnull=False,
            **date_filter
        ).aggregate(total=Sum('account_balance'))['total'] or Decimal('0.00')

        total_expenses = ChartOfAccounts.objects.filter(
            business_unit=business_unit,
            account_type__iexact='Expense',
            account_balance__isnull=False,
            **date_filter
        ).aggregate(total=Sum('account_balance'))['total'] or Decimal('0.00')

        net_income = total_revenue - total_expenses

        with transaction.atomic():
            if abs(net_income) > Decimal('0.01'):
                current_date = datetime.now().date()
                retained_earnings, created = ChartOfAccounts.objects.get_or_create(
                    business_unit=business_unit,
                    account_type='Equity',
                    account_name='Retained Earnings',
                    defaults={
                        'account_code': 'RETAINED-EARN',
                        'account_balance': net_income,
                        'create_by': user.saas_username,
                        'create_remarks': 'Auto-created for net income transfer',
                        'update_by': '',  
                        'update_marks': ''  
                    }
                )
                if not created:
                    retained_earnings.account_balance += net_income
                    retained_earnings.update_dt = current_date
                    retained_earnings.update_tm = current_date
                    retained_earnings.save()
                    retained_earnings.refresh_from_db()
                    logger.info(f"Retained Earnings balance after update: {retained_earnings.account_balance}, "
                                f"update_by='{retained_earnings.update_by}', "
                                f"update_marks='{retained_earnings.update_marks}'")
                logger.info(f"Transferred net income {net_income} to Retained Earnings for {business_unit.business_unit_id}")

        logger.info(f"income_statement: Generated for business_unit {business_unit.business_unit_id}: "
                    f"Revenue={total_revenue} ({len(revenue)} accounts), "
                    f"Expenses={total_expenses} ({len(expenses)} accounts), "
                    f"Net Income={net_income}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'revenue': revenue,
            'expenses': expenses,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
            'start_date': start_date,
            'end_date': end_date,
        }
        return render(request, 'income_statement.html', context)
    except Exception as e:
        logger.error(f"income_statement: Error generating income statement: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, "An error occurred while generating the income statement. Please try again.")
        return render(request, 'income_statement.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'revenue': [],
            'expenses': [],
            'total_revenue': Decimal('0.00'),
            'total_expenses': Decimal('0.00'),
            'net_income': Decimal('0.00'),
            'start_date': None,
            'end_date': None,
        })





@login_required
def sales_by_customer_report(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"sales_by_customer_report: Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

    start_date_str = request.GET.get('start_date', '2025-01-01')
    end_date_str = request.GET.get('end_date', '2025-04-01')

    logger.info(f"sales_by_customer_report: Received date parameters: start_date={start_date_str}, end_date={end_date_str}")

    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Date parameters cannot be empty")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
    except ValueError as e:
        logger.warning(f"sales_by_customer_report: Invalid date format or range: {str(e)}, start_date={start_date_str}, end_date={end_date_str}")
        messages.error(request, f"Invalid date format or range: {str(e)}. Using default dates (2025-01-01 to 2025-04-01).")
        start_date = datetime(2025, 1, 1).date()
        end_date = datetime(2025, 4, 1).date()

    try:
        sales = Customer.objects.filter(
            business_unit=business_unit
        ).annotate(
            number_of_orders=Count('salesheader', filter=Q(salesheader__sale_date__range=[start_date, end_date])),
            total_sales=Sum('salesheader__total_amount', filter=Q(salesheader__sale_date__range=[start_date, end_date])),
            outstanding_balance=Sum(
                'salesheader__total_amount',
                filter=Q(salesheader__sale_date__range=[start_date, end_date], salesheader__payment_status='Unpaid')
            )
        ).values('customer_name', 'number_of_orders', 'total_sales', 'outstanding_balance').order_by('-total_sales')

        logger.info(f"sales_by_customer_report: Retrieved {sales.count()} customer sales records for business_unit {business_unit.business_unit_id} "
                    f"from {start_date} to {end_date}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'sales': sales,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'sales_by_customer_report.html', context)
    except Exception as e:
        logger.error(f"sales_by_customer_report: Error generating report: {str(e)}")
        messages.error(request, f"Error generating report: {str(e)}")
        return render(request, 'sales_by_customer_report.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'sales': [],
        })
    




@login_required
def product_sales_report(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"product_sales_report: Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

    start_date_str = request.GET.get('start_date', '2025-01-01')
    end_date_str = request.GET.get('end_date', '2025-04-01')

    logger.info(f"product_sales_report: Received date parameters: start_date={start_date_str}, end_date={end_date_str}")

    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Date parameters cannot be empty")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
    except ValueError as e:
        logger.warning(f"product_sales_report: Invalid date format or range: {str(e)}, start_date={start_date_str}, end_date={end_date_str}")
        messages.error(request, f"Invalid date format or range: {str(e)}. Using default dates (2025-01-01 to 2025-04-01).")
        start_date = datetime(2025, 1, 1).date()
        end_date = datetime(2025, 4, 1).date()

    try:
        sales = Products.objects.filter(
            business_unit=business_unit,
            salesline__sale__sale_date__range=[start_date, end_date]
        ).annotate(
            total_quantity_sold=Sum('salesline__qty'),
            total_revenue=Sum(
                ExpressionWrapper(
                    F('salesline__qty') * F('salesline__price'),
                    output_field=DecimalField(max_digits=22, decimal_places=3)
                )
            ),
            average_price=Avg('salesline__price')
        ).values(
            'product_id',
            'product_name',
            'total_quantity_sold',
            'total_revenue',
            'average_price'
        ).order_by('-total_revenue')

        logger.info(f"product_sales_report: Retrieved {sales.count()} product sales records for business_unit {business_unit.business_unit_id} "
                    f"from {start_date} to {end_date}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'sales': sales,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'product_sales_report.html', context)
    except Exception as e:
        logger.error(f"product_sales_report: Error generating report: {str(e)}")
        messages.error(request, f"Error generating report: {str(e)}")
        return render(request, 'product_sales_report.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'sales': [],
        })



logger = logging.getLogger(__name__)

@login_required
def purchase_by_supplier_report(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    logger.info(f"Session data: saas_user_id={saas_user_id}, saas_customer_id={saas_customer_id}, "
                f"business_unit_group_id={business_unit_group_id}, business_unit_id={business_unit_id}, branch_id={branch_id}")

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"purchase_by_supplier_report: Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')

  
    start_date_str = request.GET.get('start_date', '2025-01-01')
    end_date_str = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))

    logger.info(f"purchase_by_supplier_report: Received date parameters: start_date={start_date_str}, end_date={end_date_str}")

    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Date parameters cannot be empty")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
    except ValueError as e:
        logger.warning(f"purchase_by_supplier_report: Invalid date format or range: {str(e)}, start_date={start_date_str}, end_date={end_date_str}")
        messages.error(request, f"Invalid date format or range: {str(e)}. Using default dates (2025-01-01 to today).")
        start_date = datetime(2025, 1, 1).date()
        end_date = date.today()

    try:
      
        suppliers = Suppliers.objects.filter(
            business_unit=business_unit
        ).annotate(
            number_of_pos=Count(
                'purchaseorders',
                filter=Q(purchaseorders__order_date__range=[start_date, end_date]) & 
                       ~Q(purchaseorders__order_date='1900-01-01'),
                distinct=True
            ),
            total_purchases=Coalesce(
                Sum(
                    'purchaseorders__total_amount',
                    filter=Q(purchaseorders__order_date__range=[start_date, end_date]) & 
                           ~Q(purchaseorders__order_date='1900-01-01')
                ),
                0,
                output_field=DecimalField()
            )
        ).values(
            'supplier_name',
            'supplier_type',
            'phone_1',
            'phone_2',
            'email',
            'address',
            'create_dt',
            'create_by',
            'create_remarks',
            'number_of_pos',
            'total_purchases'
        )

        
        purchases = []
        total_pos = 0
        total_purchases_sum = Decimal('0.00')
        total_paid_sum = Decimal('0.00')
        total_balance_sum = Decimal('0.00')

        for supplier in suppliers:
            supplier_data = supplier.copy()
            
            pos = PurchaseOrders.objects.filter(
                supplier__supplier_name=supplier['supplier_name'],
                business_unit=business_unit,
                order_date__range=[start_date, end_date]
            ).exclude(order_date='1900-01-01')

            
            total_paid = Decimal('0.00')
            total_balance = Decimal('0.00')
            for po in pos:
                paid_amount, balance, _ = calculate_payment_detailss(po)
                total_paid += paid_amount
                total_balance += balance

            supplier_data['total_paid'] = total_paid
            supplier_data['total_balance'] = total_balance
            purchases.append(supplier_data)

           
            total_pos += supplier['number_of_pos']
            total_purchases_sum += supplier['total_purchases']
            total_paid_sum += total_paid
            total_balance_sum += total_balance

            logger.info(f"Supplier: {supplier['supplier_name']}, Type: {supplier['supplier_type']}, "
                        f"Phone 1: {supplier['phone_1']}, Phone 2: {supplier['phone_2']}, "
                        f"Email: {supplier['email']}, Address: {supplier['address']}, "
                        f"Create Date: {supplier['create_dt']}, Create By: {supplier['create_by']}, "
                        f"Create Remarks: {supplier['create_remarks']}, "
                        f"Number of POs: {supplier['number_of_pos']}, "
                        f"Total Purchases: {supplier['total_purchases']}, "
                        f"Total Paid: {total_paid}, Total Balance: {total_balance}")

        logger.info(f"Total POs: {total_pos}, Total Purchases Sum: {total_purchases_sum}, "
                    f"Total Paid Sum: {total_paid_sum}, Total Balance Sum: {total_balance_sum}")

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'purchases': purchases,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
            'report_title': 'Purchase by Supplier Report',
            'total_purchases_sum': total_purchases_sum,
            'total_pos': total_pos,
            'total_paid_sum': total_paid_sum,
            'total_balance_sum': total_balance_sum
        }
        return render(request, 'purchase_by_supplier_report.html', context)
    except Exception as e:
        logger.error(f"purchase_by_supplier_report: Error generating report: {str(e)}")
        messages.error(request, f"Error generating report: {str(e)}")
        return render(request, 'purchase_by_supplier_report.html', {
            'username': user.saas_username,
            'business_unit': business_unit,
            'start_date': start_date,
            'end_date': end_date,
            'purchases': [],
            'report_title': 'Purchase Report',
            'total_purchases_sum': 0,
            'total_pos': 0,
            'total_paid_sum': 0,
            'total_balance_sum': 0
        })

logger = logging.getLogger(__name__)



@login_required
def inventory_valuation_report(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        beverage_groups = ['Water', 'Soft Drinks', 'Beverages', 'Canned Drinks', 'Bottled Water']

        inventory_data = InventoryLine.objects.filter(
            business_unit=business_unit,
            branch=branch,
            inventory__warehouse__isnull=False,
            product__product_group__product_name__in=beverage_groups
        ).select_related(
            'product',
            'inventory',
            'business_unit',
            'branch',
            'warehouse'
        ).values(
            'product__sku',
            'product__product_name',
            'product__unit_cost'
        ).annotate(
            stock_in_qty=Sum('qty', filter=Q(inventory_line_type='Stock In'), default=0),
            stock_out_qty=Sum(
                Case(
                    When(inventory_line_type='SALES', then=F('qty') * -1),  
                    When(inventory_line_type='Stock Out', then=F('qty')),
                    default=0,
                    output_field=FloatField()
                ),
                default=0
            ),
            total_qty=ExpressionWrapper(
                F('stock_in_qty') - F('stock_out_qty'),
                output_field=DecimalField()
            ),
            inventory_value=Sum(F('qty') * F('product__unit_cost'), default=0),
            line_total_value=Sum('total_value', default=0)
        ).order_by('-inventory_value')

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'inventory_data': inventory_data,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'inventory_valuation_report.html', context)

    except Exception as e:
        logger.error(f"Error in inventory_valuation_report: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')


    


@login_required
def po_creation(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        products = Products.objects.filter(business_unit=business_unit)

        if request.method == 'POST':
            form = PurchaseOrderForm(request.POST)
            formset = PurchaseOrderItemFormSet(request.POST, form_kwargs={'products': products})

            if form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():
                        
                        pono = form.cleaned_data.get('pono')
                        if PurchaseOrders.objects.filter(pono=pono).exists():
                            messages.error(request, f"Purchase Order number {pono} already exists. Please use a different number.")
                            return render(request, 'po_creation.html', {
                                'form': form,
                                'formset': formset,
                                'username': user.saas_username,
                                'saas_customer': saas_customer,
                                'business_unit_group': business_unit_group,
                                'business_unit': business_unit,
                                'branch': branch,
                                'suppliers': Suppliers.objects.filter(business_unit=business_unit),
                                'product_groups': ProductGroup.objects.filter(business_unit=business_unit),
                                'tables': Tables.objects.filter(business_unit=business_unit),
                                'rooms': Rooms.objects.filter(business_unit=business_unit),
                                'vehicles': Vehicle.objects.filter(business_unit=business_unit),
                                'customers': Customer.objects.filter(business_unit=business_unit),
                            })

                        
                        purchase_order = form.save(commit=False)
                        purchase_order.business_unit = business_unit
                        purchase_order.branch = branch
                        purchase_order.createby = user.saas_username
                        
            
                        purchase_order.postatus = 'New'
                        purchase_order.sub_total = 0
                        purchase_order.discount_amount = 0
                        
                        if not purchase_order.remarks:
                            purchase_order.remarks = f"Created by {user.saas_username} on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        purchase_order.createremarks = f"Created by {user.saas_username} on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        purchase_order.save()

                        
                        sub_total = 0
                        grn_no = f"GRN-{purchase_order.pono}"
                        
                        for item_form in formset:
                            if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                                item = item_form.save(commit=False)
                                item.poid = purchase_order
                                item.business_unit = business_unit
                                item.branch = branch
                                item.createby = user.saas_username
                                item.discount_percent = 0
                                item.remarks = f"Item ordered by {user.saas_username} on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                
                                quantity = item.quantity
                                unit_price = item.unit_price
                                tax_rate = item.tax_rate
                                line_total_before_tax = quantity * unit_price
                                line_tax_amount = line_total_before_tax * (tax_rate / 100) if tax_rate else 0
                                item.line_total = line_total_before_tax + line_tax_amount
                                
                                item.createremarks = f"Created by {user.saas_username} on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                item.save()
                                sub_total += line_total_before_tax
                        
                        
                        purchase_order.sub_total = sub_total
                        purchase_order.total_amount = sub_total + purchase_order.tax_amount - purchase_order.discount_amount
                        purchase_order.save()
                        
                        
                        try:
                            warehouse = Warehouse.objects.filter(business_unit=business_unit, branch=branch).first()
                            if not warehouse:
                                raise Exception("No warehouse found for this business unit and branch")
                            
                            inventory_header = InventoryHeader(
                                business_unit=business_unit,
                                branch=branch,
                                warehouse=warehouse,
                                grnno=grn_no,
                                ref_type='PO',
                                ref_dt=timezone.now().date(),
                                ref_no=str(purchase_order.pono),
                                net_value=purchase_order.total_amount,
                                create_by=user.saas_username,
                                create_remarks=f"Created from PO {purchase_order.pono} by {user.saas_username}"
                            )
                            inventory_header.save()
                            
                            po_items = PurchaseOrderItems.objects.filter(poid=purchase_order)
                            for item in po_items:
                                inventory_line = InventoryLine(
                                    business_unit=business_unit,
                                    branch=branch,
                                    warehouse=warehouse,
                                    inventory=inventory_header,
                                    product=item.product,
                                    inventory_line_type='purchase',
                                    qty=item.quantity,
                                    price=item.unit_price,
                                    unit_cost=item.unit_price,
                                    uom='EA',
                                    total_value=item.line_total,
                                    total_cost=item.line_total,
                                    create_by=user.saas_username,
                                    create_remarks=f"Created from PO {purchase_order.pono} by {user.saas_username}"
                                )
                                inventory_line.save()
                        except Exception as e:
                            logger.error(f"Error creating inventory records: {str(e)}")

                    messages.success(request, "Purchase Order created successfully.")
                    return redirect('po_inquiry')

                except IntegrityError:
                    messages.error(request, "This PO number already exists. Please use a different number.")
                    return render(request, 'po_creation.html', {
                        'form': form,
                        'formset': formset,
                        'username': user.saas_username,
                        'saas_customer': saas_customer,
                        'business_unit_group': business_unit_group,
                        'business_unit': business_unit,
                        'branch': branch,
                        'suppliers': Suppliers.objects.filter(business_unit=business_unit),
                        'product_groups': ProductGroup.objects.filter(business_unit=business_unit),
                        'tables': Tables.objects.filter(business_unit=business_unit),
                        'rooms': Rooms.objects.filter(business_unit=business_unit),
                        'vehicles': Vehicle.objects.filter(business_unit=business_unit),
                        'customers': Customer.objects.filter(business_unit=business_unit),
                    })

        else:
            form = PurchaseOrderForm()
            formset = PurchaseOrderItemFormSet(queryset=PurchaseOrderItems.objects.none(), form_kwargs={'products': products})

        context = {
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'form': form,
            'formset': formset,
            'suppliers': Suppliers.objects.filter(business_unit=business_unit),
            'product_groups': ProductGroup.objects.filter(business_unit=business_unit),
            'tables': Tables.objects.filter(business_unit=business_unit),
            'rooms': Rooms.objects.filter(business_unit=business_unit),
            'vehicles': Vehicle.objects.filter(business_unit=business_unit),
            'customers': Customer.objects.filter(business_unit=business_unit),
        }
        return render(request, 'po_creation.html', context)

    except Exception as e:
        logger.error(f"Error in po_creation: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')






logger = logging.getLogger(__name__)

@login_required
def stock_adjustment(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        try:
            warehouse = Warehouse.objects.get(branch=branch)
        except Warehouse.DoesNotExist:
            logger.error(f"No warehouse found for branch {branch_id}")
            messages.error(request, "No warehouse configured for this branch.")
            return redirect('inventory:stock_adjustment')

        products = Products.objects.filter(business_unit=business_unit)

        if request.method == 'POST':
            form = StockAdjustmentForm(
                request.POST,
                products=products,
                business_unit_id=business_unit_id  
            )
            if form.is_valid():
                product = form.cleaned_data['product']
                ref_type = form.cleaned_data['ref_type']
                ref_no = form.cleaned_data['ref_no']
                quantity = form.cleaned_data['quantity']
                unit_price = form.cleaned_data['unit_price']
                remarks = form.cleaned_data['remarks'] or "Stock adjustment"

                adjustment_type = "Stock In" if quantity >= 0 else "Stock Out"

                inventory_header = InventoryHeader.objects.create(
                    business_unit=business_unit,
                    branch=branch,
                    warehouse=warehouse,
                    grnno="",
                    ref_type=ref_type,
                    ref_dt=date.today(),
                    ref_no=ref_no or f"ADJ-{product.product_id}",
                    net_value=abs(quantity * unit_price),
                    create_by=user.saas_username,
                    create_remarks=remarks,
                    update_dt=date(1900, 1, 1),
                    update_tm=date(1900, 1, 1),
                    update_by="",
                    update_marks=""
                )

                InventoryLine.objects.create(
                    business_unit=business_unit,
                    branch=branch,
                    warehouse=warehouse,
                    inventory=inventory_header,
                    product=product,
                    inventory_line_type=adjustment_type,
                    qty=abs(quantity),
                    price=unit_price,
                    unit_cost=unit_price,
                    uom=getattr(product, 'uom', "Unit"),
                    total_value=abs(quantity * unit_price),
                    total_cost=abs(quantity * unit_price),
                    create_by=user.saas_username,
                    create_remarks=remarks,
                    update_dt=date(1900, 1, 1),
                    update_tm=date(1900, 1, 1),
                    update_by="",
                    update_marks=""
                )

                messages.success(request, "Stock adjustment recorded successfully.")
                return redirect('stock_adjustment')
            else:
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = StockAdjustmentForm(
                products=products,
                business_unit_id=business_unit_id  
            )

        context = {
            'form': form,
            'username': user.saas_username,
            'business_unit': business_unit,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'stock_adjustment.html', context)

    except Exception as e:
        logger.error(f"Error in stock_adjustment: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')


logger = logging.getLogger(__name__)

@login_required
def stock_return(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        try:
            warehouse = Warehouse.objects.get(branch=branch)
        except Warehouse.DoesNotExist:
            logger.error(f"No warehouse found for branch {branch_id}")
            messages.error(request, "No warehouse configured for this branch.")
            return redirect('stock_return')

        products = Products.objects.filter(business_unit=business_unit)

        if request.method == 'POST':
            form = StockAdjustmentForm(
                request.POST,
                products=products,
                business_unit_id=business_unit_id,
                category_type='STOCK_RETURN_TYPE'
            )
            if form.is_valid():
                product = form.cleaned_data['product']
                ref_type = form.cleaned_data['ref_type']
                ref_no = form.cleaned_data['ref_no']
                quantity = form.cleaned_data['quantity']
                unit_price = form.cleaned_data['unit_price']
                remarks = form.cleaned_data['remarks'] or "Stock return"

              
                quantity = -quantity
                remarks = f"Return of adjustment (Ref: {ref_no or 'RET-' + str(product.product_id)})" if not remarks else remarks
                adjustment_type = "Stock In" if quantity >= 0 else "Stock Out"

                inventory_header = InventoryHeader.objects.create(
                    business_unit=business_unit,
                    branch=branch,
                    warehouse=warehouse,
                    grnno="",
                    ref_type=ref_type,
                    ref_dt=date.today(),
                    ref_no=ref_no or f"RET-{product.product_id}",
                    net_value=abs(quantity * unit_price),
                    create_by=user.saas_username,
                    create_remarks=remarks,
                    update_dt=date(1900, 1, 1),
                    update_tm=date(1900, 1, 1),
                    update_by="",
                    update_marks=""
                )

                InventoryLine.objects.create(
                    business_unit=business_unit,
                    branch=branch,
                    warehouse=warehouse,
                    inventory=inventory_header,
                    product=product,
                    inventory_line_type=adjustment_type,
                    qty=abs(quantity),
                    price=unit_price,
                    unit_cost=unit_price,
                    uom=getattr(product, 'uom', "Unit"),
                    total_value=abs(quantity * unit_price),
                    total_cost=abs(quantity * unit_price),
                    create_by=user.saas_username,
                    create_remarks=remarks,
                    update_dt=date(1900, 1, 1),
                    update_tm=date(1900, 1, 1),
                    update_by="",
                    update_marks=""
                )

                messages.success(request, "Stock return recorded successfully.")
                return redirect('stock_return')
            else:
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = StockAdjustmentForm(
                products=products,
                business_unit_id=business_unit_id,
                category_type='STOCK_RETURN_TYPE'
            )

        context = {
            'form': form,
            'username': user.saas_username,
            'business_unit': business_unit,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'stock_return.html', context)

    except Exception as e:
        logger.error(f"Error in stock_return: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')
    





@login_required
def stock_report(request, product_id='1001'):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

    
        products = Products.objects.filter(business_unit=business_unit)
        if request.method == 'POST':
            form = StockReportForm(request.POST, products=products)
            if form.is_valid():
                product_id = form.cleaned_data['product'].product_id
                return redirect('stock_report', product_id=product_id)
        else:
            form = StockReportForm(products=products, initial_product_id=product_id)

        
        try:
            product = Products.objects.get(product_id=product_id, business_unit=business_unit)
        except Products.DoesNotExist:
            messages.error(request, f"No product found with ID {product_id} for this business unit.")
            context = {
                'form': form,
                'username': user.saas_username,
                'business_unit': business_unit,
                'saas_customer': saas_customer,
                'business_unit_group': business_unit_group,
                'branch': branch,
            }
            return render(request, 'stock_report.html', context)

    
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        current_month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        last_month_end = current_month_start - timedelta(days=1)
        last_6m_start = last_month_end - timedelta(days=180)

        
        sales_data = SalesLine.objects.filter(
            business_unit=business_unit,
            product=product
        ).aggregate(
            total_sold_qty=Sum('qty'),
            cm_sale_qty=Sum('qty', filter=Q(sale_date__range=[current_month_start, current_month_end])),
            last_6m_sale_qty=Sum('qty', filter=Q(sale_date__range=[last_6m_start, last_month_end]))
        )

        
        total_sold_qty = float(sales_data['total_sold_qty'] or 0)
        cm_sale_qty = float(sales_data['cm_sale_qty'] or 0)
        last_6m_sale_qty = float(sales_data['last_6m_sale_qty'] or 0)

    
        mad_6m = last_6m_sale_qty / 6.0 if last_6m_sale_qty else 0
        stock_month = float(product.stock) / mad_6m if mad_6m > 0 else 0
        excess_stock_qty = float(product.stock) - mad_6m if mad_6m > 0 else 0

    
        po_data = PurchaseOrderItems.objects.filter(
            business_unit=business_unit,
            product=product,
            poid__order_date__isnull=False
        ).aggregate(
            total_po_qty=Sum('quantity'),
            cm_po_qty=Sum('quantity', filter=Q(poid__order_date__range=[current_month_start, current_month_end])),
            last_6m_po_qty=Sum('quantity', filter=Q(poid__order_date__range=[last_6m_start, last_month_end]))
        )

    
        total_po_qty = float(po_data['total_po_qty'] or 0)
        cm_po_qty = float(po_data['cm_po_qty'] or 0)
        last_6m_po_qty = float(po_data['last_6m_po_qty'] or 0)

        
        report_data = {
            'product_id': product.product_id,
            'product_name': product.product_name,
            'product_price': product.product_price,
            'sale_price': product.sale_price,
            'unit_cost': product.unit_cost,
            'uom': product.uom,
            'stock': product.stock,
            'total_sold_qty': total_sold_qty,
            'cm_sale_qty': cm_sale_qty,
            'last_6m_sale_qty': last_6m_sale_qty,
            'mad_6m': mad_6m,
            'stock_month': stock_month,
            'excess_stock_qty': excess_stock_qty,
            'total_po_qty': total_po_qty,
            'cm_po_qty': cm_po_qty,
            'last_6m_po_qty': last_6m_po_qty,
        }

        context = {
            'form': form,
            'report': report_data,
            'username': user.saas_username,
            'business_unit': business_unit,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }

        return render(request, 'stock_report.html', context)

    except Exception as e:
        logger.error(f"Error in stock_report: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')





logger = logging.getLogger(__name__)

@login_required
def stock_report_list(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        
        date_filter = {}
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                date_filter['inventory__ref_dt__gte'] = start_date
            except ValueError:
                messages.error(request, "Invalid start date format. Please use YYYY-MM-DD.")
                start_date = None
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                date_filter['inventory__ref_dt__lte'] = end_date
            except ValueError:
                messages.error(request, "Invalid end date format. Please use YYYY-MM-DD.")
                end_date = None

        products = Products.objects.filter(business_unit=business_unit)
        report_data_list = []

        
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        import calendar
        year, month = current_month_start.year, current_month_start.month
        last_day_of_month = calendar.monthrange(year, month)[1]
        current_month_end = current_month_start.replace(day=last_day_of_month)
        last_month_end = current_month_start - timedelta(days=1)
        last_6m_start = last_month_end - timedelta(days=180)

        for product in products:
            
            sales_filter = {'business_unit': business_unit, 'product': product}
            if start_date:
                sales_filter['sale_date__gte'] = start_date
            if end_date:
                sales_filter['sale_date__lte'] = end_date

            sales_data = SalesLine.objects.filter(**sales_filter).aggregate(
                total_sold_qty=Sum('qty'),
                cm_sale_qty=Sum('qty', filter=Q(sale_date__range=[current_month_start, current_month_end])),
                last_6m_sale_qty=Sum('qty', filter=Q(sale_date__range=[last_6m_start, last_month_end]))
            )

            total_sold_qty = float(sales_data['total_sold_qty'] or 0)
            cm_sale_qty = float(sales_data['cm_sale_qty'] or 0)
            last_6m_sale_qty = float(sales_data['last_6m_sale_qty'] or 0)

          
            po_filter = {'business_unit': business_unit, 'product': product, 'poid__order_date__isnull': False}
            if start_date:
                po_filter['poid__order_date__gte'] = start_date
            if end_date:
                po_filter['poid__order_date__lte'] = end_date

            po_data = PurchaseOrderItems.objects.filter(**po_filter).aggregate(
                total_po_qty=Sum('quantity'),
                cm_po_qty=Sum('quantity', filter=Q(poid__order_date__range=[current_month_start, current_month_end])),
                last_6m_po_qty=Sum('quantity', filter=Q(poid__order_date__range=[last_6m_start, last_month_end]))
            )

            total_po_qty = float(po_data['total_po_qty'] or 0)
            cm_po_qty = float(po_data['cm_po_qty'] or 0)
            last_6m_po_qty = float(po_data['last_6m_po_qty'] or 0)

          
            adjustment_filter = {'business_unit': business_unit, 'product': product, **date_filter}
            adjustment_data = InventoryLine.objects.filter(**adjustment_filter).aggregate(
                stock_in_qty=Sum('qty', filter=Q(inventory_line_type='Stock In')),
                stock_out_qty=Sum('qty', filter=Q(inventory_line_type='Stock Out'))
            )

            stock_in_qty = float(adjustment_data['stock_in_qty'] or 0)
            stock_out_qty = float(adjustment_data['stock_out_qty'] or 0)
            net_adjustment_qty = stock_in_qty - stock_out_qty 

            
            initial_stock = float(getattr(product, 'initial_stock', 0))  
            calculated_stock = initial_stock + total_po_qty - total_sold_qty + net_adjustment_qty
            calculated_stock = max(calculated_stock, 0)  

            
            mad_6m = last_6m_sale_qty / 6.0 if last_6m_sale_qty else 0
            stock_month = calculated_stock / mad_6m if mad_6m > 0 else 0
            excess_stock_qty = calculated_stock - mad_6m if mad_6m > 0 else 0

            report_data_list.append({
                'product_id': product.product_id,
                'product_name': product.product_name,
                'product_price': float(product.product_price or 0),
                'sale_price': float(product.sale_price or 0),
                'unit_cost': float(product.unit_cost or 0),
                'uom': product.uom or 'N/A',
                'stock': round(calculated_stock, 2),
                'total_sold_qty': total_sold_qty,
                'cm_sale_qty': cm_sale_qty,
                'last_6m_sale_qty': last_6m_sale_qty,
                'mad_6m': round(mad_6m, 2),
                'stock_month': round(stock_month, 2),
                'excess_stock_qty': round(excess_stock_qty, 2),
                'total_po_qty': total_po_qty,
                'cm_po_qty': cm_po_qty,
                'last_6m_po_qty': last_6m_po_qty,
                'return_stock_qty': round(stock_out_qty, 2),  
            })

        context = {
            'reports': report_data_list,
            'username': user.saas_username,
            'business_unit': business_unit,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
            'start_date': start_date,
            'end_date': end_date,
        }

        return render(request, 'stock_report_list.html', context)

    except Exception as e:
        logger.error(f"Error in stock_report: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')


@login_required
def admin_view(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        products_count = Products.objects.filter(business_unit=business_unit).count()
        customers_count = Customer.objects.filter(business_unit=business_unit).count()
        supplier_count = Suppliers.objects.filter(business_unit=business_unit).count()

        context = {
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'products_count': products_count,
            'customers_count': customers_count,
            'supplier_count': supplier_count,
            'app_label': 'pos',
        }
        return render(request, 'admin.html', context)
    except Exception as e:
        logger.error(f"Error in admin_view: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')








@login_required
def productgroup_add(request):
    business_unit_id = request.session.get('business_unit_id')
    saas_user_id = request.session.get('saas_user_id')  

    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        saas_user = SAASUsers.objects.get(saas_user_id=saas_user_id)  
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    except SAASUsers.DoesNotExist:
        messages.error(request, "Invalid user session.")
        return redirect('login')

    if request.method == 'POST':
        form = ProductGroupForm(request.POST, request.FILES)
        if form.is_valid():
            product_group = form.save(commit=False)
            product_group.business_unit = business_unit
            product_group.create_by = saas_user.saas_username[:10]  
            product_group.create_remarks = f"Created by {saas_user.saas_username} for product {form.cleaned_data['product_name']}"[:200]  
            product_group.save()
            messages.success(request, "Product Group added successfully.")
            return redirect('productgroup_list')
    else:
        form = ProductGroupForm()

    return render(request, 'productgroup_add.html', {'form': form})



@login_required
def productgroup_edit(request, pk):
    business_unit_id = request.session.get('business_unit_id')
    saas_user_id = request.session.get('saas_user_id')  

    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        saas_user = SAASUsers.objects.get(saas_user_id=saas_user_id)  
        product_group = get_object_or_404(ProductGroup, pk=pk, business_unit__business_unit_id=business_unit_id)
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    except SAASUsers.DoesNotExist:
        messages.error(request, "Invalid user session.")
        return redirect('login')

    if request.method == 'POST':
        form = EditProductGroupForm(request.POST, request.FILES, instance=product_group)
        if form.is_valid():
            product_group = form.save(commit=False)

            changed_fields = []
            for field in form.changed_data:
                if field == 'product_name':
                    changed_fields.append('Product Name')
                elif field == 'product_image':
                    changed_fields.append('Product Image')

            
            if 'clear_image' in request.POST and product_group.product_image:
                product_group.product_image.delete()
                product_group.product_image = None
                changed_fields.append('Product Image (cleared)')

            product_group.update_dt = date.today()
            product_group.update_tm = timezone.now()  
            product_group.update_by = saas_user.saas_username[:10]  
            product_group.update_marks = f"Updated: {', '.join(changed_fields)}" if changed_fields else "No fields changed"

            product_group.business_unit = business_unit
            product_group.save()
            messages.success(request, "Product Group updated successfully.")
            return redirect('productgroup_list')
    else:
        form = EditProductGroupForm(instance=product_group)

    return render(request, 'productgroup_edit.html', {'form': form, 'product_group': product_group})







@login_required
def productgroup_list(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        product_groups = ProductGroup.objects.filter(business_unit=business_unit).order_by('-create_dt')
        paginator = Paginator(product_groups, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'productgroup_list.html', {'page_obj': page_obj})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')

@login_required
def productgroup_delete(request, pk):
    business_unit_id = request.session.get('business_unit_id')
    try:
        product_group = get_object_or_404(ProductGroup, pk=pk, business_unit__business_unit_id=business_unit_id)
        if request.method == 'POST':
            product_group.delete()
            messages.success(request, "Product Group deleted successfully.")
            return redirect('productgroup_list')
        return render(request, 'productgroup_confirm_delete.html', {'object': product_group})
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('productgroup_list')

@login_required
def productgroup_inquiry(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        product_groups = ProductGroup.objects.filter(business_unit=business_unit)
        return render(request, 'productgroup_inquiry.html', {'product_groups': product_groups})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')

@login_required
def productgroup_dashboard(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        product_group_count = ProductGroup.objects.filter(business_unit=business_unit).count()
        return render(request, 'productgroup_dashboard.html', {'product_group_count': product_group_count})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')







@login_required
def product_add(request):
    business_unit_id = request.session.get('business_unit_id')
    saas_user_id = request.session.get('saas_user_id')

    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        saas_user = SAASUsers.objects.get(saas_user_id=saas_user_id)
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    except SAASUsers.DoesNotExist:
        messages.error(request, "Invalid user session.")
        return redirect('login')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, business_unit=business_unit)
        if form.is_valid():
            product = form.save(commit=False)
            product.business_unit = business_unit
            product.create_by = saas_user.saas_username  
    
            current_date = timezone.now().strftime('%Y-%m-%d')
            product.create_remarks = f"Product created by {saas_user.saas_username} on {current_date}"
        
            product.update_dt = '1900-01-01'  
            product.update_tm = '1900-01-01'  
            product.update_by = ''  
            product.update_marks = ''  
            product.save()
            messages.success(request, "Product added successfully.")
            return redirect('product_list')
    else:
        form = ProductForm(business_unit=business_unit)
    return render(request, 'product_add.html', {'form': form})







@login_required
def product_edit(request, pk):
    business_unit_id = request.session.get('business_unit_id')
    saas_user_id = request.session.get('saas_user_id')

    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        saas_user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        product = get_object_or_404(Products, pk=pk, business_unit__business_unit_id=business_unit_id)
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    except SAASUsers.DoesNotExist:
        messages.error(request, "Invalid user session.")
        return redirect('login')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, business_unit=business_unit)
        if form.is_valid():
            product = form.save(commit=False)

            changed_fields = []
            field_display_names = {
                'product_group': 'Product Group',
                'category': 'Category',
                'product_name': 'Product Name',
                'product_image': 'Product Image',
                'product_price': 'Product Price',
                'sale_price': 'Sale Price',
                'unit_cost': 'Unit Cost',
                'discount': 'Discount',
                'tax': 'Tax',
                'stock': 'Stock',
                'flag_stock_out': 'Stock Out Flag',
                'uom': 'Unit of Measure',
                'sku': 'SKU',
                'inv_class': 'Inventory Class',
            }
            for field in form.changed_data:
                changed_fields.append(field_display_names.get(field, field))

            
            if 'clear_image' in request.POST and product.product_image:
                product.product_image.delete(save=False)
                product.product_image = None
                changed_fields.append('Product Image (cleared)')

    
            product.update_dt = date.today()
            product.update_tm = timezone.now()  
            product.update_by = saas_user.saas_username[:10]  
            product.update_marks = (
                f"Updated on {date.today().strftime('%Y-%m-%d')} by {saas_user.saas_username[:10]}. "
                f"Fields changed: {', '.join(changed_fields)}" if changed_fields
                else f"Form submitted on {date.today().strftime('%Y-%m-%d')} by {saas_user.saas_username[:10]} with no field changes"
            )[:200]  

            product.business_unit = business_unit
            product.save()
            messages.success(request, "Product updated successfully.")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product, business_unit=business_unit)

    return render(request, 'product_edit.html', {'form': form, 'product': product})



@login_required
def product_list(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        products = Products.objects.filter(business_unit=business_unit).order_by('-create_dt')
        paginator = Paginator(products, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'product_list.html', {'page_obj': page_obj})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')

@login_required
def product_delete(request, pk):
    business_unit_id = request.session.get('business_unit_id')
    try:
        product = get_object_or_404(Products, pk=pk, business_unit__business_unit_id=business_unit_id)
        if request.method == 'POST':
            product.delete()
            messages.success(request, "Product deleted successfully.")
            return redirect('product_list')
        return render(request, 'product_confirm_delete.html', {'object': product})
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('product_list')

@login_required
def product_inquiry(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        products = Products.objects.filter(business_unit=business_unit)
        return render(request, 'product_inquiry.html', {'products': products})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')

@login_required
def product_dashboard(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        product_count = Products.objects.filter(business_unit=business_unit).count()
        return render(request, 'product_dashboard.html', {'product_count': product_count})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')




@login_required
def supplier_add(request):
    business_unit_id = request.session.get('business_unit_id')
    saas_user_id = request.session.get('saas_user_id')

    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        saas_user = SAASUsers.objects.get(saas_user_id=saas_user_id)
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    except SAASUsers.DoesNotExist:
        messages.error(request, "Invalid user session.")
        return redirect('login')

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.business_unit = business_unit
            supplier.create_by = saas_user.saas_username[:10]
            supplier.create_remarks = f"Created by {saas_user.saas_username} for supplier {form.cleaned_data['supplier_name']}"[:200]
            supplier.save()
            messages.success(request, "Supplier added successfully.")
            return redirect('supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'supplier_add.html', {'form': form})



@login_required
def supplier_edit(request, pk):
    business_unit_id = request.session.get('business_unit_id')
    saas_user_id = request.session.get('saas_user_id')

    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        saas_user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        supplier = get_object_or_404(Suppliers, pk=pk, business_unit__business_unit_id=business_unit_id)
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    except SAASUsers.DoesNotExist:
        messages.error(request, "Invalid user session.")
        return redirect('login')

    if request.method == 'POST':
        form = EditSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save(commit=False)
            changed_fields = [field for field in form.changed_data]
            field_names = {
                'supplier_type': 'Supplier Type',
                'supplier_name': 'Supplier Name',
                'phone_1': 'Primary Phone',
                'phone_2': 'Secondary Phone',
                'email': 'Email',
                'address': 'Address'
            }
            changed_labels = [field_names.get(field, field) for field in changed_fields]
            supplier.update_dt = date.today()
            supplier.update_tm = timezone.now()
            supplier.update_by = saas_user.saas_username[:10]
            supplier.update_marks = f"Updated: {', '.join(changed_labels)}" if changed_labels else "No fields changed"
            supplier.business_unit = business_unit
            supplier.save()
            messages.success(request, "Supplier updated successfully.")
            return redirect('supplier_list')
    else:
        form = EditSupplierForm(instance=supplier)

    return render(request, 'supplier_edit.html', {'form': form, 'supplier': supplier})

@login_required
def supplier_list(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        suppliers = Suppliers.objects.filter(business_unit=business_unit).order_by('-create_dt')
        paginator = Paginator(suppliers, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'supplier_list.html', {'page_obj': page_obj})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')

@login_required
def supplier_delete(request, pk):
    business_unit_id = request.session.get('business_unit_id')
    try:
        supplier = get_object_or_404(Suppliers, pk=pk, business_unit__business_unit_id=business_unit_id)
        if request.method == 'POST':
            supplier.delete()
            messages.success(request, "Supplier deleted successfully.")
            return redirect('supplier_list')
        return render(request, 'supplier_confirm_delete.html', {'object': supplier})
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('supplier_list')

@login_required
def supplier_inquiry(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        suppliers = Suppliers.objects.filter(business_unit=business_unit)
        return render(request, 'supplier_inquiry.html', {'suppliers': suppliers})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')

@login_required
def supplier_dashboard(request):
    business_unit_id = request.session.get('business_unit_id')
    try:
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        supplier_count = Suppliers.objects.filter(business_unit=business_unit).count()
        return render(request, 'supplier_dashboard.html', {'supplier_count': supplier_count})
    except BusinessUnit.DoesNotExist:
        messages.error(request, "Invalid business unit.")
        return redirect('admin_view')
    


@login_required
def supplier_payment_status(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    if not all([saas_user_id, saas_customer_id, business_unit_group_id, business_unit_id, branch_id]):
        logger.warning("Missing session data in supplier_payment_status: %s", {
            'saas_user_id': saas_user_id,
            'saas_customer_id': saas_customer_id,
            'business_unit_group_id': business_unit_group_id,
            'business_unit_id': business_unit_id,
            'branch_id': branch_id
        })
        messages.error(request, "Incomplete session data. Please log in again.")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        
        supplier_data = Suppliers.objects.filter(
            business_unit=business_unit
        ).annotate(
            number_of_pos=Count('purchaseorders__poid', distinct=True, filter=(
                Q(purchaseorders__order_date__range=['2025-01-01', '2025-04-01']) &
                Q(purchaseorders__branch=branch)
            )),
            total_purchases=Coalesce(Sum('purchaseorders__total_amount', filter=(
                Q(purchaseorders__order_date__range=['2025-01-01', '2025-04-01']) &
                Q(purchaseorders__branch=branch)
            )), 0, output_field=DecimalField()),
            total_payments=Coalesce(Sum('supplierpayment__amount', filter=(
                Q(supplierpayment__payment_date__range=['2025-01-01', '2025-04-01']) &
                Q(supplierpayment__branch=branch)
            )), 0, output_field=DecimalField()),
            outstanding_balance=Coalesce(Sum('purchaseorders__total_amount', filter=(
                Q(purchaseorders__order_date__range=['2025-01-01', '2025-04-01']) &
                Q(purchaseorders__branch=branch)
            )), 0, output_field=DecimalField()) - 
            Coalesce(Sum('supplierpayment__amount', filter=(
                Q(supplierpayment__payment_date__range=['2025-01-01', '2025-04-01']) &
                Q(supplierpayment__branch=branch)
            )), 0, output_field=DecimalField())
        ).order_by('-total_purchases')

        context = {
            'supplier_data': supplier_data,
            'username': user.saas_username,
            'business_unit': business_unit,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'branch': branch,
        }
        return render(request, 'supplier_payment_status.html', context)

    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, 
            BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Session data not found: {str(e)}")
        messages.error(request, "Invalid session data. Please log in again.")
        return redirect('login')
    



logger = logging.getLogger(__name__)

def calculate_payment_detailss(po):
    
    try:
        paid_amount_query = JournalEntryLine.objects.filter(
            journal_entry__reference=po.pono,
            journal_entry__business_unit=po.business_unit,
            credit__gt=0  
        )
        paid_amount = paid_amount_query.aggregate(total_paid=Sum('credit'))['total_paid'] or Decimal('0.000')
        balance = po.total_amount - paid_amount

        payment_details = [
            {
                'journal_entry_id': jel.journal_entry.journal_entry_id,
                'reference': jel.journal_entry.reference,
                'business_unit_id': jel.journal_entry.business_unit.business_unit_id,
                'debit': jel.debit,
                'credit': jel.credit,
                'account_type': jel.account.account_type,
                'account_name': jel.account.account_name,
                'create_remarks': jel.create_remarks
            } for jel in paid_amount_query
        ]

        logger.debug(f"Calculate Payment - PO {po.pono}: total_amount={po.total_amount:.3f}, paid_amount={paid_amount:.3f}, balance={balance:.3f}, payment_details={payment_details}")
        return paid_amount, balance, payment_details
    except Exception as e:
        logger.error(f"Error calculating payment details for PO {po.pono}: {str(e)}")
        return Decimal('0.000'), po.total_amount, []

@login_required
def supplier_payment(request, poid):
    saas_user_id = request.session.get('saas_user_id')
    if not saas_user_id:
        logger.warning("No saas_user_id in supplier_payment")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_username = user.saas_username

        purchase_order = PurchaseOrders.objects.get(poid=poid)
        business_unit_id = purchase_order.business_unit.business_unit_id

        
        paid_amount, balance, payment_details = calculate_payment_detailss(purchase_order)

    
        if paid_amount >= purchase_order.total_amount:
            postatus = 'Paid'
        elif paid_amount > 0:
            postatus = 'Partially Paid'
        else:
            postatus = 'Unpaid'

        
        payment_accounts = Category.objects.filter(
            category_type='PAYMENT_TYPE',
            business_unit_id=business_unit_id
        ).values('category_id', 'category_name', 'category_value')

        if not payment_accounts:
            logger.warning(f"No payment accounts for business unit: {purchase_order.business_unit}")
            messages.warning(request, "No payment methods available. Please contact the administrator.")

        context = {
            'purchase_order': purchase_order,
            'po_total': purchase_order.total_amount,
            'poid': poid,
            'username': saas_username,
            'payment_accounts': payment_accounts,
            'paid_amount': paid_amount,
            'balance': balance,
            'postatus': postatus,  
        }
        return render(request, 'supplier_payment.html', context)
    except PurchaseOrders.DoesNotExist:
        logger.error(f"Purchase Order not found: {poid}")
        messages.error(request, "Purchase Order not found.")
        return redirect('po_inquiry')
    except SAASUsers.DoesNotExist:
        logger.error(f"User not found: {saas_user_id}")
        return redirect('login')
    except Exception as e:
        logger.error(f"Error in supplier_payment: {str(e)}")
        messages.error(request, f"Error loading payment view: {str(e)}")
        return redirect('po_inquiry')





@login_required
@transaction.atomic
@require_POST
def confirm_supplier_payment(request):
    
    saas_user_id = request.session.get('saas_user_id')
    if not saas_user_id:
        logger.warning("No saas_user_id in confirm_supplier_payment")
        messages.error(request, "User not logged in.")
        return redirect('login')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_username = user.saas_username
    except SAASUsers.DoesNotExist:
        logger.error(f"User not found: {saas_user_id}")
        messages.error(request, "User not found.")
        return redirect('login')

    poid = request.POST.get('poid')
    total_amount = request.POST.get('total_amount')
    net_amount = request.POST.get('net_amount')
    payment_method_id = request.POST.get('payment_method')
    card_no = request.POST.get('card_no', '')
    remarks = request.POST.get('remarks', '')

    logger.debug(f"Confirm Payment - Received POST data: poid={poid}, total_amount={total_amount}, net_amount={net_amount}, payment_method_id={payment_method_id}, card_no='{card_no}', remarks='{remarks}'")

    if not all([poid, total_amount, net_amount, payment_method_id]):
        missing = []
        if not poid:
            missing.append("poid")
        if not total_amount:
            missing.append("total_amount")
        if not net_amount:
            missing.append("net_amount")
        if not payment_method_id:
            missing.append("payment_method")
        logger.warning(f"Missing fields in confirm_supplier_payment: {missing}")
        messages.error(request, f"Missing required fields: {', '.join(missing)}.")
        return redirect('supplier_payment', poid=poid)

    try:
        purchase_order = PurchaseOrders.objects.get(poid=poid)
        total_amount = Decimal(total_amount)
        net_amount = Decimal(net_amount)

        paid_amount, current_balance, payment_details = calculate_payment_detailss(purchase_order)

        logger.debug(f"Confirm Payment - PO {purchase_order.pono}: total_amount={total_amount:.3f}, paid_amount={paid_amount:.3f}, current_balance={current_balance:.3f}, net_amount={net_amount:.3f}, business_unit_id={purchase_order.business_unit.business_unit_id}")

        if net_amount <= 0:
            logger.warning(f"Invalid net_amount: {net_amount}")
            messages.error(request, "Payment amount must be greater than zero.")
            return redirect('supplier_payment', poid=poid)

        if net_amount > current_balance:
            logger.warning(f"Net amount {net_amount} exceeds balance {current_balance}")
            messages.error(request, "Payment amount cannot exceed remaining balance.")
            return redirect('supplier_payment', poid=poid)

        if paid_amount >= purchase_order.total_amount:
            logger.warning(f"PO already paid: {poid}")
            messages.error(request, "This purchase order has already been paid.")
            return redirect('supplier_payment', poid=poid)

        if not purchase_order.business_unit:
            logger.error(f"No business unit for PO: {poid}")
            messages.error(request, "Purchase order has no associated business unit.")
            return redirect('supplier_payment', poid=poid)

        def get_account(account_type, account_code, account_name):
            try:
                account = ChartOfAccounts.objects.get(
                    business_unit=purchase_order.business_unit,
                    account_code=account_code
                )
                if account.account_type != account_type or account.account_name != account_name:
                    raise ValueError(
                        f"Account mismatch: '{account_code}' exists but has type='{account.account_type}' "
                        f"and name='{account.account_name}' (expected type='{account_type}', name='{account_name}')"
                    )
                return account
            except ChartOfAccounts.DoesNotExist:
                available_accounts = ChartOfAccounts.objects.filter(
                    business_unit=purchase_order.business_unit
                ).values('account_code', 'account_name', 'account_type')
                logger.error(
                    f"Required account not found: {account_name} ({account_code}) for business unit {purchase_order.business_unit}. "
                    f"Available accounts: {list(available_accounts)}"
                )
                raise ValueError(
                    f"Required account not found: {account_name} ({account_code}). "
                    f"Please ensure the account exists for business unit {purchase_order.business_unit.name}."
                )

        try:
            payment_category = Category.objects.get(
                category_id=payment_method_id,
                category_type='PAYMENT_TYPE',
                business_unit_id=purchase_order.business_unit.business_unit_id
            )
            account_name = payment_category.category_name.upper()
            payment_account = ChartOfAccounts.objects.get(
                account_name=account_name,
                business_unit=purchase_order.business_unit
            )
        except Category.DoesNotExist:
            logger.error(f"Invalid payment method category: {payment_method_id}")
            messages.error(request, "Invalid payment method selected.")
            return redirect('supplier_payment', poid=poid)
        except ChartOfAccounts.DoesNotExist:
            logger.error(f"No ChartOfAccounts entry for payment method: {account_name}")
            messages.error(request, f"No account found for payment method: {account_name}.")
            return redirect('supplier_payment', poid=poid)

        accounts_payable = get_account('Liability', 'LIAB_002', 'Accounts Payable')
        tax_account = get_account('Liability', 'LIAB_001', 'Tax Payable')

        current_date = timezone.now().date()
        current_time = timezone.now()

        new_paid_amount = paid_amount + net_amount
        payment_status = 'Paid' if new_paid_amount >= purchase_order.total_amount else 'Partially Paid'

        
        if purchase_order.tax_amount > 0:
            
            tax_proportion = purchase_order.tax_amount / purchase_order.total_amount
            tax_amount = net_amount * tax_proportion
            payable_amount = net_amount - tax_amount
        else:
            
            tax_amount = Decimal('0.000')
            payable_amount = net_amount

        payment_remarks = f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment made for PO No: {purchase_order.pono}"
        if card_no or remarks:
            payment_remarks += f"; Card No: {card_no or 'N/A'}; Remarks: {remarks or 'None'}"

        logger.debug(f"Confirm Payment - PO {purchase_order.pono}: payment_remarks='{payment_remarks}', tax_amount={tax_amount:.3f}, payable_amount={payable_amount:.3f}")

        
        journal_entry = JournalEntries.objects.create(
            business_unit=purchase_order.business_unit,
            journal_entry_date=current_date,
            description=f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment for PO No: {purchase_order.pono}",
            card_no=card_no or '',
            remarks=remarks or '',
            reference=purchase_order.pono,
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=payment_remarks
        )

        
        
        JournalEntryLine.objects.create(
            business_unit=purchase_order.business_unit,
            journal_entry=journal_entry,
            account=accounts_payable,
            debit=payable_amount,
            credit=Decimal('0.000'),
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=f"Payment for PO No: {purchase_order.pono}"
        )

        
        if tax_amount > 0:
            JournalEntryLine.objects.create(
                business_unit=purchase_order.business_unit,
                journal_entry=journal_entry,
                account=tax_account,
                debit=tax_amount,
                credit=Decimal('0.000'),
                create_dt=current_date,
                create_tm=current_time,
                create_by=saas_username,
                create_remarks=f"Tax payment for PO No: {purchase_order.pono}"
            )


        JournalEntryLine.objects.create(
            business_unit=purchase_order.business_unit,
            journal_entry=journal_entry,
            account=payment_account,
            debit=Decimal('0.000'),
            credit=net_amount,
            create_dt=current_date,
            create_tm=current_time,
            create_by=saas_username,
            create_remarks=payment_remarks
        )

        
        updates = [
            (accounts_payable, -payable_amount, f"Payment of PO No: {purchase_order.pono}"),
            (payment_account, -net_amount, f"Payment made for PO No: {purchase_order.pono}")
        ]
        if tax_amount > 0:
            updates.append((tax_account, -tax_amount, f"Tax payment of PO No: {purchase_order.pono}"))

        for account, amount, remark in updates:
            if amount != 0:
                account.account_balance += amount
                account.save(update_fields=['account_balance'])

    
        saved_payment = JournalEntryLine.objects.filter(
            journal_entry__reference=purchase_order.pono,
            journal_entry__business_unit=purchase_order.business_unit,
            credit=net_amount,
            create_remarks=payment_remarks
        ).first()
        if saved_payment:
            logger.debug(f"Confirm Payment - PO {purchase_order.pono}: Payment saved successfully, journal_entry_line_id={saved_payment.journal_entry_line_id}, create_remarks='{saved_payment.create_remarks}'")
        else:
            logger.error(f"Confirm Payment - PO {purchase_order.pono}: Failed to verify saved payment for {net_amount:.3f}, payment_remarks='{payment_remarks}'")
            messages.error(request, f"Payment processing issue for PO No: {purchase_order.pono}. Please try again.")
            return redirect('supplier_payment', poid=poid)

        logger.debug(f"Confirm Payment - PO {purchase_order.pono}: Payment of {net_amount:.3f}, new_paid_amount={new_paid_amount:.3f}, payment_status={payment_status}, tax_amount={tax_amount:.3f}, payable_amount={payable_amount:.3f}")

        messages.success(request, f"{'Partial ' if payment_status == 'Partially Paid' else ''}Payment of {net_amount:.3f} for PO No: {purchase_order.pono} processed successfully.")
        return redirect('po_inquiry')
    except PurchaseOrders.DoesNotExist:
        logger.error(f"Purchase Order not found: {poid}")
        messages.error(request, "Purchase Order not found.")
        return redirect('supplier_payment', poid=poid)
    except ValueError as e:
        logger.error(f"Account error in confirm_supplier_payment: {str(e)}")
        messages.error(request, f"Account error: {str(e)}")
        return redirect('supplier_payment', poid=poid)
    except Exception as e:
        logger.error(f"Error in confirm_supplier_payment: {str(e)}")
        messages.error(request, f"Error confirming payment: {str(e)}")
        return redirect('supplier_payment', poid=poid)

def calculate_payment_detailss(po):
    try:
        paid_amount_query = JournalEntryLine.objects.filter(
            journal_entry__reference=po.pono,
            journal_entry__business_unit=po.business_unit,
            credit__gt=0  
        )
        paid_amount = paid_amount_query.aggregate(total_paid=Sum('credit'))['total_paid'] or Decimal('0.000')
        balance = po.total_amount - paid_amount

        payment_details = [
            {
                'journal_entry_id': jel.journal_entry.journal_entry_id,
                'reference': jel.journal_entry.reference,
                'business_unit_id': jel.journal_entry.business_unit.business_unit_id,
                'debit': jel.debit,
                'credit': jel.credit,
                'account_type': jel.account.account_type,
                'account_name': jel.account.account_name,
                'create_remarks': jel.create_remarks
            } for jel in paid_amount_query
        ]

        logger.debug(f"Calculate Payment - PO {po.pono}: total_amount={po.total_amount:.3f}, paid_amount={paid_amount:.3f}, balance={balance:.3f}, payment_details={payment_details}")
        return paid_amount, balance, payment_details
    except Exception as e:
        logger.error(f"Error calculating payment details for PO {po.pono}: {str(e)}")
        return Decimal('0.000'), po.total_amount, []
    
    
@login_required
def po_inquiry(request):
   
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        purchase_orders = PurchaseOrders.objects.filter(
            business_unit=business_unit,
            branch=branch
        ).select_related('supplier').order_by('-order_date')

        
        for po in purchase_orders:
            paid_amount, balance, payment_details = calculate_payment_detailss(po)
            po.paid_amount = paid_amount
            po.balance = balance
            
            if paid_amount >= po.total_amount:
                po.postatus = 'Paid'
            elif paid_amount > 0:
                po.postatus = 'Partially Paid'
            else:
                po.postatus = 'Unpaid'

            po.items_list = po.purchaseorderitems_set.all()    

        context = {
            'username': user.saas_username,
            'business_unit': business_unit,
            'branch': branch,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'purchase_orders': purchase_orders,
            'start_date': request.GET.get('start_date', ''),
            'end_date': request.GET.get('end_date', ''),
        }
        return render(request, 'po_inquiry.html', context)

    except Exception as e:
        logger.error(f"Error in po_inquiry: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')    
    



logger = logging.getLogger(__name__)

@login_required
def po_detail(request, poid):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)

        
        purchase_order = PurchaseOrders.objects.filter(
            poid=poid,
            business_unit=business_unit,
            branch=branch
        ).select_related('supplier').prefetch_related('purchaseorderitems_set').first()

        if not purchase_order:
            logger.error(f"Purchase order with ID {poid} not found")
            messages.error(request, "Purchase order not found.")
            return redirect('po_inquiry')

        paid_amount, balance, payment_details = calculate_payment_detailss(purchase_order)
        purchase_order.paid_amount = paid_amount
        purchase_order.balance = balance
        purchase_order.items_list = purchase_order.purchaseorderitems_set.all()

        context = {
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'purchase_order': purchase_order,
        }
        return render(request, 'po_detail.html', context)

    except Exception as e:
        logger.error(f"Error in po_detail: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')    





logger = logging.getLogger(__name__)


def room_add(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in room_add: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        form = RoomForm(request.POST, business_unit=business_unit)
        if form.is_valid():
            room = form.save(commit=False)
            room.business_unit = business_unit
            room.create_by = user.saas_username

            current_date = timezone.now().strftime('%Y-%m-%d')
            room.create_remarks = f"Room created by {user.saas_username} on {current_date}"

            room.update_dt = '1900-01-01'
            room.update_tm = '1900-01-01'
            room.update_by = ''
            room.update_marks = ''
            room.save()
            messages.success(request, "Room added successfully.")
            return redirect('room_list')
    else:
        form = RoomForm(business_unit=business_unit)

    context = {
        'form': form,
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'app_label': 'pos',
    }
    return render(request, 'room_add.html', context)

def room_edit(request, pk):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        room = get_object_or_404(Rooms, pk=pk, business_unit__business_unit_id=business_unit_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in room_edit: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room, business_unit=business_unit)
        if form.is_valid():
            room = form.save(commit=False)

            changed_fields = []
            field_display_names = {
                'room_type': 'Room Type',
                'room_name': 'Room Name',
                'location': 'Location',
                'phone_1': 'Phone 1',
                'phone_2': 'Phone 2',
            }
            for field in form.changed_data:
                changed_fields.append(field_display_names.get(field, field))

            room.update_dt = date.today()
            room.update_tm = timezone.now()
            room.update_by = user.saas_username[:10]
            room.update_marks = (
                f"Updated on {date.today().strftime('%Y-%m-%d')} by {user.saas_username[:10]}. "
                f"Fields changed: {', '.join(changed_fields)}" if changed_fields
                else f"Form submitted on {date.today().strftime('%Y-%m-%d')} by {user.saas_username[:10]} with no field changes"
            )[:200]

            room.business_unit = business_unit
            room.save()
            messages.success(request, "Room updated successfully.")
            return redirect('room_list')
    else:
        form = RoomForm(instance=room, business_unit=business_unit)

    context = {
        'form': form,
        'room': room,
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'app_label': 'pos',
    }
    return render(request, 'room_edit.html', context)

def room_list(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        rooms = Rooms.objects.filter(business_unit=business_unit).order_by('-create_dt')
        paginator = Paginator(rooms, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'room_list.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in room_list: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

def room_delete(request, pk):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        room = get_object_or_404(Rooms, pk=pk, business_unit__business_unit_id=business_unit_id)
        if request.method == 'POST':
            room.delete()
            messages.success(request, "Room deleted successfully.")
            return redirect('room_list')

        context = {
            'object': room,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'room_confirm_delete.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in room_delete: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')

def room_inquiry(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        rooms = Rooms.objects.filter(business_unit=business_unit)

        context = {
            'rooms': rooms,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'room_inquiry.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in room_inquiry: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

def room_dashboard(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        room_count = Rooms.objects.filter(business_unit=business_unit).count()

        context = {
            'room_count': room_count,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'room_dashboard.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in room_dashboard: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')


def table_add(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in table_add: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        form = TableForm(request.POST, business_unit=business_unit)
        if form.is_valid():
            table = form.save(commit=False)
            table.business_unit = business_unit
            table.create_by = user.saas_username

            current_date = timezone.now().strftime('%Y-%m-%d')
            table.create_remarks = f"Table created by {user.saas_username} on {current_date}"

            table.update_dt = '1900-01-01'
            table.update_tm = '1900-01-01'
            table.update_by = ''
            table.update_marks = ''
            table.save()
            messages.success(request, "Table added successfully.")
            return redirect('table_list')
    else:
        form = TableForm(business_unit=business_unit)

    context = {
        'form': form,
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'app_label': 'pos',
    }
    return render(request, 'table_add.html', context)

def table_edit(request, pk):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        table = get_object_or_404(Tables, pk=pk, business_unit__business_unit_id=business_unit_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in table_edit: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        form = TableForm(request.POST, instance=table, business_unit=business_unit)
        if form.is_valid():
            table = form.save(commit=False)

            changed_fields = []
            field_display_names = {
                'location': 'Location',
                'no_of_seats': 'Number of Seats',
            }
            for field in form.changed_data:
                changed_fields.append(field_display_names.get(field, field))

            table.update_dt = date.today()
            table.update_tm = timezone.now()
            table.update_by = user.saas_username[:10]
            table.update_marks = (
                f"Updated on {date.today().strftime('%Y-%m-%d')} by {user.saas_username[:10]}. "
                f"Fields changed: {', '.join(changed_fields)}" if changed_fields
                else f"Form submitted on {date.today().strftime('%Y-%m-%d')} by {user.saas_username[:10]} with no field changes"
            )[:200]

            table.business_unit = business_unit
            table.save()
            messages.success(request, "Table updated successfully.")
            return redirect('table_list')
    else:
        form = TableForm(instance=table, business_unit=business_unit)

    context = {
        'form': form,
        'table': table,
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'app_label': 'pos',
    }
    return render(request, 'table_edit.html', context)

def table_list(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        tables = Tables.objects.filter(business_unit=business_unit).order_by('-create_dt')
        paginator = Paginator(tables, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'table_list.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in table_list: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

def table_delete(request, pk):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        table = get_object_or_404(Tables, pk=pk, business_unit__business_unit_id=business_unit_id)
        if request.method == 'POST':
            table.delete()
            messages.success(request, "Table deleted successfully.")
            return redirect('table_list')

        context = {
            'object': table,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'table_confirm_delete.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in table_delete: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')

def table_inquiry(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        tables = Tables.objects.filter(business_unit=business_unit)

        context = {
            'tables': tables,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'table_inquiry.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in table_inquiry: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

def table_dashboard(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        table_count = Tables.objects.filter(business_unit=business_unit).count()

        context = {
            'table_count': table_count,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'table_dashboard.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in table_dashboard: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')


def vehicle_add(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in vehicle_add: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        form = VehicleForm(request.POST, business_unit=business_unit)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.business_unit = business_unit
            vehicle.create_by = user.saas_username

            current_date = timezone.now().strftime('%Y-%m-%d')
            vehicle.create_remarks = f"Vehicle created by {user.saas_username} on {current_date}"

            vehicle.update_dt = '1900-01-01'
            vehicle.update_tm = '1900-01-01'
            vehicle.update_by = ''
            vehicle.update_marks = ''
            vehicle.save()
            messages.success(request, "Vehicle added successfully.")
            return redirect('vehicle_list')
    else:
        form = VehicleForm(business_unit=business_unit)

    context = {
        'form': form,
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'app_label': 'pos',
    }
    return render(request, 'vehicle_add.html', context)

def vehicle_edit(request, pk):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        vehicle = get_object_or_404(Vehicle, pk=pk, business_unit__business_unit_id=business_unit_id)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in vehicle_edit: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle, business_unit=business_unit)
        if form.is_valid():
            vehicle = form.save(commit=False)

            changed_fields = []
            field_display_names = {
                'vehicle_type': 'Vehicle Type',
                'vehicle_name': 'Vehicle Name',
            }
            for field in form.changed_data:
                changed_fields.append(field_display_names.get(field, field))

            vehicle.update_dt = date.today()
            vehicle.update_tm = timezone.now()
            vehicle.update_by = user.saas_username[:10]
            vehicle.update_marks = (
                f"Updated on {date.today().strftime('%Y-%m-%d')} by {user.saas_username[:10]}. "
                f"Fields changed: {', '.join(changed_fields)}" if changed_fields
                else f"Form submitted on {date.today().strftime('%Y-%m-%d')} by {user.saas_username[:10]} with no field changes"
            )[:200]

            vehicle.business_unit = business_unit
            vehicle.save()
            messages.success(request, "Vehicle updated successfully.")
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle, business_unit=business_unit)

    context = {
        'form': form,
        'vehicle': vehicle,
        'username': user.saas_username,
        'saas_customer': saas_customer,
        'business_unit_group': business_unit_group,
        'business_unit': business_unit,
        'branch': branch,
        'app_label': 'pos',
    }
    return render(request, 'vehicle_edit.html', context)

def vehicle_list(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        vehicles = Vehicle.objects.filter(business_unit=business_unit).order_by('-create_dt')
        paginator = Paginator(vehicles, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'vehicle_list.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in vehicle_list: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

def vehicle_delete(request, pk):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        vehicle = get_object_or_404(Vehicle, pk=pk, business_unit__business_unit_id=business_unit_id)
        if request.method == 'POST':
            vehicle.delete()
            messages.success(request, "Vehicle deleted successfully.")
            return redirect('vehicle_list')

        context = {
            'object': vehicle,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'vehicle_confirm_delete.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in vehicle_delete: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')

def vehicle_inquiry(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        vehicles = Vehicle.objects.filter(business_unit=business_unit)

        context = {
            'vehicles': vehicles,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'vehicle_inquiry.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in vehicle_inquiry: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')

def vehicle_dashboard(request):
    saas_user_id = request.session.get('saas_user_id')
    saas_customer_id = request.session.get('saas_customer_id')
    business_unit_group_id = request.session.get('business_unit_group_id')
    business_unit_id = request.session.get('business_unit_id')
    branch_id = request.session.get('branch_id')

    try:
        user = SAASUsers.objects.get(saas_user_id=saas_user_id)
        saas_customer = SAASCustomer.objects.get(saas_customer_id=saas_customer_id)
        business_unit_group = BusinessUnitGroup.objects.get(business_unit_group_id=business_unit_group_id)
        business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
        branch = Branch.objects.get(branch_id=branch_id)
        vehicle_count = Vehicle.objects.filter(business_unit=business_unit).count()

        context = {
            'vehicle_count': vehicle_count,
            'username': user.saas_username,
            'saas_customer': saas_customer,
            'business_unit_group': business_unit_group,
            'business_unit': business_unit,
            'branch': branch,
            'app_label': 'pos',
        }
        return render(request, 'vehicle_dashboard.html', context)
    except (SAASUsers.DoesNotExist, SAASCustomer.DoesNotExist, BusinessUnitGroup.DoesNotExist, BusinessUnit.DoesNotExist, Branch.DoesNotExist) as e:
        logger.error(f"Error in vehicle_dashboard: {str(e)}")
        messages.error(request, f"Invalid session data: {str(e)}")
        return redirect('login')