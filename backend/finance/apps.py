from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'
    verbose_name = 'Financial Management'
    
    def ready(self):
        """
        Import signals when the app is ready.
        """
        try:
            import finance.signals  # noqa
        except ImportError:
            pass
