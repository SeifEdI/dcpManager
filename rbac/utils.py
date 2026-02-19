from .models import Permission, Role, UserRole
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

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
            
            # Audit permissions
            ('audit.view', 'View Audit Logs', 'audit', 'Can view audit logs and security events'),
            ('audit.manage', 'Manage Audit System', 'audit', 'Can configure audit settings and retention'),
            ('audit.export', 'Export Audit Data', 'audit', 'Can export audit logs and reports'),
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
                        'reports.view', 'reports.generate', 'users.view', 'users.assign_roles',
                        'audit.view'
                    ]
                )
            },
            {
                'name': 'HR Assistant',
                'description': 'HR assistant with limited employee management',
                'permissions': Permission.objects.filter(
                    codename__in=[
                        'dashboard.view', 'employees.view', 'employees.add', 'employees.edit',
                        'departments.view', 'reports.view', 'users.view'
                    ]
                )
            },
            {
                'name': 'Department Manager',
                'description': 'Department manager with view access to employees',
                'permissions': Permission.objects.filter(
                    codename__in=[
                        'dashboard.view', 'employees.view', 'departments.view', 
                        'reports.view', 'users.view'
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
            },
            {
                'name': 'Auditor',
                'description': 'Audit and compliance specialist with log access',
                'permissions': Permission.objects.filter(
                    codename__in=[
                        'dashboard.view', 'employees.view', 'users.view',
                        'audit.view', 'audit.export', 'reports.view', 'reports.generate'
                    ]
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
    @transaction.atomic
    def assign_role_to_user(user, role_name, assigned_by=None):
        """Assign a role to a user"""
        try:
            role = Role.objects.get(name=role_name, is_active=True)
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={
                    'assigned_by': assigned_by,
                    'assigned_at': timezone.now(),
                    'is_active': True
                }
            )
            if not created and not user_role.is_active:
                # Reactivate previously deactivated role
                user_role.is_active = True
                user_role.assigned_by = assigned_by
                user_role.assigned_at = timezone.now()
                user_role.save()
                return user_role
            elif not created and user_role.is_active:
                # Role already active
                return None
            return user_role
        except Role.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error assigning role: {e}")
            return None

    @staticmethod
    @transaction.atomic
    def remove_role_from_user(user, role_name):
        """Remove a role from a user"""
        try:
            role = Role.objects.get(name=role_name)
            updated = UserRole.objects.filter(
                user=user, 
                role=role, 
                is_active=True
            ).update(
                is_active=False,
                deactivated_at=timezone.now()
            )
            return updated > 0
        except Role.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error removing role: {e}")
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

    @staticmethod
    def get_user_roles_summary(user):
        """Get a summary of user's active roles"""
        user_roles = UserRole.objects.filter(
            user=user, 
            is_active=True
        ).select_related('role', 'assigned_by')
        
        return [{
            'role': user_role.role,
            'assigned_by': user_role.assigned_by,
            'assigned_at': user_role.assigned_at,
            'permissions_count': user_role.role.permissions.count()
        } for user_role in user_roles]

    @staticmethod
    def check_user_permission(user, permission_codename):
        """Check if user has a specific permission"""
        return user.has_rbac_permission(permission_codename)

    @staticmethod
    def get_users_with_role(role_name):
        """Get all users with a specific role"""
        try:
            role = Role.objects.get(name=role_name, is_active=True)
            return User.objects.filter(
                user_roles__role=role,
                user_roles__is_active=True
            ).distinct()
        except Role.DoesNotExist:
            return User.objects.none()

    @staticmethod
    def get_role_statistics():
        """Get statistics about roles and permissions"""
        return {
            'total_roles': Role.objects.filter(is_active=True).count(),
            'total_permissions': Permission.objects.count(),
            'total_user_roles': UserRole.objects.filter(is_active=True).count(),
            'users_with_roles': User.objects.filter(user_roles__is_active=True).distinct().count(),
            'users_without_roles': User.objects.filter(user_roles__isnull=True).count(),
        }

    @staticmethod
    def cleanup_inactive_roles():
        """Clean up old inactive role assignments"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=90)  # 90 days old
        
        deleted_count = UserRole.objects.filter(
            is_active=False,
            deactivated_at__lt=cutoff_date
        ).delete()[0]
        
        return deleted_count

    @staticmethod
    def bulk_assign_role(users, role_name, assigned_by=None):
        """Assign a role to multiple users at once"""
        results = {
            'success': [],
            'failed': [],
            'already_assigned': []
        }
        
        for user in users:
            result = RBACManager.assign_role_to_user(user, role_name, assigned_by)
            if result is None:
                results['already_assigned'].append(user)
            elif result:
                results['success'].append(user)
            else:
                results['failed'].append(user)
        
        return results

    @staticmethod
    def get_permission_usage():
        """Get usage statistics for permissions"""
        permissions = Permission.objects.all()
        usage_stats = []
        
        for permission in permissions:
            roles_count = permission.roles.filter(is_active=True).count()
            users_count = User.objects.filter(
                user_roles__role__permissions=permission,
                user_roles__is_active=True
            ).distinct().count()
            
            usage_stats.append({
                'permission': permission,
                'roles_using': roles_count,
                'users_with_access': users_count
            })
        
        return usage_stats
