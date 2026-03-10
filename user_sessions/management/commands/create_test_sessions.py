from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from user_sessions.models import ActiveSession
from user_sessions.utils import SessionManager
from django.utils import timezone
import uuid

class Command(BaseCommand):
    help = 'Create test sessions for debugging'

    def handle(self, *args, **options):
        session_manager = SessionManager()
        
        # Get all users
        users = User.objects.all()
        
        for user in users:
            # Create a fake session
            session_key = f"test_{uuid.uuid4().hex[:20]}"
            
            # Create Django session
            session = Session.objects.create(
                session_key=session_key,
                session_data='{}',
                expire_date=timezone.now() + timezone.timedelta(days=1)
            )
            
            # Create active session
            ActiveSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address='127.0.0.1',
                user_agent='Test Browser',
                device_type='desktop',
                browser='Chrome',
                os='Windows',
                location_city='Test City',
                location_country='Test Country',
                is_active=True,
                remember_me=False
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created test session for {user.username}')
            )
        
        # Show statistics
        stats = session_manager.get_session_statistics()
        self.stdout.write(f"Total connected users: {stats['total_connected']}")
