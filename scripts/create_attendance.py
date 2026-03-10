import os
import sys
from datetime import datetime
import django

# Add the project directory to Python path
sys.path.append('/home/seifeddine/dev/dcpManager')


# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcpmanager.settings')
django.setup()

from employees.models import Attendance, Employee

def create_attendance():
    """Create sample attendance records for the dcpManager system"""
    
    employees = Employee.objects.all()
    
    if not employees.exists():
        print("No employees found. Please create employees first.")
        return
    
    # Create sample attendance records
    attendance_records = [
        {
            'employee': employees[4],
            'date': '2026-02-03',
            'clock_in': '08:00:00',
            'clock_out' : '15:15:00'
        },
     
    ]
    print(employees[0])
    print(employees[1])
    print(employees[2])
    print(employees[3])
    print(employees[4])
    print(employees[5])


    for record in attendance_records:
        attendance, created = Attendance.objects.get_or_create(
            employee=record['employee'],
            date=record['date'],
            clock_in = record['clock_in'],
            clock_out = record['clock_out'],
            created_by = employees[3],
            note = 'Hello',

        )
        if created:
            print(f"Created attendance record for {attendance.employee} on {attendance.date}")
        else:
            print(f"Attendance record for {attendance.employee} on {attendance.date} already exists")
    
    

if __name__ == '__main__':
    create_attendance()
