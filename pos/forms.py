from django import forms
from .models import *

from django.forms import modelformset_factory


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