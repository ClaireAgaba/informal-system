from django.apps import AppConfig


class DitMigrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dit_migration'
    verbose_name = 'DIT Migration Tools'