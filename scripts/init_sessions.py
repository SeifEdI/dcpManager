#!/usr/bin/env python
"""
Initialize the user sessions system for dcpManager
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcpmanager.settings')
django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rbac.models import Role, UserRole
from user_sessions.models import ActiveSession, SessionStatistics

def main():
    print("🚀 Initializing User Sessions System...")
    
    # Create permissions for session management
    print("📋 Creating session permissions...")
    
    # Get content types
    session_ct = ContentType.objects.get_for_model(ActiveSession)
    stats_ct = ContentType.objects.get_for_model(SessionStatistics)
    
    # Create custom permissions
    permissions_to_create = [
        ('view_connected_users', 'Can view connected users', session_ct),
        ('manage_user_sessions', 'Can manage user sessions', session_ct),
        ('force_logout_users', 'Can force logout users', session_ct),
        ('view_session_statistics', 'Can view session statistics', stats_ct),
    ]
    
    created_permissions = []
    for codename, name, content_type in permissions_to_create:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={'name': name}
        )
        if created:
            created_permissions.append(permission)
            print(f"  ✅ Created permission: {name}")
        else:
            print(f"  ℹ️  Permission already exists: {name}")
    
    # Add session permissions to existing roles
    print("\n🔐 Adding session permissions to roles...")
    
    try:
        # Add to Admin role
        admin_role = Role.objects.get(name='Admin')
        session_permissions = Permission.objects.filter(
            codename__in=[
                'view_connected_users',
                'manage_user_sessions', 
                'force_logout_users',
                'view_session_statistics',
                'view_activesession',
                'add_activesession',
                'change_activesession',
                'delete_activesession',
            ]
        )
        admin_role.permissions.add(*session_permissions)
        print("  ✅ Added session permissions to Admin role")
        
        # Add limited permissions to Manager role
        manager_role = Role.objects.get(name='Manager')
        manager_permissions = Permission.objects.filter(
            codename__in=[
                'view_connected_users',
                'view_session_statistics',
                'view_activesession',
            ]
        )
        manager_role.permissions.add(*manager_permissions)
        print("  ✅ Added view permissions to Manager role")
        
    except Role.DoesNotExist:
        print("  ⚠️  Default roles not found. Please run init_rbac.py first.")
    
    # Clean up any existing expired sessions
    print("\n🧹 Cleaning up expired sessions...")
    from user_sessions.utils import SessionManager
    session_manager = SessionManager()
    session_manager.cleanup_expired_sessions()
    print("  ✅ Expired sessions cleaned up")
    
    # Create initial session statistics entry
    print("\n📊 Initializing session statistics...")
    from datetime import date
    today = date.today()
    stats, created = SessionStatistics.objects.get_or_create(
        date=today,
        defaults={
            'total_sessions': 0,
            'unique_users': 0,
            'peak_concurrent': 0,
            'mobile_sessions': 0,
            'desktop_sessions': 0,
        }
    )
    if created:
        print("  ✅ Created initial session statistics")
    else:
        print("  ℹ️  Session statistics already exist for today")
    
    print("\n🎉 User Sessions System initialization completed!")
    print("\nNext steps:")
    print("1. Run: python manage.py makemigrations user_sessions")
    print("2. Run: python manage.py migrate")
    print("3. Restart your Django development server")
    print("4. Navigate to /sessions/connected-users/ to view connected users")
    
    print("\n📋 Available URLs:")
    print("  • /sessions/connected-users/ - View all connected users")
    print("  • /sessions/my-sessions/ - View your own sessions")
    print("  • /sessions/api/connected-users/ - API endpoint for connected users")
    print("  • /sessions/api/statistics/ - API endpoint for session statistics")

if __name__ == '__main__':
    main()
