from django import forms
from django.contrib.auth.models import User
from .models import Role, Permission, UserRole

class RoleForm(forms.ModelForm):
    """Form for creating and editing roles"""
    
    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permissions': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Group permissions by module for better display
        self.fields['permissions'].queryset = Permission.objects.all().order_by('module', 'name')

class AssignRoleForm(forms.Form):
    """Form for assigning roles to users"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select User"
    )
    
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Role"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order users by name for better UX
        self.fields['user'].queryset = User.objects.all().order_by('first_name', 'last_name', 'username')
