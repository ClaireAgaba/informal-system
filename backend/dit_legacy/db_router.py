class DitLegacyRouter:
    app_label = 'dit_legacy'
    db_name = 'dit_legacy'

    def _uses_default(self, model):
        return getattr(model, '_use_default_db', False)

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'default' if self._uses_default(model) else self.db_name
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'default' if self._uses_default(model) else self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == self.app_label or obj2._meta.app_label == self.app_label:
            return True if (self._uses_default(type(obj1)) or self._uses_default(type(obj2))) else False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            # All Django-managed models in dit_legacy go to the default DB.
            # The legacy MySQL tables are accessed via raw SQL only.
            return db == 'default'
        return None
