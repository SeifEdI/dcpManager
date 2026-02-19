from .models import Permission, Role, UserRole
from django.contrib.auth.models import User

class RBACManager:
    """Utility class for managing RBAC operations"""
    
    @staticmethod
    def create_default_permissions():
        """Create default permissions for the system"""
        default_permissions = [
            # Dashboard permissions
            ('dashboard.view', 'View Dashboard', 'dashboard', 'Can view the main dashboard'),
            ('dashboard.view_analytics', 'View Analytics', 'dashboard', 'Can view dashboard analytics and charts'),
            
            # Employee permissions
            ('employees.view', 'View Employees', 'employees', 'Can view employee list and details'),
            ('employees.add', 'Add Employees', 'employees', 'Can add new employees'),
            ('employees.edit', 'Edit Employees', 'employees', 'Can edit employee information'),
            ('employees.delete', 'Delete Employees', 'employees', 'Can delete employees'),
            ('employees.export', 'Export Employees', 'employees', 'Can export employee data'),
            ('employees.import', 'Import Employees', 'employees', 'Can import employee data'),
            ('employees.view_sensitive', 'View Sensitive Data', 'employees', 'Can view sensitive employee information'),
            
            # Department permissions
            ('departments.view', 'View Departments', 'departments', 'Can view department information'),
            ('departments.manage', 'Manage Departments', 'departments', 'Can add, edit, and delete departments'),
            
            # User management permissions
            ('users.view', 'View Users', 'users', 'Can view user accounts'),
            ('users.manage', 'Manage Users', 'users', 'Can manage user accounts and roles'),
            ('users.assign_roles', 'Assign Roles', 'users', 'Can assign roles to users'),
            
            # System permissions
            ('system.admin', 'System Administration', 'system', 'Full system administration access'),
            ('system.settings', 'System Settings', 'system', 'Can modify system settings'),
            ('system.logs', 'View System Logs', 'system', 'Can view system logs and audit trails'),
            
            # Reports permissions
            ('reports.view', 'View Reports', 'reports', 'Can view generated reports'),
            ('reports.generate', 'Generate Reports', 'reports', 'Can generate new reports'),
            ('reports.schedule', 'Schedule Reports', 'reports', 'Can schedule automated reports'),
        ]
        
        created_permissions = []
        for codename, name, module, description in default_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'module': module,
                    'description': description
                }
            )
            if created:
                created_permissions.append(permission)
        
        return created_permissions
    
    @staticmethod
    def create_default_roles():
        """Create default roles with appropriate permissions"""
        # Ensure permissions exist
        RBACManager.create_default_permissions()
        
        default_roles = [
            {
                'name': 'Super Administrator',
                'description': 'Full system access with all permissions',
                'permissions': Permission.objects.all()
            },
            {
                'name': 'HR Manager',
                'description': 'Human Resources manager with employee management capabilities',
                'permissions': Permission.objects.filter(
                    codename__in=[
                        'dashboard.view', 'dashboard.view_analytics',
                        'employees.view', 'employees.add', 'employees.edit', 'employees.export',
                        'employees.view_sensitive', 'departments.view', 'departments.manage',
                        'reports.view', 'reports.generate'
                    ]
                )
            },
            {
                'name': 'HR Assistant',
                'description': 'HR assistant with limited employee management',
                'permissions': Permission.objects.filter(
                    codename__in=[
                        'dashboard.view', 'employees.view', 'employees.add', 'employees.edit',
                        'departments.view', 'reports.view'
                    ]
                )
            },
            {
                'name': 'Department Manager',
                'description': 'Department manager with view access to employees',
                'permissions': Permission.objects.filter(
                    codename__in=[
                        'dashboard.view', 'employees.view', 'departments.view', 'reports.view'
                    ]
                )
            },
            {
                'name': 'Employee',
                'description': 'Regular employee with basic access',
                'permissions': Permission.objects.filter(
                    codename__in=['dashboard.view']
                )
            },
            {
                'name': 'Viewer',
                'description': 'Read-only access to employee information',
                'permissions': Permission.objects.filter(
                    codename__in=['dashboard.view', 'employees.view', 'departments.view']
                )
            }
        ]
        
        created_roles = []
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            if created or not role.permissions.exists():
                role.permissions.set(role_data['permissions'])
                created_roles.append(role)
        
        return created_roles
    
    @staticmethod
    def assign_role_to_user(user, role_name, assigned_by=None):
        """Assign a role to a user"""
        try:
            role = Role.objects.get(name=role_name, is_active=True)
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={'assigned_by': assigned_by}
            )
            if not created:
                user_role.is_active = True
                user_role.save()
            return user_role
        except Role.DoesNotExist:
            return None
    
    @staticmethod
    def remove_role_from_user(user, role_name):
        """Remove a role from a user"""
        try:
            role = Role.objects.get(name=role_name)
            UserRole.objects.filter(user=user, role=role).update(is_active=False)
            return True
        except Role.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_permissions_summary(user):
        """Get a summary of user's permissions organized by module"""
        permissions = user.get_rbac_permissions()
        summary = {}
        
        for permission in permissions:
            if permission.module not in summary:
                summary[permission.module] = []
            summary[permission.module].append({
                'name': permission.name,
                'codename': permission.codename,
                'description': permission.description
            })
        
        return summary
