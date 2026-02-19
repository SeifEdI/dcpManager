from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import timedelta, datetime

class Department(models.Model):
    """Department model for organizing employees"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Employee(models.Model):
    """Extended employee profile linked to Django User"""
    
    EMPLOYEE_TYPES = [
        ('internal', 'Internal Employee'),
        ('external', 'External Authorized Person'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    employee_type = models.CharField(max_length=10, choices=EMPLOYEE_TYPES, default='internal')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def is_internal(self):
        return self.employee_type == 'internal'

    @property
    def is_external(self):
        return self.employee_type == 'external'


class Attendance(models.Model):
    """Attendance / pointage records. Designed for manual admin entry.

    - `date`: jour du pointage
    - `clock_in` / `clock_out`: heures d'entrée / sortie (optionnelles)
    - `duration`: durée totale (facultative, peut être calculée)
    - `created_by`: utilisateur ayant saisi l'enregistrement
    """

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True, help_text='Durée totale (optionnelle)')
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('employee', 'date'),)
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date}"

    @property
    def computed_duration(self):
        """Retourne la durée calculée entre `clock_in` et `clock_out` si `duration` absent."""
        if self.duration:
            return self.duration
        if self.clock_in and self.clock_out and self.date:
            dt_in = datetime.combine(self.date, self.clock_in)
            dt_out = datetime.combine(self.date, self.clock_out)
            if dt_out < dt_in:
                dt_out += timedelta(days=1)
            return dt_out - dt_in
        return None
