# Generated by Django 4.0.8 on 2022-11-06 23:18
from django.db import connection
from django.db import migrations

def reparair_rol_organization(apps, schema_editor):
    OrganizationUserManagement = apps.get_model('laboratory', 'OrganizationUserManagement')
    OrganizationStructure = apps.get_model('laboratory', 'OrganizationStructure')
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('auth_and_perms', 'Profile')
    ProfilePermission = apps.get_model('auth_and_perms', 'ProfilePermission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Group = apps.get_model("auth", "Group")
    Rol = apps.get_model("auth_and_perms", "Rol")
    Laboratory = apps.get_model('laboratory', 'Laboratory')

    for user in User.objects.filter(profile__isnull=True):
        Profile.objects.create(user=user, phone_number='5068888888',
                               id_card='0000000', job_position='')

    try:
        cc = ContentType.objects.get(app_label='laboratory', model="profile")
        cc.app_label="auth_and_perms"
        cc.save()
    except Exception as e:
        ContentType.objects.create(app_label='auth_and_perms', model="profile")
    for org in OrganizationStructure.objects.all():
        query = OrganizationUserManagement.objects.filter(organization=org)
        if query.count() > 1:
            base = query[0]
            query = query.exclude(pk=base.pk)
            for q in query:
                for user in q.users.all():
                    base.users.add(user)
            print(query.delete())
    for profile in Profile.objects.all():
        for pp in ProfilePermission.objects.filter(profile=profile):
            if pp.content_type.model == 'laboratory':
                lab = Laboratory.objects.get(pk=pp.object_id)
                oum = OrganizationUserManagement.objects.filter(
                    organization=lab.organization, users=profile.user)

                if not oum.exists():
                    #print(lab.organization, lab.organization.pk)
                    org, created = OrganizationUserManagement.objects.get_or_create(organization=lab.organization)
                    org.users.add(profile.user)
                    pp_rols = [x.pk for x in pp.rol.all()]
                    lab.organization.rol.add(*pp_rols)


        ProfilePermission.objects.get_or_create(
                profile=profile,
                content_type=ContentType.objects.filter(
                    app_label=profile._meta.app_label,
                    model=profile._meta.model_name).first(),
                object_id=profile.pk)

    rols = {}
    for group in Group.objects.all():
        rols[group.pk] = Rol.objects.create(name=group.name)
        rols[group.pk].permissions.add(*[x for x in group.permissions.all()])

    records=[]
    with connection.cursor() as cursor:
        cursor.execute(
            "select oum.group_id, oum.organization_id, oumu.user_id from laboratory_organizationusermanagement as oum join laboratory_organizationusermanagement_users as oumu on oum.id = oumu.organizationusermanagement_id")
        for row in cursor.fetchall():
            org = OrganizationStructure.objects.get(pk=row[1])
            group = Group.objects.get(pk=row[0])
            profile = Profile.objects.filter(user_id=row[2]).first()
            if not profile:
                profile = Profile.objects.create(user_id=row[2], phone_number='5068888888',
                                       id_card='0000000', job_position='')

            rol = rols[group.pk]
            pp, x = ProfilePermission.objects.get_or_create(profile=profile, object_id=profile.pk,
                                                  content_type=ContentType.objects.filter(
                                                      app_label=profile._meta.app_label,
                                                      model=profile._meta.model_name).first())

            pp.rol.add(rol)
            org.rol.add(rol)



class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0056_remove_organizationusermanagement_group'),
    ]

    operations = [
        migrations.RunPython(reparair_rol_organization),
#        migrations.RemoveField(
#                 model_name='organizationusermanagement',
#                 name='group',
#        ),
    ]