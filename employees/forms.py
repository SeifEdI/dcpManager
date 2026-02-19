from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Employee, Department
import re

class EmployeeProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = Employee
        fields = ['phone_number', 'department', 'position']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+1234567890'}),
            'position': forms.TextInput(attrs={'placeholder': 'Your job title'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
        
        # Only show departments for internal employees
        if self.instance and self.instance.employee_type == 'external':
            self.fields['department'].widget = forms.HiddenInput()
            self.fields['department'].required = False

class AddEmployeeForm(forms.Form):
    """Form for adding new employees with user account creation"""
    
    # User account fields
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        }),
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        help_text='Your password must contain at least 8 characters.'
    )
    
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        help_text='Enter the same password as before, for verification.'
    )
    
    # Employee profile fields
    employee_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., EMP001, EXT001'
        }),
        help_text='Unique employee identifier'
    )
    
    employee_type = forms.ChoiceField(
        choices=Employee.EMPLOYEE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='internal'
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Select Department",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    position = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Job title or position'
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        }),
        help_text='Phone number in international format'
    )
    
    hire_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    status = forms.ChoiceField(
        choices=Employee.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='active'
    )
    
    is_staff = forms.BooleanField(
        required=False,
        label='Staff status',
        help_text='Designates whether the user can log into the admin site.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('A user with that username already exists.')
        return username
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if Employee.objects.filter(employee_id=employee_id).exists():
            raise ValidationError('An employee with that ID already exists.')
        return employee_id
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if phone_number:
            # Validate phone number format
            phone_regex = re.compile(r'^\+?1?\d{9,15}$')
            if not phone_regex.match(phone_number):
                raise ValidationError('Phone number must be in format: +999999999. Up to 15 digits allowed.')
        return phone_number
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        employee_type = cleaned_data.get('employee_type')
        department = cleaned_data.get('department')
        
        # Check password match
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('The two password fields didn\'t match.')
        
        # Validate department for internal employees
        if employee_type == 'internal' and not department:
            self.add_error('department', 'Department is required for internal employees.')
        
        return cleaned_data
