from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from laboratory.models import (CLInventory,
                               ObjectFeatures,
                               Object,
                               ShelfObject,
                               LaboratoryRoom,
                               Shelf,
                               Furniture,
                               OrganizationStructure,
                               OrganizationUserManagement,
                               Profile,
                               Laboratory,
                               Solution,
                               )
from academic.models import (Procedure,
                             ProcedureStep,
                             ProcedureRequiredObject,
                             ProcedureObservations
                             )


def create_perms(codename):
    model_perms = {
        "user": User,
        "report": Laboratory,
        "clinventory": CLInventory,
        "objectfeatures": ObjectFeatures,
        "object": Object,
        "shelfobject": ShelfObject,
        "shelf": Shelf,
        "furniture": Furniture,
        "organizationstructure": OrganizationStructure,
        "laboratory": Laboratory,
        "laboratoryroom": LaboratoryRoom,
        "organizationusermanagement": OrganizationUserManagement,
        "profile": Profile,
        "solution": Solution,
        "procedure": Procedure,
        "procedurestep": ProcedureStep,
        "procedurerequiredobject": ProcedureRequiredObject,
        "procedureobservations": ProcedureObservations
    }
    action, name = (codename.split("_"))
    if name in model_perms:
        model = model_perms[name]
        content_type = ContentType.objects.get_for_model(model)
        try:
            permission = Permission.objects.get(codename=codename)
            print("\t Permission %s exist" % codename)
        except Permission.DoesNotExist:
            permission, created = Permission.objects.get_or_create(codename=codename,
                                                                   name=_(
                                                                       'Can %s' % name),
                                                                   content_type=content_type)
            print("\t Permission %s creating" % codename)


def check_perms(perms):
    if not hasattr(perms, '__iter__'):
        create_perms(perms)
    else:
        for iperm in perms:
            create_perms(iperm)


def set_perms(group, perms):
    if not hasattr(perms, '__iter__'):
        group.permissions.add(perms)
    else:
        for perm in perms:
            group.permissions.add(perm)


def load_group_perms(apps, schema_editor):

    perms_student = [
        # reservations
        "view_reservation", "add_reservation",
        # laboratory
        "view_laboratory",
    ]
    check_perms(perms_student)
    perms_professor = [  # reservations
        "view_reservation", "add_reservation",
        # procedureobservations
        "view_procedureobservations", "add_procedureobservations", "change_procedureobservations", "delete_procedureobservations",
        # procedure
        "view_procedure", "add_procedure", "change_procedure", "delete_procedure",
        # procedurestep
        "view_procedurestep", "add_procedurestep", "change_procedurestep", "delete_procedurestep",
        # procedurerequiredobject
        "view_procedurerequiredobject", "add_procedurerequiredobject", "change_procedurerequiredobject", "delete_procedurerequiredobject",

        # solutions
        "view_solution", "add_solution", "change_solution",

        # laboratory
        "view_laboratory",
    ]
    check_perms(perms_professor)

    perms_laboratory = [  # reservations
        "add_reservation", "change_reservation", "delete_reservation", "add_reservationtoken",
        "change_reservationtoken", "delete_reservationtoken", "view_reservation",

        # shelf
        "view_shelf", "add_shelf", "change_shelf", "delete_shelf",
        # shelfobjets
        "view_shelfobject", "add_shelfobject", "change_shelfobject", "delete_shelfobject",
        # objets
        "view_object", "add_object", "change_object", "delete_object",
        # objectfeatures
        "view_objectfeatures", "add_objectfeatures", "change_objectfeatures", "delete_objectfeatures",
        # procedurerequiredobject
        "view_procedurerequiredobject", "add_procedurerequiredobject", "change_procedurerequiredobject",
        "delete_procedurerequiredobject",
        # laboratory
        "view_laboratory", "add_laboratory", "change_laboratory", "delete_laboratory",
        # laboratoryroom
        "view_laboratoryroom", "add_laboratoryroom", "change_laboratoryroom", "delete_laboratoryroom",
        # furniture
        "view_furniture", "add_furniture", "change_furniture", "delete_furniture",
        # Products
        "view_product", "add_product", "change_product", "delete_product",
        # onsertation
        "view_observation", "add_observation", "change_observation", "delete_observation",
        # CL Inventory
        "view_clinventory", "add_clinventory", "change_clinventory", "delete_clinventory", "add_solution",
        # solutions
        "view_solution", "add_solution", "change_solution", "delete_solution",

        # reports
        "view_report", "do_report",
    ]
    check_perms(perms_laboratory)

    GLaboratory = Group.objects.get(name='Laboratory Administrator')
    if not GLaboratory:
        GLaboratory = Group(name='Laboratory Administrator')
        GLaboratory.save()

    GProfessor = Group.objects.get(name='Professor')
    if not GProfessor:
        GProfessor = Group(name='Professor')
        GProfessor.save()

    # Get groups
    GStudent = Group.objects.get(name='Student')
    if not GStudent:
        GStudent = Group(name='Student')
        GStudent.save()

    # add perms to student
    perms = Permission.objects.filter(codename__in=perms_student)
    set_perms(GStudent, perms)

    # add perms to Professor
    perms = Permission.objects.filter(codename__in=perms_professor)
    set_perms(GProfessor, perms)
    # add perms to Laboratories Administrator
    perms = Permission.objects.filter(codename__in=perms_laboratory)
    set_perms(GLaboratory, perms)

def create_groups(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Group = apps.get_model("auth", "Group")
    groups = ['Laboratory Administrator', 'Professor', 'Student']
    for group in groups:
        if not Group.objects.filter(name=group).exists():
            Group.objects.create(name=group)
