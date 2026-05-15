"""Invoice Forms"""
from django import forms
from .models import Invoice, InvoiceDocument
from apps.organisations.models import Organisation

INPUT_CLASS = 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors text-sm'


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['buyer', 'invoice_number', 'purchase_order_number', 'grn_number',
                  'currency', 'invoice_amount', 'invoice_date', 'due_date', 'description']
        widgets = {
            'buyer': forms.Select(attrs={'class': INPUT_CLASS}),
            'invoice_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. INV-1001'}),
            'purchase_order_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'PO number (optional)'}),
            'grn_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'GRN number (optional)'}),
            'currency': forms.Select(attrs={'class': INPUT_CLASS}),
            'invoice_amount': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '0.00', 'step': '0.01', 'min': '0.01'}),
            'invoice_date': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Description of goods/services'}),
        }

    def __init__(self, *args, supplier_org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['buyer'].queryset = Organisation.objects.filter(
            organisation_type='buyer', status='approved'
        )

    def clean_invoice_amount(self):
        amount = self.cleaned_data.get('invoice_amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Enter an amount greater than zero.')
        return amount

    def clean(self):
        cleaned = super().clean()
        invoice_date = cleaned.get('invoice_date')
        due_date = cleaned.get('due_date')
        if invoice_date and due_date and due_date <= invoice_date:
            self.add_error('due_date', 'Due date must be after the invoice date.')
        return cleaned


class InvoiceDocumentForm(forms.ModelForm):
    class Meta:
        model = InvoiceDocument
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': INPUT_CLASS}),
            'file': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': '.pdf,.jpg,.jpeg,.png,.docx,.xlsx'}),
        }
