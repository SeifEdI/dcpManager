import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/seifeddine/dev/dcpManager')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcpmanager.settings')
django.setup()

from audit.utils import AuditLogger
from django.contrib.auth.models import User

def initialize_audit_system():
    """Initialize the audit system and create initial log entries"""
    
    print("🔍 Initializing Audit System...")
    
    # Create initial system log entry
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if admin_user:
        AuditLogger.log_action(
            user=admin_user,
            action='create',
            description='Audit system initialized successfully',
            severity='medium',
            module='system',
            metadata={
                'system_component': 'audit',
                'initialization_time': str(timezone.now()),
                'features_enabled': [
                    'audit_logging',
                    'employee_access_tracking',
                    'security_event_monitoring',
                    'rbac_integration'
                ]
            }
        )
        
        print(f"✅ Created initial audit log entry by {admin_user.username}")
    
    print("\n🎉 Audit System initialization completed!")
    print("\n📊 Features Available:")
    print("   • General audit logging for all user actions")
    print("   • Employee data access tracking")
    print("   • Security event monitoring")
    print("   • Failed login attempt tracking")
    print("   • Role assignment change logging")
    print("   • RBAC integration with permission checks")
    
    print("\n🔗 Access Points:")
    print("   • Audit Dashboard: /audit/dashboard/")
    print("   • Audit Logs: /audit/logs/")
    print("   • Employee Access Logs: /audit/employee-access/")
    print("   • Security Events: /audit/security-events/")
    print("   • My Activity: /audit/my-activity/")
    
    print("\n💡 Next Steps:")
    print("   1. Access the audit dashboard to view system activity")
    print("   2. Configure log retention policies in settings")
    print("   3. Set up alerts for high-risk security events")
    print("   4. Review and customize audit permissions in RBAC")

if __name__ == '__main__':
    from django.utils import timezone
    initialize_audit_system()
