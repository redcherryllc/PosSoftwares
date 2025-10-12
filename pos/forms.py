from django import forms
from .models import *

from django.forms import modelformset_factory

from django.contrib.auth.hashers import make_password
import re




class LoginForm(forms.Form):
    saas_username = forms.CharField(max_length=50, required=True)
    saas_user_password = forms.CharField(widget=forms.PasswordInput, required=True)




class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_name',
            'phone_1',
            'phone_2',
            'email',
            'address',
            'create_remarks'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_1': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone_2': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'create_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }





class ExpenseEntryForm(forms.Form):
    expense_account = forms.ModelChoiceField(queryset=ChartOfAccounts.objects.none(), label="Expense Account")
    payment_account = forms.ModelChoiceField(queryset=ChartOfAccounts.objects.none(), label="Payment Method")
    category = forms.ChoiceField(choices=[('COGS', 'Cost of Goods Sold'), ('Operating', 'Operating Expense'), ('Payroll', 'Payroll'), ('Other', 'Other')])
    amount = forms.DecimalField(max_digits=22, decimal_places=3, min_value=0.001)
    discount = forms.DecimalField(max_digits=22, decimal_places=3, min_value=0, initial=0)
    tax_amount = forms.DecimalField(max_digits=22, decimal_places=3, min_value=0, initial=0)
    expense_date = forms.DateField()
    description = forms.CharField(max_length=250)
    reference = forms.CharField(max_length=50)

    def __init__(self, business_unit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expense_account'].queryset = ChartOfAccounts.objects.filter(
            business_unit=business_unit, account_type__in=['Expense', 'Operating Expense', 'COGS']
        )
        self.fields['payment_account'].queryset = ChartOfAccounts.objects.filter(
            business_unit=business_unit, account_type='Asset', account_name__in=['Cash - Register', 'Bank - Operating', 'Petty Cash']
        )



class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ['product', 'ref_type', 'ref_no', 'quantity', 'unit_price', 'remarks']

    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        business_unit_id = kwargs.pop('business_unit_id', None)
        category_type = kwargs.pop('category_type', 'STOCK_ADJUST_TYPE')  
        super().__init__(*args, **kwargs)

        self.fields['quantity'].widget.attrs.update({'min': '-999999', 'max': '999999'})

        if products is not None:
            self.fields['product'].queryset = products

        if business_unit_id is not None:
            ref_types = Category.objects.filter(
                business_unit_id=business_unit_id,
                category_type=category_type
            ).values_list('category_value', 'category_name')
            self.fields['ref_type'] = forms.ChoiceField(
                choices=list(ref_types),  
                widget=forms.Select(attrs={'class': 'form-control'})
            )


            

class StockReportForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Products.objects.all(),
        label="Select Product",
        required=True
    )

    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        initial_product_id = kwargs.pop('initial_product_id', None)
        super().__init__(*args, **kwargs)
        
        if products is not None:
            self.fields['product'].queryset = products
        
        if initial_product_id:
            try:
                self.initial['product'] = Products.objects.get(product_id=initial_product_id)
            except Products.DoesNotExist:
                pass  






class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrders
        fields = ['supplier', 'order_date', 'expected_delivery_date', 'pono', 'tax_amount', 'total_amount', 'remarks']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_pono(self):
        pono = self.cleaned_data.get('pono')
        if pono and PurchaseOrders.objects.filter(pono=pono).exists():
            raise forms.ValidationError("This PO number already exists. Please use a different number.")
        return pono

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItems
        fields = ['product', 'quantity', 'unit_price', 'tax_rate']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        super().__init__(*args, **kwargs)
        if products is not None:
            self.fields['product'].queryset = products

PurchaseOrderItemFormSet = modelformset_factory(
    PurchaseOrderItems,
    form=PurchaseOrderItemForm,
    fields=['product', 'quantity', 'unit_price', 'tax_rate'],
    extra=1
)

    




class ProductGroupForm(forms.ModelForm):
    class Meta:
        model = ProductGroup
        fields = ['product_name', 'product_image']  
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class EditProductGroupForm(forms.ModelForm):
    class Meta:
        model = ProductGroup
        fields = ['product_name', 'product_image']  
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_image': forms.FileInput(attrs={'class': 'form-control'}),
        }




class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)
        if business_unit:
            self.fields['product_group'].queryset = ProductGroup.objects.filter(business_unit=business_unit)
            self.fields['category'].queryset = Category.objects.filter(
                category_type='PRODUCT_TYPE',
                business_unit_id=business_unit.business_unit_id
            )

    class Meta:
        model = Products
        fields = [
            'product_group', 'category', 'product_name', 'product_image',
            'product_price', 'sale_price', 'unit_cost', 'discount', 'tax',
            'stock', 'flag_stock_out', 'uom', 'sku', 'inv_class'
        ]
        widgets = {
            'product_group': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_image': forms.FileInput(attrs={'class': 'form-control'}),
            'product_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'flag_stock_out': forms.TextInput(attrs={'class': 'form-control'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'inv_class': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Suppliers
        fields = ['supplier_name', 'phone_1', 'phone_2', 'email', 'address']  # Exclude supplier_type
        widgets = {
            'supplier_name': forms.TextInput(attrs={'placeholder': 'Enter supplier name'}),
            'phone_1': forms.NumberInput(attrs={'placeholder': 'Enter primary phone'}),
            'phone_2': forms.NumberInput(attrs={'placeholder': 'Enter secondary phone'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'address': forms.TextInput(attrs={'placeholder': 'Enter address'}),
        }

    def clean_phone_1(self):
        phone_1 = self.cleaned_data['phone_1']
        if phone_1 < 0:
            raise forms.ValidationError("Phone number cannot be negative.")
        if len(str(phone_1)) > 15:
            raise forms.ValidationError("Phone number cannot exceed 15 digits.")
        return phone_1

    def clean_phone_2(self):
        phone_2 = self.cleaned_data['phone_2']
        if phone_2 < 0:
            raise forms.ValidationError("Phone number cannot be negative.")
        if len(str(phone_2)) > 15:
            raise forms.ValidationError("Phone number cannot exceed 15 digits.")
        return phone_2

    def clean_email(self):
        email = self.cleaned_data['email']
        if len(email) > 50:
            raise forms.ValidationError("Email cannot exceed 50 characters.")
        return email

    def save(self, commit=True):
        supplier = super().save(commit=False)
        supplier.supplier_type = 'cash'  # Set default supplier_type to 'cash'
        if commit:
            supplier.save()
        return supplier

class EditSupplierForm(SupplierForm):
    class Meta(SupplierForm.Meta):
        pass


class SupplierPaymentForm(forms.ModelForm):
    purchase_order = forms.ModelChoiceField(
        queryset=PurchaseOrders.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Purchase Order"
    )
    payment_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
        label="Payment Amount"
    )

    class Meta:
        model = SupplierPayment
        fields = ['purchase_order', 'payment_amount', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        purchase_order = cleaned_data.get('purchase_order')
        payment_amount = cleaned_data.get('payment_amount')

        if purchase_order and payment_amount:
    
            balance = purchase_order.balance_amount
            if payment_amount > balance:
                raise forms.ValidationError(
                    f"Payment amount ({payment_amount}) exceeds remaining balance ({balance})."
                )
            if payment_amount <= 0:
                raise forms.ValidationError("Payment amount must be greater than zero.")
        return cleaned_data    
    




class RoomForm(forms.ModelForm):
    class Meta:
        model = Rooms
        fields = ['room_type', 'room_name', 'location', 'phone_1', 'phone_2']
        widgets = {
            'room_type': forms.TextInput(attrs={'class': 'form-control'}),
            'room_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_1': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone_2': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)




class TableForm(forms.ModelForm):
    class Meta:
        model = Tables
        fields = ['location', 'no_of_seats']
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'no_of_seats': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_type', 'vehicle_name']
        widgets = {
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)






class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_type', 'category_value', 'category_name']
        widgets = {
            'category_type': forms.TextInput(attrs={'class': 'form-control'}),
            'category_value': forms.TextInput(attrs={'class': 'form-control'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)









class SAASUsersForm(forms.ModelForm):
    class Meta:
        model = SAASUsers
        fields = ['saas_username', 'saas_user_password']
        widgets = {
            'saas_username': forms.TextInput(attrs={'class': 'form-control'}),
            'saas_user_password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.saas_customer = kwargs.pop('saas_customer', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
       
        user.saas_user_password = self.cleaned_data['saas_user_password']
        if self.saas_customer:
            user.saas_customer = self.saas_customer
        if commit:
            user.save()
        return user



class BusinessUnitGroupForm(forms.ModelForm):
    class Meta:
        model = BusinessUnitGroup
        fields = ['business_unit_group_name']  
        widgets = {
            'business_unit_group_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.saas_customer = kwargs.pop('saas_customer', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        group = super().save(commit=False)
        if self.saas_customer:
            group.saas_customer = self.saas_customer
        if commit:
            group.save()
        return group

class BusinessUnitForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = ['business_unit_name', 'business_unit_currency', 'phone_1', 'phone_2', 'email', 'business_unit_group', 'address']
        widgets = {
            'business_unit_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_unit_currency': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_1': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone_2': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'business_unit_group': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        saas_customer = kwargs.pop('saas_customer', None)
        super().__init__(*args, **kwargs)
        if saas_customer:
            self.fields['business_unit_group'].queryset = BusinessUnitGroup.objects.filter(saas_customer=saas_customer)
            if self.fields['business_unit_group'].queryset.count() == 1:
                self.fields['business_unit_group'].initial = self.fields['business_unit_group'].queryset.first()
                self.fields['business_unit_group'].widget.attrs['readonly'] = True

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['branch_name', 'phone_1', 'phone_2', 'email', 'address']  
        widgets = {
            'branch_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_1': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone_2': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        branch = super().save(commit=False)
        if self.business_unit:
            branch.business_unit = self.business_unit
        if commit:
            branch.save()
        return branch

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['warehouse_name', 'branch', 'address'] 
        widgets = {
            'warehouse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)
        if self.business_unit:
            self.fields['branch'].queryset = Branch.objects.filter(business_unit=self.business_unit)

    def save(self, commit=True):
        warehouse = super().save(commit=False)
        if self.business_unit:
            warehouse.business_unit = self.business_unit
        if commit:
            warehouse.save()
        return warehouse










class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'phone_1', 'phone_2', 'email', 'aadhaar_card_no', 'national_id', 'passport_no', 'address']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter customer name',
                'required': 'required'
            }),
            'phone_1': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter primary phone number',
                'pattern': '[0-9]{10,15}',
                'required': 'required'
            }),
            'phone_2': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter secondary phone number ',
                'pattern': '[0-9]{10,15}'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter email address '
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Enter address '
            }),
            'aadhaar_card_no': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter 12-digit Aadhaar number ',
                'pattern': '[0-9]{12}',
                'maxlength': '12'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter national ID '
            }),
            'passport_no': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter passport number '
            }),
        }
        labels = {
            'customer_name': 'Customer Name *',
            'phone_1': 'Phone Number (Primary) *',
            'phone_2': 'Phone Number (Secondary)',
            'email': 'Email',
            'aadhaar_card_no': 'Aadhaar Number',
            'national_id': 'National ID',
            'passport_no': 'Passport Number',
            'address': 'Address',
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)
        
       
        self.fields['phone_2'].required = False
        self.fields['email'].required = False
        self.fields['address'].required = False
        self.fields['aadhaar_card_no'].required = False
        self.fields['national_id'].required = False
        self.fields['passport_no'].required = False

    def clean_customer_name(self):
        customer_name = self.cleaned_data.get('customer_name', '').strip()
        if not customer_name:
            raise forms.ValidationError("Customer name is required.")
        return customer_name

    def clean_phone_1(self):
        phone_1 = self.cleaned_data.get('phone_1', '').strip()
        if not phone_1:
            raise forms.ValidationError("Primary phone number is required.")
        
        
        phone_digits = re.sub(r'\D', '', phone_1)
        if not (10 <= len(phone_digits) <= 15):
            raise forms.ValidationError("Phone number must be between 10 and 15 digits.")
        
        
        if self.business_unit:
            existing = Customer.objects.filter(
                business_unit=self.business_unit, 
                phone_1=phone_1
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError("This phone number already exists for this business unit.")
        
        return phone_1

    def clean_phone_2(self):
        phone_2 = self.cleaned_data.get('phone_2', '').strip()
        if phone_2:  
            phone_digits = re.sub(r'\D', '', phone_2)
            if not (10 <= len(phone_digits) <= 15):
                raise forms.ValidationError("Phone number must be between 10 and 15 digits.")
        return phone_2

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        
        return email

    def clean_aadhaar_card_no(self):
        aadhaar = self.cleaned_data.get('aadhaar_card_no', '').strip()
        if aadhaar:  
            if not re.match(r'^\d{12}$', aadhaar):
                raise forms.ValidationError("Aadhaar number must be exactly 12 digits.")
        return aadhaar

    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id', '').strip()
        return national_id

    def clean_passport_no(self):
        passport_no = self.cleaned_data.get('passport_no', '').strip()
        return passport_no

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        return address
    

    



class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = [
            'customer', 'phone1', 'booking_agent_code', 'booking_agent_dt',
            'booking_agent_ref_no', 'start_dt', 'end_dt', 'start_tm', 'end_tm',
            'room', 'no_of_rooms', 'no_of_guest', 'unit_price', 'booking_dt',
            'booking_status'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'booking_agent_code': forms.TextInput(attrs={'class': 'form-control'}),
            'booking_agent_dt': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'booking_agent_ref_no': forms.TextInput(attrs={'class': 'form-control'}),
            'start_dt': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_dt': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_tm': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_tm': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'no_of_rooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'no_of_guest': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'booking_dt': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'booking_status': forms.Select(
                attrs={'class': 'form-control'},
                choices=[
                    ('00', 'Booked'),
                    ('10', 'Confirmed'),
                    ('20', 'Occupied'),
                    ('40', 'Cancelled'),
                    ('50', 'Released'),
                ]
            ),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)
        if self.business_unit:
            self.fields['customer'].queryset = Customer.objects.filter(business_unit=self.business_unit)
            self.fields['room'].queryset = Rooms.objects.filter(business_unit=self.business_unit)

    def save(self, commit=True):
        registration = super().save(commit=False)
        if self.business_unit:
            registration.business_unit = self.business_unit
        if commit:
            registration.save()
        return registration
    
    


class AuthorityForm(forms.ModelForm):
    class Meta:
        model = Authority
        fields = ['au_type', 'saas_username', 'au_menu', 'au_submenu', 'au_menu_text', 'au_submenu_text', 'au_status']
        widgets = {
            'au_type': forms.TextInput(attrs={'class': 'form-control'}),
            'saas_username': forms.TextInput(attrs={'class': 'form-control'}),
            'au_menu': forms.TextInput(attrs={'class': 'form-control'}),
            'au_submenu': forms.TextInput(attrs={'class': 'form-control'}),
            'au_menu_text': forms.TextInput(attrs={'class': 'form-control'}),
            'au_submenu_text': forms.TextInput(attrs={'class': 'form-control'}),
            'au_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.business_unit = kwargs.pop('business_unit', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.au_status:
            self.fields['au_status'].initial = True
        else:
            self.fields['au_status'].initial = False

    def save(self, commit=True):
        authority = super().save(commit=False)
        if self.business_unit:
            authority.business_unit = self.business_unit
        authority.au_status = self.cleaned_data.get('au_status', False)
        if commit:
            authority.save()
        return authority

class SAASUserForm(forms.Form):
    
    saas_username = forms.ModelChoiceField(
        queryset=SAASUsers.objects.none(),
        empty_label="Select User",
        label="Select Existing User",
        to_field_name='saas_user_id',  
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    
    add_new_user = forms.ModelChoiceField(
        queryset=SAASUsers.objects.none(),
        empty_label="Select User to Add",
        label="Add Other Existing User",
        to_field_name='saas_username',  
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, business_unit_id=None, logged_in_username=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if business_unit_id and logged_in_username:
            try:
                
                business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
                saas_customer = business_unit.business_unit_group.saas_customer

                
                authority_usernames = Authority.objects.filter(
                    business_unit_id=business_unit_id
                ).values_list('saas_username', flat=True).distinct()
                
                
                self.fields['saas_username'].queryset = SAASUsers.objects.filter(
                    saas_username__in=authority_usernames
                ).order_by('saas_username')
                
                
                self.fields['add_new_user'].queryset = SAASUsers.objects.filter(
                    saas_customer=saas_customer
                ).exclude(
                    saas_username__in=authority_usernames
                ).exclude(
                    saas_username=logged_in_username
                ).order_by('saas_username')
                
            except (BusinessUnit.DoesNotExist, AttributeError) as e:
                
                self.fields['saas_username'].queryset = SAASUsers.objects.none()
                self.fields['add_new_user'].queryset = SAASUsers.objects.none()