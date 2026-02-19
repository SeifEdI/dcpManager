# Database initialization script for dcpmanager
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/seifeddine/dev/dcpManager')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcpmanager.settings')
django.setup()

from django.contrib.auth.models import User
from employees.models import Employee, Department

def create_sample_data():
    """Create sample departments and users for testing"""
    
    # Create departments
    departments = [
        {'name': 'Production', 'description': 'Manufacturing and production operations'},
        {'name': 'Quality Control', 'description': 'Quality assurance and testing'},
        {'name': 'Maintenance', 'description': 'Equipment maintenance and repair'},
        {'name': 'Administration', 'description': 'Administrative and management functions'},
    ]
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'description': dept_data['description']}
        )
        if created:
            print(f"Created department: {dept.name}")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'System',
            'last_name': 'Administrator',
            'email': 'admin@dcpmanager.local',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("Created admin user (username: admin, password: admin123)")
    
    # Create admin employee profile
    admin_employee, created = Employee.objects.get_or_create(
        user=admin_user,
        defaults={
            'employee_id': 'ADM001',
            'employee_type': 'internal',
            'department': Department.objects.get(name='Administration'),
            'position': 'System Administrator',
            'status': 'active',
        }
    )
    if created:
        print("Created admin employee profile")
    
    # Create sample internal employee
    internal_user, created = User.objects.get_or_create(
        username='john.doe',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@dcpmanager.local',
        }
    )
    if created:
        internal_user.set_password('password123')
        internal_user.save()
        print("Created internal employee user (username: john.doe, password: password123)")
    
    internal_employee, created = Employee.objects.get_or_create(
        user=internal_user,
        defaults={
            'employee_id': 'EMP001',
            'employee_type': 'internal',
            'department': Department.objects.get(name='Production'),
            'position': 'Production Supervisor',
            'phone_number': '+1234567890',
            'status': 'active',
        }
    )
    if created:
        print("Created internal employee profile")
    
    # Create sample external user
    external_user, created = User.objects.get_or_create(
        username='jane.smith',
        defaults={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@external.com',
        }
    )
    if created:
        external_user.set_password('password123')
        external_user.save()
        print("Created external user (username: jane.smith, password: password123)")
    
    external_employee, created = Employee.objects.get_or_create(
        user=external_user,
        defaults={
            'employee_id': 'EXT001',
            'employee_type': 'external',
            'position': 'Quality Consultant',
            'phone_number': '+0987654321',
            'status': 'active',
        }
    )
    if created:
        print("Created external employee profile")

if __name__ == '__main__':
    create_sample_data()
    print("\nDatabase initialization completed!")
    print("\nSample login credentials:")
    print("Admin: username=admin, password=admin123")
    print("Internal Employee: username=john.doe, password=password123")
    print("External User: username=jane.smith, password=password123")
