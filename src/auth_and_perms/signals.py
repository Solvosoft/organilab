from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token

from auth_and_perms.models import AuthorizedApplication


@receiver(post_save, sender=AuthorizedApplication)
def create_authentication_for_project(sender, instance, created, **kwargs):
    if created:
        user = User.objects.create_user("application/"+instance.name, is_active=True)
        token = Token.objects.create(user=user)
        AuthorizedApplication.objects.filter(pk=instance.pk).update(user=user)