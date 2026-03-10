from django.apps import AppConfig


class UserSessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_sessions'
    verbose_name = "User Sessions"

def ready(self):
    import user_sessions.signals  # Import signals to connect them when the app is ready
    