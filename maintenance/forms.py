from django import forms
from .models import Asset, AssetCategory, MaintenanceSchedule, WorkOrder, WorkOrderComment, MaintenanceLog, TechnicalDatasheet


class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'asset_id', 'name', 'category', 'description', 'location',
            'serial_number', 'manufacturer', 'model_number',
            'purchase_date', 'warranty_expiry',
            'status', 'criticality', 'assigned_to', 'notes',
        ]
        widgets = {
            'asset_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AST-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Building / Floor / Room'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'criticality': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceScheduleForm(forms.ModelForm):
    class Meta:
        model = MaintenanceSchedule
        fields = [
            'asset', 'title', 'description', 'frequency', 'custom_interval_days',
            'last_performed', 'next_due', 'assigned_to', 'is_active',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'custom_interval_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'last_performed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_due': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        custom_days = cleaned_data.get('custom_interval_days')
        if frequency == 'custom' and not custom_days:
            self.add_error('custom_interval_days', 'Please specify the interval in days for custom frequency.')
        return cleaned_data


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'title', 'description', 'work_type', 'priority', 'status',
            'asset', 'schedule', 'assigned_to', 'due_date',
            'estimated_hours', 'actual_hours',
            'resolution_notes', 'parts_used',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'work_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'schedule': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'actual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parts_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class WorkOrderCommentForm(forms.ModelForm):
    class Meta:
        model = WorkOrderComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment or update…',
            }),
        }


class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = [
            'performed_by', 'performed_at', 'summary',
            'findings', 'recommendations', 'next_maintenance_date', 'cost',
        ]
        widgets = {
            'performed_by': forms.Select(attrs={'class': 'form-select'}),
            'performed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'findings': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class WorkOrderFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + WorkOrder.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priorities')] + WorkOrder.PRIORITY_CHOICES
    TYPE_CHOICES = [('', 'All Types')] + WorkOrder.TYPE_CHOICES

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False,
                               widget=forms.Select(attrs={'class': 'form-select'}))
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False,
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    work_type = forms.ChoiceField(choices=TYPE_CHOICES, required=False,
                                  widget=forms.Select(attrs={'class': 'form-select'}))
    search = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search…'}))
    date_from = forms.DateField(required=False,
                                widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False,
                              widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))


class AssetFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + Asset.STATUS_CHOICES
    CRITICALITY_CHOICES = [('', 'All Criticalities')] + Asset.CRITICALITY_CHOICES

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False,
                               widget=forms.Select(attrs={'class': 'form-select'}))
    criticality = forms.ChoiceField(choices=CRITICALITY_CHOICES, required=False,
                                    widget=forms.Select(attrs={'class': 'form-select'}))
    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    search = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search…'}))


class TechnicalDatasheetForm(forms.ModelForm):
    class Meta:
        model = TechnicalDatasheet
        fields = ['title', 'document_type', 'file', 'version', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Motor Datasheet v2'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.svg,.dwg,.dxf',
            }),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. v1.0, Rev A'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes…'}),
        }

