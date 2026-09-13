from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = "authentication"

    def ready(self):
        from djgentelella.async_notification.registry import register_context

        super(AuthenticationConfig, self).ready()
        register_context(
            code="new-user",
            subject="You are register now in Organilab",
            models={
                "user": "auth.User",
                "organization": "laboratory.OrganizationStructure",
            },
            exclude={"user": ["password", "last_login", "is_superuser"]},
            extra_variables={
                "role": "Selected role 1. Organization 2. Student",
            },
        )
        register_context(
            code="new-feedback",
            subject="New Feedback to Organilab",
            models={"feedback": "presentation.FeedbackEntry"},
            extra_variables={
                "admin_url": "Link to the feedback entry in the admin",
                "explanation": "Feedback explanation with absolute image URLs",
                "file_url": "Absolute URL of the attached file, if any",
            },
        )
