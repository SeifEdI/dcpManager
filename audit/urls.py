from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('dashboard/', views.audit_dashboard, name='dashboard'),
    path('logs/', views.audit_logs, name='logs'),
    path('employee-access/', views.employee_access_logs, name='employee_access_logs'),
    path('security-events/', views.security_events, name='security_events'),
    path('my-activity/', views.my_activity, name='my_activity'),
]
