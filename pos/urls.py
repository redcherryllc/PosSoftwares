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


 path('room/add/', views.room_add, name='room_add'),
    path('room/edit/<int:pk>/', views.room_edit, name='room_edit'),
    path('room/list/', views.room_list, name='room_list'),
    path('room/delete/<int:pk>/', views.room_delete, name='room_delete'),
    path('room/inquiry/', views.room_inquiry, name='room_inquiry'),
    path('room/dashboard/', views.room_dashboard, name='room_dashboard'),


path('table/add/', views.table_add, name='table_add'),
    path('table/edit/<int:pk>/', views.table_edit, name='table_edit'),
    path('table/list/', views.table_list, name='table_list'),
    path('table/delete/<int:pk>/', views.table_delete, name='table_delete'),
    path('table/inquiry/', views.table_inquiry, name='table_inquiry'),
    path('table/dashboard/', views.table_dashboard, name='table_dashboard'),

    path('vehicle/add/', views.vehicle_add, name='vehicle_add'),
    path('vehicle/edit/<int:pk>/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicle/list/', views.vehicle_list, name='vehicle_list'),
    path('vehicle/delete/<int:pk>/', views.vehicle_delete, name='vehicle_delete'),
    path('vehicle/inquiry/', views.vehicle_inquiry, name='vehicle_inquiry'),
    path('vehicle/dashboard/', views.vehicle_dashboard, name='vehicle_dashboard'),    

    path('saasuser/add/', views.saasuser_add, name='saasuser_add'),
    path('saasuser/edit/<int:pk>/', views.saasuser_edit, name='saasuser_edit'),
    path('saasuser/list/', views.saasuser_list, name='saasuser_list'),
    path('saasuser/delete/<int:pk>/', views.saasuser_delete, name='saasuser_delete'),
    path('saasuser/inquiry/', views.saasuser_inquiry, name='saasuser_inquiry'),
    path('saasuser/dashboard/', views.saasuser_dashboard, name='saasuser_dashboard'),

    path('category/add/', views.category_add, name='category_add'),
    path('category/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('category/list/', views.category_list, name='category_list'),
    path('category/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('category/inquiry/', views.category_inquiry, name='category_inquiry'),
    path('category/dashboard/', views.category_dashboard, name='category_dashboard'),

    path('businessunitgroup/add/', views.businessunitgroup_add, name='businessunitgroup_add'),
    path('businessunitgroup/edit/<int:pk>/', views.businessunitgroup_edit, name='businessunitgroup_edit'),
    path('businessunitgroup/list/', views.businessunitgroup_list, name='businessunitgroup_list'),
    path('businessunitgroup/delete/<int:pk>/', views.businessunitgroup_delete, name='businessunitgroup_delete'),
    path('businessunitgroup/inquiry/', views.businessunitgroup_inquiry, name='businessunitgroup_inquiry'),
    path('businessunitgroup/dashboard/', views.businessunitgroup_dashboard, name='businessunitgroup_dashboard'),
  
    path('businessunit/add/', views.businessunit_add, name='businessunit_add'),
    path('businessunit/edit/<int:pk>/', views.businessunit_edit, name='businessunit_edit'),
    path('businessunit/list/', views.businessunit_list, name='businessunit_list'),
    path('businessunit/delete/<int:pk>/', views.businessunit_delete, name='businessunit_delete'),
    path('businessunit/inquiry/', views.businessunit_inquiry, name='businessunit_inquiry'),
    path('businessunit/dashboard/', views.businessunit_dashboard, name='businessunit_dashboard'),
   
    path('branch/add/', views.branch_add, name='branch_add'),
    path('branch/edit/<int:pk>/', views.branch_edit, name='branch_edit'),
    path('branch/list/', views.branch_list, name='branch_list'),
    path('branch/delete/<int:pk>/', views.branch_delete, name='branch_delete'),
    path('branch/inquiry/', views.branch_inquiry, name='branch_inquiry'),
    path('branch/dashboard/', views.branch_dashboard, name='branch_dashboard'),
    
    path('warehouse/add/', views.warehouse_add, name='warehouse_add'),
    path('warehouse/edit/<int:pk>/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouse/list/', views.warehouse_list, name='warehouse_list'),
    path('warehouse/delete/<int:pk>/', views.warehouse_delete, name='warehouse_delete'),
    path('warehouse/inquiry/', views.warehouse_inquiry, name='warehouse_inquiry'),
    path('warehouse/dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),
    
    path('customer/add/', views.customer_add, name='customer_add'),
    path('customer/edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('customer/list/', views.customer_list, name='customer_list'),
    path('customer/delete/<int:pk>/', views.customer_delete, name='customer_delete'),
    path('customer/inquiry/', views.customer_inquiry, name='customer_inquiry'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),

 

 


]