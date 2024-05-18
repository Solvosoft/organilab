from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models.fields.related import ManyToOneRel
from django.utils.translation import activate, get_language

def send_email_user_management(request, user_base, user_delete, action):
    schema = request.scheme + "://"
    if hasattr(user_base, 'profile'):
        lang = user_base.profile.language
        oldlang = get_language()
        context = {
            'user_base': user_base,
            'user_delete': user_delete,
            'domain': schema + request.get_host(),
            'action': action
        }
        activate(lang)
        send_mail(subject=_(
                "Account Update: Merger with Another Account.") if action == "merge" else _(
                "Account Delete"),
                      message=_("Please use a html reader client"),
                      recipient_list=[user_base.email],
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      html_message=render_to_string(
                          'auth_and_perms/mail/'+lang+'/user_merge_notification.html',
                          context=context
                      )
                      )
        activate(oldlang)


def send_delete_user_email(user_delete):
    if hasattr(user_delete, 'profile'):
        lang = user_delete.profile.language
        oldlang = get_language()
        context={'lang': lang,
                 'user': user_delete}
        activate(lang)
        send_mail(subject=_("Thanks for be part of Organilab, we will miss you."),
                      message=_("Your account was removed"),
                      recipient_list=[user_delete.email],
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      html_message=render_to_string(
                          "auth_and_perms/mail/"+lang+"/user_delete_notification.html",
                          context=context
                      )
                      )
        activate(oldlang)

def merge_information_user(to_delete, to_related):
    for field in to_delete._meta.get_fields():
        if field.name == 'sga_substance':
            print(field)
        if field.name in ['user_permissions', 'groups', 'profile', 'usertotpdevice',
                          'registrationuser', 'authorizedapplication', 'deleteuserlist',
                          'auth_token', 'chunked_uploads', 'totpdevice']:
            continue
        if isinstance(field, ManyToOneRel):
            #print(field.name,field.target_field.model, field.field.name)
            field.target_field.model.objects.filter(**{field.field.name: to_delete}).update(
                **{field.field.name: to_related}
            )
    if hasattr(to_delete, 'profile') and hasattr(to_related, 'profile'):
        del_profile=to_delete.profile
        merge_profile = to_related.profile
        for field in del_profile._meta.get_fields():
            if field.name in ['profilepermission']:
                continue
            if isinstance(field, ManyToOneRel):
                field.target_field.model.objects.filter(
                    **{field.field.name: del_profile}).update(
                    **{field.field.name: merge_profile}
                )


def delete_user(to_delete, to_related):
    merge_information_user(to_delete, to_related)
    send_delete_user_email(to_delete)
    print("Deleting:", to_delete.username)
    print(to_delete.delete())

def user_management(request, user_base, user_delete, action):
    send_email_user_management(request, user_base, user_delete, action)
    delete_user(user_delete, user_base)
