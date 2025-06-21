from django.contrib import admin
from .models import *


from django.contrib import admin
from .models import (
    SAASCustomer, SAASUsers, Category, Category2, BusinessUnitGroup,
    BusinessUnit, Branch, Warehouse, Customer, Suppliers, ProductGroup,
    Products, InventoryHeader, InventoryLine, SalesHeader, SalesLine,
    Tables, Vehicle, Rooms, ChartOfAccounts, JournalEntries, JournalEntryLine
)

@admin.register(SAASCustomer)
class SAASCustomerAdmin(admin.ModelAdmin):
    list_display = ('saas_customer_id', 'saas_customer_name', 'email', 'create_dt')
    search_fields = ('saas_customer_name', 'email')
    list_filter = ('create_dt',)

@admin.register(SAASUsers)
class SAASUsersAdmin(admin.ModelAdmin):
    list_display = ('saas_user_id', 'saas_username', 'saas_customer', 'create_dt')
    search_fields = ('saas_username',)
    list_filter = ('create_dt',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'business_unit_id', 'category_type', 'category_name', 'create_dt')
    search_fields = ('category_name', 'category_type')
    list_filter = ('business_unit_id', 'create_dt')

@admin.register(Category2)
class Category2Admin(admin.ModelAdmin):
    list_display = ('category_id', 'business_unit_id', 'category2_type', 'category_name', 'create_dt')
    search_fields = ('category_name', 'category2_type')
    list_filter = ('business_unit_id', 'create_dt')

@admin.register(BusinessUnitGroup)
class BusinessUnitGroupAdmin(admin.ModelAdmin):
    list_display = ('business_unit_group_id', 'business_unit_group_name', 'saas_customer', 'create_dt')
    search_fields = ('business_unit_group_name',)
    list_filter = ('create_dt',)

@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('business_unit_id', 'business_unit_name', 'business_unit_group', 'create_dt')
    search_fields = ('business_unit_name',)
    list_filter = ('business_unit_group', 'create_dt')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_id', 'branch_name', 'business_unit', 'create_dt')
    search_fields = ('branch_name',)
    list_filter = ('business_unit', 'create_dt')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('warehouse_id', 'warehouse_name', 'business_unit', 'branch', 'create_dt')
    search_fields = ('warehouse_name',)
    list_filter = ('business_unit', 'branch', 'create_dt')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'customer_name', 'business_unit', 'email', 'create_dt')
    search_fields = ('customer_name', 'email')
    list_filter = ('business_unit', 'create_dt')

@admin.register(Suppliers)
class SuppliersAdmin(admin.ModelAdmin):
    list_display = ('supplier_id', 'supplier_name', 'business_unit', 'supplier_type', 'create_dt')
    search_fields = ('supplier_name',)
    list_filter = ('business_unit', 'supplier_type', 'create_dt')

@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ('product_group_id', 'product_name', 'business_unit', 'create_dt')
    search_fields = ('product_name',)
    list_filter = ('business_unit', 'create_dt')



@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_name', 'business_unit', 'product_group', 'category_name', 'product_price', 'create_dt')
    search_fields = ('product_name', 'sku')
    list_filter = ('business_unit', 'product_group', 'category', 'create_dt')
    list_per_page = 20

    def category_name(self, obj):
        return obj.category.category_name if obj.category else 'No Category'
    category_name.short_description = 'Category Name'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('business_unit', 'product_group', 'category')

@admin.register(InventoryHeader)
class InventoryHeaderAdmin(admin.ModelAdmin):
    list_display = ('inventory_id', 'business_unit', 'branch', 'warehouse', 'grnno', 'ref_type', 'ref_no', 'net_value', 'create_dt')
    search_fields = ('grnno', 'ref_no', 'create_by')
    list_filter = ('business_unit', 'branch', 'warehouse', 'create_dt')

@admin.register(InventoryLine)
class InventoryLineAdmin(admin.ModelAdmin):
    list_display = ('inventory_line_id', 'business_unit', 'inventory', 'product', 'qty', 'total_value', 'create_dt')
    search_fields = ('product__product_name',)
    list_filter = ('business_unit', 'inventory', 'create_dt')

@admin.register(SalesHeader)
class SalesHeaderAdmin(admin.ModelAdmin):
    list_display = ('sale_id', 'business_unit', 'branch', 'customer', 'total_amount', 'sale_date', 'create_dt')
    search_fields = ('sale_no', 'customer__customer_name')
    list_filter = ('business_unit', 'branch', 'sale_date', 'create_dt')

@admin.register(SalesLine)
class SalesLineAdmin(admin.ModelAdmin):
    list_display = ('sale_line_id', 'sale', 'product', 'qty', 'price', 'total_amount', 'create_dt')
    search_fields = ('product__product_name',)
    list_filter = ('sale', 'create_dt')

@admin.register(Tables)
class TablesAdmin(admin.ModelAdmin):
    list_display = ('table_id', 'business_unit', 'location', 'no_of_seats', 'create_dt')
    search_fields = ('location',)
    list_filter = ('business_unit', 'create_dt')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_id', 'business_unit', 'vehicle_type', 'vehicle_name', 'create_dt')
    search_fields = ('vehicle_name',)
    list_filter = ('business_unit', 'vehicle_type', 'create_dt')

@admin.register(Rooms)
class RoomsAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'business_unit', 'room_name', 'room_type', 'location', 'create_dt')
    search_fields = ('room_name',)
    list_filter = ('business_unit', 'room_type', 'create_dt')

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'business_unit', 'account_code', 'account_name', 'account_balance', 'create_dt')
    search_fields = ('account_code', 'account_name')
    list_filter = ('business_unit', 'account_type', 'create_dt')

@admin.register(JournalEntries)
class JournalEntriesAdmin(admin.ModelAdmin):
    list_display = ('journal_entry_id', 'business_unit', 'journal_entry_date', 'description', 'create_dt')
    search_fields = ('description', 'reference')
    list_filter = ('business_unit', 'journal_entry_date', 'create_dt')

@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ('journal_entry_line_id', 'journal_entry', 'account', 'debit', 'credit', 'create_dt')
    search_fields = ('account__account_name',)
    list_filter = ('journal_entry', 'create_dt')



@admin.register(PurchaseOrders)
class PurchaseOrdersAdmin(admin.ModelAdmin):
    list_display = ('pono', 'supplier', 'order_date', 'postatus', 'total_amount', 'createdt')
    search_fields = ('pono', 'remarks')
    list_filter = ('business_unit', 'branch', 'postatus', 'order_date', 'createdt')
    list_per_page = 20


@admin.register(PurchaseOrderItems)
class PurchaseOrderItemsAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'poid', 'product', 'quantity', 'unit_price', 'line_total', 'createdt')
    search_fields = ('remarks',)
    list_filter = ('business_unit', 'poid', 'createdt')
    list_per_page = 20


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'business_unit', 'product', 'ref_no', 'ref_type', 'quantity', 'createdt')
    search_fields = ('ref_no', 'remarks')
    list_filter = ('business_unit', 'ref_type', 'createdt')
    list_per_page = 20


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'supplier', 'business_unit', 'branch',
        'payment_date', 'amount', 'payment_ref', 'createdt'
    )
    list_filter = ('business_unit', 'branch', 'payment_date', 'createdt')
    search_fields = ('payment_ref', 'supplier__supplier_name')
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date',)
    fields = (
        'business_unit', 'branch', 'supplier', 'payment_date', 'amount',
        'payment_ref', 'remarks', 'createby', 'createremarks',
        'updateby', 'updatemarks'
    )
    autocomplete_fields = ['business_unit', 'branch', 'supplier']    