import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/seifeddine/dev/dcpManager')


# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcpmanager.settings')
django.setup()

from employees.models import Department

def create_departments():
    """Create sample departments for the dcpManager system"""
    
    departments = [
        {
            'name': 'Production',
            'description': 'Manufacturing and production operations, assembly lines, and quality control'
        },
        {
            'name': 'Quality Assurance',
            'description': 'Quality control, testing, inspection, and compliance management'
        },
        {
            'name': 'Maintenance',
            'description': 'Equipment maintenance, repair, preventive maintenance, and facility management'
        },
        {
            'name': 'Administration',
            'description': 'Administrative functions, human resources, and management operations'
        },
        {
            'name': 'Engineering',
            'description': 'Process engineering, design, research and development'
        },
        {
            'name': 'Logistics',
            'description': 'Supply chain management, inventory control, shipping and receiving'
        },
        {
            'name': 'Safety & Environment',
            'description': 'Workplace safety, environmental compliance, and health regulations'
        },
        {
            'name': 'IT Support',
            'description': 'Information technology support, system administration, and technical services'
        }
    ]
    
    created_count = 0
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'description': dept_data['description']}
        )
        if created:
            print(f"✓ Created department: {dept.name}")
            created_count += 1
        else:
            print(f"- Department already exists: {dept.name}")
    
    print(f"\nDepartment creation completed!")
    print(f"Created {created_count} new departments")
    print(f"Total departments: {Department.objects.count()}")

if __name__ == '__main__':
    create_departments()
