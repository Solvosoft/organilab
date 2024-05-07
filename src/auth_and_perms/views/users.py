from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from academic.models import CommentProcedureStep, Procedure, MyProcedure
from auth_and_perms.forms import MergeUsers, UserForm
from auth_and_perms.models import ProfilePermission, RegistrationUser, \
    AuthorizedApplication
from laboratory.models import RegisterUserQR, ShelfObject, UserOrganization, \
    ObjectLogChange, BlockedListNotification, CommentInform, Protocol, \
    OrganizationStructureRelations, Inform, LabOrgLogEntry, ShelfObjectMaintenance, \
    ShelfObjectCalibrate, ShelfObjectTraining, BaseCreationObj
from presentation.models import FeedbackEntry, QRModel, AbstractOrganizationRef
from report.models import TaskReport, ObjectChangeLogReportBuilder
from reservations_management.models import Reservations, ReservedProducts
from sga.models import SubstanceObservation


def users_list(request):
     merge_form = MergeUsers(user_session=request.user.pk)
     return render(request,"auth_and_perms/users_list.html", context={
         "merge_form": merge_form})

def merge_users(request, user_base, user_delete):
    user_base_instance = get_object_or_404(User, pk=user_base)
    user_delete_instance = get_object_or_404(User, pk=user_delete)

    context = {
        "user_base": user_base,
        "user_delete": user_delete,
        "user_base_form": UserForm(instance=user_base_instance, render_type="as_horizontal"),
        "user_delete_form": UserForm(instance=user_delete_instance, render_type="as_horizontal", prefix="delete")
    }

    return render(request, "auth_and_perms/merge_users.html", context=context)


def update_user_elements_laboratory(user_base_instance, user_delete_instance, user_content_type):
    # BaseCreationObj includes --> ShelfObjectObservation, LaboratoryRoom, Shelf,
    # Furniture, Laboratory, Provider, TranferObject, Protocol
    BaseCreationObj.objects.filter(created_by=user_delete_instance).update(created_by=user_base_instance)
    RegisterUserQR.objects.filter(created_by=user_delete_instance).update(created_by=user_base_instance)
    ShelfObject.objects.filter(created_by=user_delete_instance).update(created_by=user_base_instance)
    UserOrganization.objects.filter(user=user_delete_instance).update(user=user_base_instance)
    ObjectLogChange.objects.filter(user=user_delete_instance).update(user=user_base_instance)
    BlockedListNotification.objects.filter(user=user_delete_instance).update(user=user_base_instance)
    CommentInform.objects.filter(created_by=user_delete_instance).update(created_by=user_base_instance)
    Protocol.objects.filter(upload_by=user_delete_instance).update(upload_by=user_base_instance)
    ShelfObjectMaintenance.objects.filter(
        validator=user_delete_instance.profile).update(
        validator=user_base_instance.profile)
    ShelfObjectCalibrate.objects.filter(
        validator=user_delete_instance.profile).update(
        validator=user_base_instance.profile)
    training_list = ShelfObjectTraining.objects.filter(
        intern_people_receive_training__in=[user_delete_instance.profile])

    for training in training_list:
        training.intern_people_receive_training.remove(user_delete_instance.profile)
        training.intern_people_receive_training.add(user_base_instance.profile)

    OrganizationStructureRelations.objects.filter(object_id=user_delete_instance.pk,
                                                  content_type=user_content_type).update(
        object_id=user_base_instance.pk)
    Inform.objects.filter(object_id=user_delete_instance.pk,
                          content_type=user_content_type).update(
        object_id=user_base_instance.pk)
    LabOrgLogEntry.objects.filter(object_id=user_delete_instance.pk,
                          content_type=user_content_type).update(
        object_id=user_base_instance.pk)
    RegisterUserQR.objects.filter(object_id=user_delete_instance.pk,
                                  content_type=user_content_type).update(
        object_id=user_base_instance.pk)

def update_user_elements_academic(user_base_instance, user_delete_instance, user_content_type):
    CommentProcedureStep.objects.filter(created_by=user_delete_instance).update(created_by=user_base_instance)
    Procedure.objects.filter(object_id=user_delete_instance.pk,
                             content_type=user_content_type).update(
        object_id=user_base_instance.pk)
    MyProcedure.objects.filter(object_id=user_delete_instance.pk,
                             content_type=user_content_type).update(
        object_id=user_base_instance.pk)

def update_user_elements_auth_and_perms(user_base_instance, user_delete_instance):
    CommentProcedureStep.objects.filter(created_by=user_delete_instance).update(created_by=user_base_instance)
    AuthorizedApplication.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)
    RegistrationUser.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)
    ProfilePermission.objects.filter(profile=user_delete_instance.profile).update(
        profile=user_base_instance.profile)

def update_user_elements_presentation(user_base_instance, user_delete_instance, user_content_type):
    # AbstractOrganizationRef includes MyProcedure, MSDSObject, ShelfObjectLog, Inform,
    # InformScheduler, Object, ShelfObjectCalibrate, ShelfObjectTraining, CustomForm,
    # ShelfObjectGuarantee, ShelfObjectEquipmentCharacteristics, ShelfObjectMaintenance,
    # ReservedProducts, PriorityConstrain, RiskZone, IncidentReport, Substance,
    # DisplayLabel, BuilderInformation, TemplateSGA, ReviewSubstance
    AbstractOrganizationRef.objects.filter(created_by=user_delete_instance).update(
        created_by=user_base_instance)
    FeedbackEntry.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)
    QRModel.objects.filter(object_id=user_delete_instance.pk,
                             content_type=user_content_type).update(
        object_id=user_base_instance.pk)

def update_user_elements_report(user_base_instance, user_delete_instance):
    TaskReport.objects.filter(created_by=user_delete_instance).update(
        created_by=user_base_instance)
    ObjectChangeLogReportBuilder.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)

def update_user_elements_reservations(user_base_instance, user_delete_instance):
    Reservations.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)
    ReservedProducts.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)

def update_user_elements_sga(user_base_instance, user_delete_instance):
    BuilderInformation.objects.filter(user=user_delete_instance).update(
        user=user_base_instance)
    SubstanceObservation.objects.filter(created_by=user_delete_instance).update(
        created_by=user_base_instance)

def call_update_user_functions(user_base_instance, user_delete_instance):
    user_content_type = ContentType.objects.get(app_label='auth', model="user")
    update_user_elements_auth_and_perms(user_base_instance, user_delete_instance)
    update_user_elements_report(user_base_instance, user_delete_instance)
    update_user_elements_reservations(user_base_instance, user_delete_instance)
    update_user_elements_sga(user_base_instance, user_delete_instance)
    update_user_elements_presentation(user_base_instance, user_delete_instance,
                                      user_content_type)
    update_user_elements_laboratory(user_base_instance, user_delete_instance,
                                    user_content_type)
    update_user_elements_academic(user_base_instance, user_delete_instance,
                                  user_content_type)


def save_user_merge(request, user_base, user_delete):
    user_base_instance = get_object_or_404(User, pk=user_base)
    user_delete_instance = get_object_or_404(User, pk=user_delete)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user_base_instance, render_type="as_horizontal")

        if form.is_valid():
            form.save()
            call_update_user_functions(user_base_instance, user_delete_instance)
            user_delete_instance.delete()
            messages.success(request, _("Element saved successfully"))
        else:
            context = {
                "user_base": user_base,
                "user_delete": user_delete,
                "user_base_form": form,
                "user_delete_form": UserForm(instance=user_delete_instance,
                                             render_type="as_horizontal")
            }
            return render(request, "auth_and_perms/merge_users.html", context=context)
    return redirect(reverse("auth_and_perms:users_list"))
