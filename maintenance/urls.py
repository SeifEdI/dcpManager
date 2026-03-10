from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/add/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),

    # Datasheets
    path('assets/<int:asset_pk>/datasheets/upload/', views.datasheet_upload, name='datasheet_upload'),
    path('datasheets/<int:pk>/delete/', views.datasheet_delete, name='datasheet_delete'),

    # Work Orders
    path('work-orders/', views.work_order_list, name='work_order_list'),
    path('work-orders/create/', views.work_order_create, name='work_order_create'),
    path('work-orders/<int:pk>/', views.work_order_detail, name='work_order_detail'),
    path('work-orders/<int:pk>/edit/', views.work_order_edit, name='work_order_edit'),
    path('work-orders/<int:pk>/complete/', views.work_order_complete, name='work_order_complete'),
    path('work-orders/<int:pk>/delete/', views.work_order_delete, name='work_order_delete'),

    # Maintenance Schedules
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
]
