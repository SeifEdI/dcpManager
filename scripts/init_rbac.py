import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/seifeddine/dev/dcpManager')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcpmanager.settings')
django.setup()

from rbac.utils import RBACManager
from django.contrib.auth.models import User

def initialize_rbac():
    """Initialize the RBAC system with default permissions and roles"""
    
    print("🚀 Initializing RBAC System...")
    
    # Create default permissions
    print("\n📋 Creating default permissions...")
    permissions = RBACManager.create_default_permissions()
    print(f"✅ Created {len(permissions)} new permissions")
    
    # Create default roles
    print("\n👥 Creating default roles...")
    roles = RBACManager.create_default_roles()
    print(f"✅ Created {len(roles)} new roles")
    
    # Assign Super Administrator role to existing superusers
    print("\n🔐 Assigning roles to existing users...")
    superusers = User.objects.filter(is_superuser=True)
    for user in superusers:
        user_role = RBACManager.assign_role_to_user(user, 'Super Administrator')
        if user_role:
            print(f"✅ Assigned 'Super Administrator' role to {user.username}")
    
    # Assign Employee role to existing non-staff users
    regular_users = User.objects.filter(is_superuser=False, is_staff=False)
    for user in regular_users:
        user_role = RBACManager.assign_role_to_user(user, 'Employee')
        if user_role:
            print(f"✅ Assigned 'Employee' role to {user.username}")
    
    # Assign HR Manager role to existing staff users (non-superuser)
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    for user in staff_users:
        user_role = RBACManager.assign_role_to_user(user, 'HR Manager')
        if user_role:
            print(f"✅ Assigned 'HR Manager' role to {user.username}")
    
    print("\n🎉 RBAC System initialization completed!")
    print("\n📊 Summary:")
    print(f"   • Total Permissions: {len(RBACManager.create_default_permissions()) + len(permissions)}")
    print(f"   • Total Roles: {len(RBACManager.create_default_roles())}")
    print(f"   • Users with roles: {User.objects.filter(user_roles__isnull=False).distinct().count()}")
    
    print("\n🔑 Default Roles Created:")
    print("   • Super Administrator - Full system access")
    print("   • HR Manager - Employee management capabilities")
    print("   • HR Assistant - Limited employee management")
    print("   • Department Manager - View access to employees")
    print("   • Employee - Basic dashboard access")
    print("   • Viewer - Read-only access")
    
    print("\n💡 Next Steps:")
    print("   1. Login to the admin panel to fine-tune roles and permissions")
    print("   2. Use the RBAC management interface to assign roles to users")
    print("   3. Test the permission system with different user accounts")

if __name__ == '__main__':
    initialize_rbac()
