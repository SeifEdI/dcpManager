from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('add/', views.add_employee, name='add'),
    path('export/csv/',views.export_employees_csv, name='export_csv'),
    path('print/pdf/',views.print_employees_pdf,name='print_pdf'),
    path('profile/', views.employee_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('<int:employee_id>/', views.employee_detail, name='detail'),
    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/add/', views.attendance_create, name='attendance_add'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
]
