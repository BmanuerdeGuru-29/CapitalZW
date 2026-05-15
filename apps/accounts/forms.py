"""
Account Forms - Registration, Login, User Management
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import get_user_model
from apps.organisations.models import Organisation

User = get_user_model()

ACCOUNT_TYPE_CHOICES = [
    ('supplier', 'Supplier'),
    ('buyer', 'Buyer'),
    ('financier', 'Financier'),
]

SECTOR_CHOICES = [
    ('', 'Select sector'),
    ('agriculture', 'Agriculture'),
    ('construction', 'Construction'),
    ('manufacturing', 'Manufacturing'),
    ('mining', 'Mining'),
    ('retail', 'Retail'),
    ('services', 'Services'),
    ('technology', 'Technology'),
    ('finance', 'Finance'),
    ('healthcare', 'Healthcare'),
    ('education', 'Education'),
    ('transport', 'Transport & Logistics'),
    ('energy', 'Energy'),
    ('food', 'Food & Beverages'),
    ('other', 'Other'),
]

INPUT_CLASS = 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors text-sm'
SELECT_CLASS = INPUT_CLASS


class RegistrationForm(forms.Form):
    """Multi-step registration form for suppliers, buyers, and financiers."""
    # Account type
    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )

    # Personal info
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Email address'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+263...'})
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Create password'})
    )
    password_confirm = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Confirm password'})
    )

    # Organisation info
    organisation_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Registered company name'})
    )
    trading_name = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Trading name (if different)'})
    )
    registration_number = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Company registration number'})
    )
    sector = forms.ChoiceField(
        choices=SECTOR_CHOICES,
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'City'})
    )
    country = forms.CharField(
        max_length=100, initial='Zimbabwe',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Country'})
    )
    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Organisation contact email'})
    )
    contact_phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Organisation contact phone'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter your password',
        })
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }


class AdminUserForm(forms.ModelForm):
    """Form for admin to manage users."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'role', 'is_active', 'organisation']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'role': forms.Select(attrs={'class': SELECT_CLASS}),
            'organisation': forms.Select(attrs={'class': SELECT_CLASS}),
        }
