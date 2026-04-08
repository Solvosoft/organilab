from django.db import migrations

FEEDBACK_MESSAGE = (
    "<h2>New Feedback Received</h2>\n"
    "<p><strong>Title:</strong> {{ feedback.title }}</p>\n"
    "{% if feedback.user %}"
    "<p><strong>User:</strong> {{ feedback.user.get_full_name }} ({{ feedback.user.email }})</p>"
    "{% endif %}\n"
    "<hr>\n"
    "<p><strong>Explanation:</strong></p>\n"
    "<div>{{ explanation|safe }}</div>\n"
    "{% if file_url %}"
    "<br><p><strong>Archivo adjunto:</strong> "
    '<a href="{{ file_url }}">{{ feedback.related_file.name }}</a></p>'
    "{% endif %}\n"
    "<br>\n"
    '<p><a href="{{ admin_url }}">Ver en el administrador</a></p>'
)


def update_feedback_template(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.filter(code="New feedback").update(message=FEEDBACK_MESSAGE)


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0006_delete_demorequest_delete_feedbackentry"),
        ("async_notifications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(update_feedback_template, migrations.RunPython.noop),
    ]