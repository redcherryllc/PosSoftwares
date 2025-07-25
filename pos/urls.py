from django.urls import path
from . import views 
from .views import login_view, home_view



urlpatterns = [
 
   

     path("", login_view, name="login"),
     path('login/', views.login_view, name='login'),
    path("home/", home_view, name="home"),
    path('get_business_unit_groups/', views.get_business_unit_groups, name='get_business_unit_groups'),
    path('get_business_units/', views.get_business_units, name='get_business_units'),
    path('get_branches/', views.get_branches, name='get_branches'),


    path('api/check-stock/<int:product_id>/', views.check_stock, name='check_stock'),
    path('api/products/', views.get_products, name='get_products'),
    path('api/complete-sale/', views.complete_sale, name='complete_sale'),



    path('api/save-sale/', views.save_sale, name='save_sale'),

    path('view-order/', views.view_order, name='view_order'),

    path('sale_inquiry/', views.sale_inquiry, name='sale_inquiry'),
    
    path('sale_detail/<int:sale_id>/', views.sale_detail, name='sale_detail'),

    path('api/get-sale-details/', views.get_sale_details, name='get_sale_details'),

    path('logout/', views.logout_view, name='logout'),

    path('add-customer/', views.add_customer, name='add_customer'),


    

    path('process_payment/', views.process_payment, name='process_payment'),
    
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),

    path('payment_view/', views.payment_view, name="payment_view"),

    path('admin_view/', views.admin_view, name="admin_view"),


    path('expense_entry/', views.expense_entry, name='expense_entry'),

    path('expenses/', views.expense_list, name='expense_list'),





    
    path('general-ledger/', views.general_ledger_report, name='general_ledger_report'),
    path('trial-balance/', views.trial_balance_report, name='trial_balance_report'),
    path('balance-sheet/', views.balance_sheet, name='balance_sheet'),
    path('income-statement/', views.income_statement, name='income_statement'),
    path('sales-by-customer/', views.sales_by_customer_report, name='sales_by_customer_report'),
    path('product-sales/', views.product_sales_report, name='product_sales_report'),
path('purchase-by-supplier/', views.purchase_by_supplier_report, name='purchase_by_supplier_report'),


    path('expense_entry/', views.expense_entry, name='expense_entry'),

    path('inventory-valuation/', views.inventory_valuation_report, name='inventory_valuation_report'),
path('po-creation/', views.po_creation, name='po_creation'),
    path('po-inquiry/', views.po_inquiry, name='po_inquiry'),
        path('stock-adjustment/', views.stock_adjustment, name='stock_adjustment'),

   
    path('stock-adjustment/', views.stock_adjustment, name='stock_adjustment'),
        path('stock-return/', views.stock_return, name='stock_return'),
   

    path('stock_report/<str:product_id>/', views.stock_report, name='stock_report'),
    path('stock_report_list/', views.stock_report_list, name='stock_report_list'),


    path('customer-bills/', views.customer_bills, name='customer_bills'),
    path('customer-summary/', views.customer_summary, name='customer_summary'),
    

    path('productgroup/add/', views.productgroup_add, name='productgroup_add'),
    path('productgroup/edit/<int:pk>/', views.productgroup_edit, name='productgroup_edit'),
    path('productgroup/list/', views.productgroup_list, name='productgroup_list'),
    path('productgroup/delete/<int:pk>/', views.productgroup_delete, name='productgroup_delete'),
    path('productgroup/inquiry/', views.productgroup_inquiry, name='productgroup_inquiry'),
    path('productgroup/dashboard/', views.productgroup_dashboard, name='productgroup_dashboard'),
    
    
    path('product/add/', views.product_add, name='product_add'),
    path('product/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('product/list/', views.product_list, name='product_list'),
    path('product/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('product/inquiry/', views.product_inquiry, name='product_inquiry'),
    path('product/dashboard/', views.product_dashboard, name='product_dashboard'),


    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),
    path('suppliers/list/', views.supplier_list, name='supplier_list'),
    path('suppliers/inquiry/', views.supplier_inquiry, name='supplier_inquiry'),
    path('suppliers/dashboard/', views.supplier_dashboard, name='supplier_dashboard'),



    path('supplier-payment/', views.supplier_payment, name='supplier_payment'),
     path('supplier-payment-status/', views.supplier_payment_status, name='supplier_payment_status'),

     path('supplier_payment/<int:poid>/', views.supplier_payment, name='supplier_payment'),

path('confirm_supplier_payment/', views.confirm_supplier_payment, name='confirm_supplier_payment'),

 path('po_detail/<int:poid>/', views.po_detail, name='po_detail'),


]