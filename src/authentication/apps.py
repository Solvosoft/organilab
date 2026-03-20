from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = "authentication"

    def ready(self):
        # TODO: migrate to djgentelella.async_notification.registry.register_context
        # from async_notifications.register import update_template_context
        # update_template_context("new user", "You are register now in Organilab", [...])
        # update_template_context("New feedback", "New Feedback to Organilab", [...])

        super(AuthenticationConfig, self).ready()
