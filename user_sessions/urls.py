from django.urls import path
from . import views

app_name = 'user_sessions'

urlpatterns = [
    path('connected-users/', views.connected_users, name='connected_users'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/logout/', views.force_logout, name='force_logout'),
    path('my-sessions/', views.my_sessions, name='my_sessions'),
    
    # API endpoints
    path('api/connected-users/', views.api_connected_users, name='api_connected_users'),
    path('api/statistics/', views.api_statistics, name='api_statistics'),
    path('debug/', views.debug_sessions, name='debug_sessions'), # Debug view for development
]
