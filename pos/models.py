from django.db import models
from django.utils import timezone
import datetime



class SAASCustomer(models.Model):
    saas_customer_id = models.BigAutoField(primary_key=True)
    saas_customer_name = models.CharField(max_length=50, default='', null=False)
    phone_1 = models.BigIntegerField(default=0, null=False)
    phone_2 = models.BigIntegerField(default=0, null=False)
    email = models.CharField(max_length=50, default='', null=False)
    address = models.CharField(max_length=200, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'SAASCUSTOMER'
      
    def __str__(self):
         return self.saas_customer_name   
    
class SAASUsers(models.Model):
    saas_user_id = models.BigIntegerField(primary_key=True)
    saas_customer = models.ForeignKey(SAASCustomer, on_delete=models.CASCADE, db_column='saas_customer_id')
    saas_username = models.CharField(max_length=50, default='', null=False)
    saas_user_password = models.CharField(max_length=50, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)    

    class Meta:
        db_table = 'SAASUSERS'
    def __str__(self):
         return self.saas_username
    

class Category(models.Model):
    business_unit_id = models.BigIntegerField(default=0, null=False)
    category_type = models.CharField(max_length=50, default='', null=False)
    category_value = models.CharField(max_length=50, default='', null=False)
    category_name = models.CharField(max_length=150, default='', null=False)
    category_id = models.BigAutoField(primary_key=True)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'CATEGORY'
        unique_together = ('business_unit_id', 'category_type', 'category_value')
    def __str__(self):
         return self.category_name    

class Category2(models.Model):
    business_unit_id = models.BigIntegerField(default=0, null=False)
    category2_type = models.CharField(max_length=50, default='', null=False)
    category2_value = models.CharField(max_length=50, default='', null=False)
    category2_param_type = models.CharField(max_length=50, default='', null=False)
    category2_param_value = models.CharField(max_length=50, default='', null=False)
    category_name = models.CharField(max_length=150, default='', null=False)
    category_id = models.BigAutoField(primary_key=True)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'CATEGORY2'
        unique_together = ('business_unit_id', 'category2_type', 'category2_value', 'category2_param_type', 'category2_param_value')

class BusinessUnitGroup(models.Model):
    business_unit_group_id = models.BigAutoField(primary_key=True)
    business_unit_group_name = models.CharField(max_length=50, default='', null=False)
    saas_customer = models.ForeignKey(SAASCustomer, on_delete=models.CASCADE, db_column='saas_customer_id')
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'BUSINESSUNITGROUP'
    def __str__(self):
         return self.business_unit_group_name      

class BusinessUnit(models.Model):
    business_unit_id = models.BigAutoField(primary_key=True)
    business_unit_name = models.CharField(max_length=50, default='', null=False)
    business_unit_currency = models.CharField(max_length=10, default='', null=False)
    phone_1 = models.BigIntegerField(default=0, null=False)
    phone_2 = models.BigIntegerField(default=0, null=False)
    email = models.CharField(max_length=50, default='', null=False)
    address = models.CharField(max_length=200, default='', null=False)
    business_unit_group = models.ForeignKey(BusinessUnitGroup, on_delete=models.CASCADE, db_column='business_unit_group_id')
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'BUSINESSUNIT'
    def __str__(self):
         return self.business_unit_name   

class Branch(models.Model):
    branch_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    branch_name = models.CharField(max_length=50, default='', null=False)
    phone_1 = models.BigIntegerField(default=0, null=False)
    phone_2 = models.BigIntegerField(default=0, null=False)
    email = models.CharField(max_length=50, default='', null=False)
    address = models.CharField(max_length=200, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'BRANCH'
    def __str__(self):
         return self.branch_name    
    

class Warehouse(models.Model):
    warehouse_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, db_column='branch_id')
    warehouse_name = models.CharField(max_length=50, default='', null=False)
    address = models.CharField(max_length=200, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'WAREHOUSE'

    def __str__(self):
         return self.warehouse_name
    
class Customer(models.Model):
    customer_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    customer_name = models.CharField(max_length=150, null=False)
    phone_1 = models.BigIntegerField(default=0, null=False)
    phone_2 = models.BigIntegerField(default=0, null=False)
    email = models.CharField(max_length=50, default='', null=False)
    address = models.CharField(max_length=200, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'CUSTOMER'

    def __str__(self):
         return self.customer_name
    
class Suppliers(models.Model):
    supplier_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    supplier_type = models.CharField(max_length=50, default='', null=False)
    supplier_name = models.CharField(max_length=150, default='', null=False)
    phone_1 = models.BigIntegerField(default=0, null=False)
    phone_2 = models.BigIntegerField(default=0, null=False)
    email = models.CharField(max_length=50, default='', null=False)
    address = models.CharField(max_length=50, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'SUPPLIERS'

    def __str__(self):
         return self.supplier_name
    
class ProductGroup(models.Model):
    product_group_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    product_name = models.CharField(max_length=50, default='', null=False)
    product_image = models.ImageField(upload_to='products/images/', null=True, blank=True)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'PRODUCTGROUP'
    def __str__(self):
         return self.product_name    

class Products(models.Model):
    product_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, db_column='product_group_id')
    product_category_id = models.CharField(max_length=50, default='', null=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        db_column='category_fk_id',
        limit_choices_to={'category_type': 'PRODUCT_TYPE'}, 
        related_name='products',
        null=True,
        blank=True
    )

    
    product_name = models.CharField(max_length=50, default='', null=False)
    product_image = models.ImageField(upload_to='products/images/', null=True, blank=True)
    product_price = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    sale_price = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    unit_cost = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    discount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    tax = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    stock = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    flag_stock_out = models.CharField(max_length=1, default='', null=False)
    uom = models.CharField(max_length=10, default='', null=False)
    sku = models.CharField(max_length=50, default='', null=False)
    inv_class = models.CharField(max_length=1, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'PRODUCTS'
    def __str__(self):
         return self.product_name   
    

    def save(self, *args, **kwargs):
        
        if self.category:
            self.product_category_id = str(self.category.category_id)
        else:
            self.product_category_id = ''
        super().save(*args, **kwargs)
     




class Tables(models.Model):
    table_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    location = models.CharField(max_length=50, default='', null=False)
    no_of_seats = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'TABLES'

    def __str__(self):
         return self.location    

class Vehicle(models.Model):
    vehicle_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    vehicle_type = models.CharField(max_length=50, default='', null=False)
    vehicle_name = models.CharField(max_length=50, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'VEHCILE'
    def __str__(self):
         return self.vehicle_name


class Rooms(models.Model):
    room_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    room_type = models.CharField(max_length=50, default='', null=False)
    room_name = models.CharField(max_length=50, default='', null=False)
    location = models.CharField(max_length=50, default='', null=False)
    phone_1 = models.BigIntegerField(default=0, null=False)
    phone_2 = models.BigIntegerField(default=0, null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'ROOMS'

    def __str__(self):
         return self.room_name 
    
           
class InventoryHeader(models.Model):
    inventory_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, db_column='BUSINESSUNITID')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, db_column='BRANCHID')
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE, db_column='WAREHOUSEID')
    grnno = models.CharField(max_length=50, default='', null=True, blank=True)
    ref_type = models.CharField(max_length=50, default='', null=False, db_column='REFTYPE')
    ref_dt = models.DateField(default='1900-01-01', null=False, db_column='REFDT')
    ref_no = models.CharField(max_length=50, default='', null=False, db_column='REFNO')
    net_value = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False, db_column='NETVALUE')
    create_dt = models.DateField(auto_now_add=True, null=False, db_column='CREATEDT')
    create_tm = models.DateTimeField(auto_now_add=True, null=False, db_column='CREATETM')
    create_by = models.CharField(max_length=10, default='', null=False, db_column='CREATEBY')
    create_remarks = models.CharField(max_length=200, default='', null=False, db_column='CREATEREMARKS')
    update_dt = models.DateField(default='1900-01-01', null=False, db_column='UPDATEDT')
    update_tm = models.DateField(default='1900-01-01', null=False, db_column='UPDATETM')
    update_by = models.CharField(max_length=10, default='', null=False, db_column='UPDATEBY')
    update_marks = models.CharField(max_length=200, default='', null=False, db_column='UPDATEMARKS')

    class Meta:
        db_table = 'INVENTORYHEADER'

    def __str__(self):
        return str(self.inventory_id)
    
class InventoryLine(models.Model):
    inventory_line_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, db_column='branch_id')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_id')
    inventory = models.ForeignKey(InventoryHeader, on_delete=models.CASCADE, db_column='inventory_id')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    inventory_line_type = models.CharField(max_length=50, default='', null=False)
    qty = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    price = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    unit_cost = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    uom = models.CharField(max_length=10, default='', null=False)
    total_value = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    total_cost = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'INVENTORYLINE'

    def __str__(self):
         return self.inventory_line_type
    

class ChartOfAccounts(models.Model):
    account_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    account_code = models.CharField(max_length=50, default='', null=False)
    account_name = models.CharField(max_length=250, default='', null=False)
    account_type = models.CharField(max_length=250, default='', null=False)
    account_balance = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'CHARTOFACCOUNTS'
    def __str__(self):
        return self.account_name 
    def __str__(self):
         return self.account_code
    def __str__(self):
         return self.account_type   
    
      

class JournalEntries(models.Model):
    journal_entry_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    journal_entry_date = models.DateField(default='1900-01-01', null=False)
    description = models.CharField(max_length=250, default='', null=False)
    card_no = models.CharField(max_length=20, default='', blank=True)
    remarks = models.CharField(max_length=200, default='', blank=True)
    reference = models.CharField(max_length=50, default='', null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'JOURNALENTRIES'
    def __str__(self):
        return str(self.journal_entry_id)
        

class JournalEntryLine(models.Model):
    journal_entry_line_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    journal_entry = models.ForeignKey(JournalEntries, on_delete=models.CASCADE, db_column='journal_entry_id')
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, db_column='account_id')
    debit = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    credit = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)


    class Meta:
        db_table = 'JOURNALENTRYLINE'


  






class PurchaseOrders(models.Model):
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, db_column='branch_id')
    poid = models.BigAutoField(primary_key=True)
    supplier = models.ForeignKey('Suppliers', on_delete=models.CASCADE, db_column='SupplierID', default=0)
    order_date = models.DateField(default='1900-01-01')
    expected_delivery_date = models.DateField(default='1900-01-01')
    pono = models.CharField(max_length=50, default='', unique=True)
    postatus = models.CharField(max_length=20, default='')
    sub_total = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    tax_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    discount_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    total_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    remarks = models.CharField(max_length=200, default='')
    createdt = models.DateField(default=timezone.now)
    createtm = models.DateTimeField(default=timezone.now)
    createby = models.CharField(max_length=10, default='')
    createremarks = models.CharField(max_length=200, default='')
    updatedt = models.DateField(default='1900-01-01')
    updatetm = models.DateTimeField(default=datetime.datetime(1900, 1, 1))
    updateby = models.CharField(max_length=10, default='')
    updatemarks = models.CharField(max_length=200, default='')

    class Meta:
        db_table = 'PurchaseOrders'

    def __str__(self):
        return f"PO {self.pono} - {self.supplier}"

class PurchaseOrderItems(models.Model):
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, db_column='branch_id')
    item_id = models.AutoField(primary_key=True)
    poid = models.ForeignKey(PurchaseOrders, on_delete=models.CASCADE, db_column='POID', default=0)
    product = models.ForeignKey('Products', on_delete=models.CASCADE, db_column='product_id', default=0)
    quantity = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    discount_percent = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    tax_rate = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    line_total = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    remarks = models.CharField(max_length=200, default='')
    createdt = models.DateField(default=timezone.now)
    createtm = models.DateTimeField(default=timezone.now)
    createby = models.CharField(max_length=10, default='')
    createremarks = models.CharField(max_length=200, default='')
    updatedt = models.DateField(default='1900-01-01')
    updatetm = models.DateTimeField(default=datetime.datetime(1900, 1, 1))
    updateby = models.CharField(max_length=10, default='')
    updatemarks = models.CharField(max_length=200, default='')

    class Meta:
        db_table = 'PurchaseOrderItems'

    def __str__(self):
        return f"Item {self.item_id} for PO {self.poid}"





class SalesHeader(models.Model):
    sale_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, db_column='branch_id', default=0)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, db_column='customer_id')
    table = models.ForeignKey('Tables', on_delete=models.SET_NULL, null=True, blank=True, db_column='table_id')
    room = models.ForeignKey('Rooms', on_delete=models.SET_NULL, null=True, blank=True, db_column='room_id')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True, db_column='vehicle_id')
    sale_date = models.DateField(auto_now_add=True, null=False)
    sale_no = models.CharField(max_length=50, default='', null=False)
    total_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    payment_method = models.CharField(max_length=50, default='', null=False)
    discount_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    tax = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    tax_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    service_type = models.CharField(max_length=50, default='', null=False)
    service_id = models.BigIntegerField(default=0, null=False)
    payment_status = models.CharField(max_length=10, default='Unpaid')
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'SALESHEADER'

    def save(self, *args, **kwargs):
        if not self.pk or not self.sale_no or self.sale_no == '':
            target_date = timezone.now().date()
            
            daily_sales_count = SalesHeader.objects.filter(
                sale_date=target_date
            ).count()
            
            self.sale_no = str(daily_sales_count + 1)
        
        super().save(*args, **kwargs)

    @property
    def daily_sale_no(self):
        """Calculate daily sale number with date prefix (YYYYMMDD + sequential number)"""
        if not self.sale_date:
            return "20250101001"
        
        if self.sale_no and self.sale_no.isdigit():
            seq_num = self.sale_no.zfill(3)  
        else:
            earlier_sales = SalesHeader.objects.filter(
                sale_date=self.sale_date,
                sale_id__lt=self.sale_id if self.sale_id else 999999999
            ).count()
            seq_num = str(earlier_sales + 1).zfill(3)
        
        date_str = self.sale_date.strftime('%Y%m%d')
        return f"{date_str}{seq_num}"

    @property
    def get_sale_no(self):
        """Get the daily sale number for display"""
        return self.daily_sale_no

    def __str__(self):
        return self.daily_sale_no  
    
class SalesLine(models.Model):
    sale_line_id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, db_column='branch_id', default=0)
    sale = models.ForeignKey(SalesHeader, on_delete=models.CASCADE, db_column='sale_id')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='customer_id')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    sale_date = models.DateField(auto_now_add=True, null=False)
    qty = models.BigIntegerField(default=0, null=False)
    price = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    total_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    discount_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    tax = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    tax_amount = models.DecimalField(max_digits=22, decimal_places=3, default=0, null=False)
    create_dt = models.DateField(auto_now_add=True, null=False)
    create_tm = models.DateTimeField(auto_now_add=True, null=False)
    create_by = models.CharField(max_length=10, default='', null=False)
    create_remarks = models.CharField(max_length=200, default='', null=False)
    update_dt = models.DateField(default='1900-01-01', null=False)
    update_tm = models.DateField(default='1900-01-01', null=False)
    update_by = models.CharField(max_length=10, default='', blank=True)
    update_marks = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        db_table = 'SALESLINE'



class StockAdjustment(models.Model):
    id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, db_column='branch_id')
    product = models.ForeignKey('Products', on_delete=models.CASCADE, db_column='product_id', default=0)
    ref_id = models.BigIntegerField(default=0, db_column='REFID')
    ref_type = models.CharField(max_length=50, default='', db_column='REFTYPE')
    ref_no = models.CharField(max_length=50, default='', db_column='REFNO')
    remarks = models.CharField(max_length=50, default='')
    quantity = models.DecimalField(max_digits=22, decimal_places=3, default=0)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    createdt = models.DateField(default=timezone.now)
    createtm = models.DateTimeField(default=timezone.now)
    createby = models.CharField(max_length=10, default='')
    createremarks = models.CharField(max_length=200, default='')
    updatedt = models.DateField(default='1900-01-01')
    updatetm = models.DateTimeField(default=datetime.datetime(1900, 1, 1))
    updateby = models.CharField(max_length=10, default='')
    updatemarks = models.CharField(max_length=200, default='')

    class Meta:
        db_table = 'STOCKADJUSTMENT'

    def __str__(self):
        return f"Adjustment {self.id} - {self.ref_no}"
    


class SupplierPayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, db_column='business_unit_id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, db_column='branch_id')
    supplier = models.ForeignKey(Suppliers, on_delete=models.CASCADE, db_column='SupplierID')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=22, decimal_places=2)
    payment_ref = models.CharField(max_length=50)
    remarks = models.CharField(max_length=200, default='')
    createdt = models.DateField(default=timezone.now)
    createtm = models.DateTimeField(default=timezone.now)
    createby = models.CharField(max_length=10, default='')
    createremarks = models.CharField(max_length=200, default='')
    updatedt = models.DateField(default='1900-01-01')
    updatetm = models.DateTimeField(default=datetime.datetime(1900, 1, 1))
    updateby = models.CharField(max_length=10, default='')
    updatemarks = models.CharField(max_length=200, default='')


    class Meta:
        db_table = 'SUPPLIERPAYMENTS'

    def __str__(self):
        return f"Payment {self.payment_ref} - {self.supplier}"
