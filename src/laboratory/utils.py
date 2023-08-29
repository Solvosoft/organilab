import io

import qrcode
import qrcode.image.svg
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db.models.query_utils import Q
from django.http import Http404
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload

from auth_and_perms.models import Profile, User
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory.models import Laboratory, OrganizationStructure, LabOrgLogEntry, \
    UserOrganization, RegisterUserQR, OrganizationStructureRelations


def check_group_has_perm(group,codename):
    if codename:
        _, perm = (codename.split("."))
        return group.permissions.filter(codename=perm).exists()
    return False

def sum_ancestors_group(user_org,lab_org,perm):
    lab_parant = lab_org.get_ancestors(ascending=True, include_self=True)
    user_org = user_org.first()  # first have the first org
    for org in lab_parant:
        if org.level >= user_org.level:
            group = org.group if hasattr(org, 'group') else None
            if group:
                if check_group_has_perm(group,perm):
                    return True
    return False

def check_user_has_perm(user, perm):
    return bool(user.has_perm(perm))


def get_organizations_by_user(user):
    user_org = OrganizationStructure.os_manager.filter_user(user, ancestors=True)
    return user_org

def get_user_laboratories(user, q=None):
    user_org = OrganizationStructure.os_manager.filter_user(user)
    return filter_laboratorist_profile_student(user, user_org, q)


def filter_laboratorist_profile_student(user,user_org, q=None):
    queryset = Laboratory.objects.filter(Q(profile__user=user.pk) |
                                     Q(organization__in=user_org)  ).distinct()
    if q is not None:
        queryset = queryset.filter(name__icontains=q)
    return queryset





def filter_laboratorist_profile(user, user_org=None):
    if user_org is None:
        user_org = OrganizationStructure.os_manager.filter_user(user)
    return Laboratory.objects.filter( Q(profile__user=user.pk) |
                                      Q (organization__in=user_org)
                                    ).distinct()

def check_lab_group_has_perm(user,lab,perm,callback_filter=filter_laboratorist_profile):
    if not user or not lab:
        return False

    # django admins
    if user.is_superuser:
        return True

    if not user.is_authenticated:
        return False

    # Check org of labs
    lab_org = lab.organization  if hasattr(lab, 'organization') else None
    user_org = OrganizationStructure.os_manager.filter_user(user)

    if not user_org:
        user_org=[]

    # if lab have an organizations, compare that perms with perm param
    if lab_org  and lab_org in  user_org:  # user have some organization
        if sum_ancestors_group(user_org,lab_org,perm): # check ancestor perms
                return True

    user_perm = check_user_has_perm(user,perm)   # check if user has perms to do action
    labs = callback_filter(user,user_org)
    return all([user_perm,lab in labs]) # User have perms to all action level


check_lab_perms = check_lab_group_has_perm


def get_rols_from_organization(rootpk, rolfilters={}, org=None):
    if org is None:
        org = OrganizationStructure.objects.filter(pk=rootpk).first()
    query = OrganizationStructure.objects.filter(pk=rootpk, **rolfilters).descendants(of=org, include_self=True)
    return query.values_list('rol', flat=True)


def get_users_from_organization(rootpk, userfilters={}, org=None):
    if org is None:
        org = OrganizationStructure.objects.filter(pk=rootpk).first()
    orgs = list(OrganizationStructure.objects.filter(pk=rootpk).descendants(of=org, include_self=True).values_list('pk', flat=True))
   # orgs = org.descendants(include_self=True) .value_list('pk', flat=True)

    query=UserOrganization.objects.filter(
        organization__in=orgs, user__isnull=False,status=True
    )

    return query.values_list('user', flat=True)


def get_profile_by_organization(organization):
    users = get_users_from_organization(organization)
    return Profile.objects.filter(user__in=users)


def get_laboratories_from_organization(rootpk):
    org = OrganizationStructure.objects.filter(pk=rootpk).first()
    if org:
        desendants = list(OrganizationStructure.objects.filter(pk=rootpk).descendants(include_self=True, of=org).values_list('pk', flat=True))
        return Laboratory.objects.filter(organization__in= desendants).distinct()
    return Laboratory.objects.none()

def get_cas(object, default=None):
    result = default
    if hasattr(object, 'sustancecharacteristics') and object.sustancecharacteristics:
        result = object.sustancecharacteristics.cas_id_number
    return result


def get_imdg(object, default=None):
    result = default
    if hasattr(object, 'sustancecharacteristics') and object.sustancecharacteristics:
        imdg = object.sustancecharacteristics.imdg
        result = imdg if imdg else ""
    return result

def get_molecular_formula(object, default=None):
    result = default
    if hasattr(object, 'sustancecharacteristics') and object.sustancecharacteristics:
        result = object.sustancecharacteristics.molecular_formula
    return result


def find_rel_object(object):
    natural_name = "%s.%s"%(
        object._meta.app_label,
        object._meta.model_name
    )
    instance = None
    if natural_name == 'academic.procedurestep':
        instance = object.procedure.content_object
    elif natural_name == 'academic.procedure':
        instance = object.content_object
    elif natural_name == 'academic.procedurerequiredobject':
        instance = object.step.procedure.content_object
    elif natural_name == 'academic.procedureobservations':
        instance = object.step.procedure.content_object
    elif natural_name == ' reservations_management.reservedproducts':
        #TODO: Allow return a list
        instance = object.shelf_object.shelf.furniture.labroom.laboratory_set.all().first()
    elif natural_name == "laboratory.protocol":
        instance = object.laboratory

    return instance


def organilab_logentry(user, object, action_flag, model_name=None, changed_data=None, object_repr='', change_message='',
                       content_type=None, relobj=None):

    if content_type is None:
        content_type = ContentType.objects.get_for_model(object)

    if model_name is None:
        model_name = object._meta.verbose_name

    if isinstance(relobj, (int, str)):
        relobj=Laboratory.objects.filter(pk=relobj).first()

    action = 'added'
    if action_flag == 2:
        action = 'changed'
    elif action_flag == 3:
        action = 'deleted'

    if not object_repr:
        object_repr = model_name.capitalize() + " has been %s" % (action,)

    if not change_message:
        if action_flag != 3:
            change_message = str([{action: {"fields": changed_data if changed_data else []}}])
        else:
            change_message = "%s %s has been %s" % (str(object), model_name, action)

    log_entry = LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=content_type.id,
        object_id=object.pk,
        object_repr=object_repr,
        action_flag=action_flag,
        change_message=change_message
    )

    if relobj is None:
        relobj = find_rel_object(object)

    if relobj:
        if not isinstance(relobj, (list,)):
            relobj=[relobj]
        for rel_obj in relobj:
            content_type_obj = ContentType.objects.get_for_model(rel_obj)
            LabOrgLogEntry.objects.create(
                log_entry=log_entry,
                content_type=content_type_obj,
                object_id=rel_obj.id
            )


def get_pk_org_ancestors(org_pk):
    organization = OrganizationStructure.objects.filter(pk=org_pk)
    pks = []
    if organization.exists():
        organization = organization.first()
        pks.append(organization.pk)
        pks = pks + list(organization.ancestors().values_list('pk', flat=True))
    return pks

def get_pk_org_ancestors_decendants(user, org_pk):
    org = OrganizationStructure.objects.filter(users=user, pk=org_pk)

    pks = []
    if org.exists():
        org = org.first()
        pks.append(org_pk)
        if org.descendants():
            pks += list(org.descendants().values_list('pk', flat=True))
        if org.ancestors():
            pks += list(org.ancestors().values_list('pk', flat=True))
    return pks


def generate_QR_img_file(url, user, file_name, extension_file):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    file = io.BytesIO()
    img.save(file)
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    obj = ChunkedUpload.objects.create(
        file=content,
        filename=file_name+extension_file,
        offset=len(file.getvalue()),
        completed_on=now(),
        user=user
    )
    return obj.get_uploaded_file(), file


def get_organizations_register_user_base(organization, lab_id):
    lab = Laboratory.objects.get(pk=lab_id)
    content_type = ContentType.objects.filter(
        app_label='laboratory',
        model='laboratory'
    ).first()

    org_base_list = list(organization.descendants().values_list('pk', flat=True))

    org_list_by_lab = OrganizationStructureRelations.objects.filter(
        organization__in=org_base_list,
        content_type=content_type,
        object_id=lab_id
    )

    org_list = list(org_list_by_lab.values_list('organization__pk', flat=True)) + [organization.pk, lab.organization.pk]

    return org_list


def get_exclude_org_register_user(lab_pk, query_org, org_register_pk=None):
    content_type = ContentType.objects.filter(
        app_label='laboratory',
        model='laboratory'
    ).first()

    exclude_org = RegisterUserQR.objects.filter(
        organization_register__in=query_org,
        content_type=content_type,
        object_id=lab_pk
    )

    if org_register_pk:
        exclude_org = exclude_org.exclude(organization_register=org_register_pk)
    return list(exclude_org.values_list('organization_register__pk', flat=True))


def get_organizations_register_user(organization, lab_id, org_register_pk=None):
    org_base = get_organizations_register_user_base(organization, lab_id)
    org_exclude = get_exclude_org_register_user(lab_id, org_base, org_register_pk=org_register_pk)
    return OrganizationStructure.objects.filter(pk__in=org_base).exclude(pk__in=org_exclude).distinct()


def get_logentries_org_management(self, org):
    in_org=org
    if not org:
        return self.queryset.none()
    else:
        org = OrganizationStructure.objects.filter(pk=org).first()
        if not org:
            return LabOrgLogEntry.objects.filter(
                     Q(
                        content_type__app_label='laboratory',
                        content_type__model='organizationstructure',
                        object_id=in_org
                    )
                ).values_list('log_entry', flat=True)
    laboratories = list(get_laboratories_from_organization(org.pk).values_list('pk', flat=True))

    log_entries = LabOrgLogEntry.objects.filter(
        Q(content_type__app_label='laboratory',
          content_type__model='laboratory',
          object_id__in=laboratories
          ) | Q(
            content_type__app_label='laboratory',
            content_type__model='organizationstructure',
            object_id=org.pk
        )
    ).values_list('log_entry', flat=True)

    return log_entries


def check_has_profile(user):
    obj = Profile.objects.filter(user=user)
    return obj.exists()

def get_laboratories_from_organization_profile(rootpk, user):
    org = OrganizationStructure.objects.filter(pk=rootpk).first()
    if org:
        desendants = list(OrganizationStructure.objects.filter(pk=rootpk).descendants(include_self=True, of=org).values_list('pk', flat=True))
        return Laboratory.objects.filter(organization__in= desendants, profile__user__pk=user).distinct()

    return Laboratory.objects.none()


def get_laboratories_by_user_profile(user, org_pk):
    queryset = OrganizationStructure.os_manager.filter_labs_by_user(user, org_pk=org_pk)
    rel_lab = OrganizationStructureRelations.objects.filter(
        organization=org_pk, content_type__app_label='laboratory',
        content_type__model='laboratory').values_list('object_id', flat=True)
    filters = Q(organization__pk=org_pk, profile__user=user) | Q(pk__in=rel_lab)
    return list(queryset.filter(filters).distinct().values_list('pk', flat=True))


def check_user_access_kwargs_org_lab(org, lab, user):
    user_access = False

    if org:
        organization = OrganizationStructure.objects.filter(pk=org)

        if organization.exists():
            organization = organization.first()

            if organization.users.filter(pk=user.pk).exists():

                if lab:
                    laboratory = Laboratory.objects.filter(pk=lab)

                    if laboratory.exists():
                        can_change = organization_can_change_laboratory(laboratory.first(), organization)
                        user_labs = get_laboratories_by_user_profile(user, org)

                        if can_change and lab in user_labs:
                            user_access = True
                else:
                    user_access = True #REPORT VIEWS WITH LAB = 0
    return user_access


def save_object_by_action(user, obj, relobj, changed_data, action_flag, object_repr):
    obj.save()
    organilab_logentry(user, obj, action_flag, object_repr, changed_data=changed_data,
                       relobj=relobj)
