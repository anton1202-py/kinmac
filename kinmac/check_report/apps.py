from django.apps import AppConfig


class CheckReportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'check_report'

    def ready(self):
        import check_report.signals  # Импортируйте файл с сигналами
