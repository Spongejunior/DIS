from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Mzimba North VetAssistant'

    def ready(self):
        # The login view records last_login in Malawi time itself.
        from django.contrib.auth.signals import user_logged_in
        user_logged_in.disconnect(dispatch_uid='update_last_login')
