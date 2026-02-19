from django.urls import path
from . import views

app_name = 'rbac'

urlpatterns = [
    path('roles/', views.role_list, name='role_list'),
    path('roles/<int:role_id>/', views.role_detail, name='role_detail'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/roles/', views.user_roles, name='user_roles'),
    path('my-permissions/', views.my_permissions, name='my_permissions'),
]
