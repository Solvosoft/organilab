from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = 'authentication'

    def ready(self):
        from async_notifications.register import update_template_context

        super(AuthenticationConfig, self).ready()
        context = [
            ('User', 'New user'),
            ('organization', 'Organization registered'),
            ('role', 'Selected role 1. Organization 2. Student')
        ]
        update_template_context(
            "new user",  'You are register now in Organilab', context)

        fdcontext = [
            ('feedback', """Feedback instance, use like {{ feedback.title }} options:  
            title, explanation, related_file, laboratory_id""")
        ]
        update_template_context(
            "New feedback",  'New Feedback to Organilab', fdcontext)
