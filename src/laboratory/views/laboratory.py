# encoding: utf-8
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.template.loader import get_template
from django.urls import reverse_lazy, path
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView
from weasyprint import HTML

from academic.models import MyProcedure
from auth_and_perms.models import Profile, ProfilePermission
from laboratory import utils
from laboratory.forms import (
    LaboratoryCreate,
    H_CodeForm,
    LaboratoryEdit,
    OrganizationUserManagementForm,
    RegisterUserQRForm,
    RegisterForm,
    LoginForm,
    PasswordCodeForm,
)
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    RegisterUserQR,
    UserOrganization,
    OrganizationStructureRelations,
    Inform,
    InformsPeriod,
)
from laboratory.utils import (
    organilab_logentry,
    get_laboratories_by_user_profile,
    register_laboratory_contenttype,
    delete_profile_roles_related_to_laboratory,
    delete_relation_between_laboratory_with_other_models,
)
from laboratory.views.djgeneric import CreateView, UpdateView, ListView, DeleteView
from laboratory.views.laboratory_utils import filter_by_user_and_hcode
from presentation.models import FeedbackEntry


@method_decorator(permission_required("laboratory.change_laboratory"), name="dispatch")
class LaboratoryEdit(UpdateView):
    model = Laboratory
    template_name = "laboratory/edit.html"
    lab_pk_field = "pk"

    # fields = ['name', 'phone_number', 'location', 'geolocation']
    form_class = LaboratoryEdit

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context["laboratory"] = self.object.pk
        return context

    def get_success_url(self):
        return reverse("laboratory:mylabs", kwargs={"org_pk": self.org})

    def form_valid(self, form):
        laboratory = form.save()
        utils.organilab_logentry(
            self.request.user,
            laboratory,
            CHANGE,
            changed_data=form.changed_data,
            relobj=self.object,
        )
        return super(LaboratoryEdit, self).form_valid(form)


class LaboratoryView(object):
    model = Laboratory
    template_name_base = "laboratory/laboratory_"

    def __init__(self):
        self.create = login_required(
            CreateView.as_view(
                model=self.model,
                fields=("name",),
                success_url=reverse_lazy("laboratory:laboratory_list"),
                template_name=self.template_name_base + "form.html",
            )
        )

        self.edit = login_required(
            UpdateView.as_view(
                model=self.model,
                fields=("name",),
                success_url=reverse_lazy("laboratory:laboratory_list"),
                template_name=self.template_name_base + "form.html",
            )
        )

        self.delete = login_required(
            DeleteView.as_view(
                model=self.model,
                success_url=reverse_lazy("laboratory:laboratory_list"),
                template_name=self.template_name_base + "delete.html",
            )
        )

        self.list = login_required(
            ListView.as_view(
                model=self.model,
                paginate_by=10,
                template_name=self.template_name_base + "list.html",
            )
        )

    def get_urls(self):
        return [
            path("list", self.list, name="laboratory_list"),
            path("create", self.create, name="laboratory_create"),
            path("edit/<int:pk>/", self.edit, name="laboratory_update"),
            path("delete/<int:pk>/", self.delete, name="laboratory_delete"),
        ]


@method_decorator(permission_required("laboratory.add_laboratory"), name="dispatch")
class CreateLaboratoryFormView(FormView):
    template_name = "laboratory/laboratory_create.html"
    form_class = LaboratoryCreate
    success_url = ""

    def get_form_kwargs(self):
        kwargs = super(CreateLaboratoryFormView, self).get_form_kwargs()
        kwargs["initial"] = {"organization": self.kwargs["org_pk"]}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CreateLaboratoryFormView, self).get_context_data(**kwargs)
        context["addorgform"] = OrganizationUserManagementForm(prefix="addorg")
        context["org_pk"] = self.kwargs["org_pk"]
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        utils.organilab_logentry(
            self.request.user,
            self.object,
            ADDITION,
            changed_data=form.changed_data,
            relobj=self.object,
        )

        user = self.request.user
        contenttypeobj = self.object
        ppp = user.profile.profilepermission_set.first()

        rol = ppp.rol.first() if ppp else None
        pp, created = ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=ContentType.objects.filter(
                app_label=contenttypeobj._meta.app_label,
                model=contenttypeobj._meta.model_name,
            ).first(),
            object_id=contenttypeobj.pk,
        )
        if created and rol:
            pp.rol.add(rol)

        register_laboratory_contenttype(self.object.organization, self.object)
        #        admins = User.objects.filter(is_superuser=True)
        # TODO: This is necesary ?  all user has to be profile
        user.profile.laboratories.add(self.object)
        #        for admin in admins:
        #            if not hasattr(admin, 'profile'):
        #                admin.profile = Profile.objects.create(user=admin)
        #            admin.profile.laboratories.add(self.object)
        response = super(CreateLaboratoryFormView, self).form_valid(form)

        return response

    def get_success_url(self):
        messages.success(self.request, _("Laboratory was created successfully"))
        return reverse("auth_and_perms:organizationManager")


@method_decorator(permission_required("laboratory.add_laboratory"), name="dispatch")
class CreateLaboratoryView(CreateView):
    form_class = LaboratoryCreate
    success_url = "/"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        form = self.get_form()
        if request.user.has_perm("laboratory.add_laboratory"):
            if form.is_valid():
                form.save(user)
                return redirect(self.success_url)
        else:
            messages.error(
                request,
                _(
                    "Sorry, there is not available laboratory, please contact the administrator and request a laboratory enrollment"
                ),
            )
            # Translate
            return redirect(self.success_url)


@method_decorator(permission_required("laboratory.view_laboratory"), name="dispatch")
class LaboratoryListView(ListView):
    model = Laboratory
    template_name = "laboratory/laboratory_list.html"
    success_url = "/"
    paginate_by = 15
    ordering = ["name"]

    def get_queryset(self):
        laboratories = get_laboratories_by_user_profile(self.request.user, self.org)
        pp = (
            ProfilePermission.objects.filter(
                profile=self.request.user.profile,
                content_type__app_label=self.model._meta.app_label,
                content_type__model=self.model._meta.model_name,
                object_id__in=laboratories,
            )
            .distinct("object_id")
            .values_list("object_id", flat=True)
        )
        queryset = self.model.objects.filter(pk__in=pp)
        q = self.request.GET.get("search_fil", "")
        if q != "":
            queryset = queryset.filter(name__icontains=q)
        return queryset.order_by(*self.ordering)


@method_decorator(permission_required("laboratory.delete_laboratory"), name="dispatch")
class LaboratoryDeleteView(DeleteView):
    model = Laboratory
    template_name = "laboratory/laboratory_delete.html"
    lab_pk_field = "pk"

    def get_success_url(self):
        return reverse("laboratory:mylabs", kwargs={"org_pk": self.org})

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        msg_delete_relationship = "%s %s %s, %s" % (
            self.object.name,
            _("maintains a relationship with"),
            self.organization.name,
            _("are you sure you want to delete this relationship?"),
        )

        msg_delete = "%s %s %s, %s" % (
            self.object.name,
            _("was created for"),
            self.organization.name,
            _(
                "this action will involve deleting all relations with others organizations."
            ),
        )

        if self.org != self.object.organization.pk:
            msg_delete = msg_delete_relationship
        else:
            org_relations = OrganizationStructureRelations.objects.filter(
                content_type=ContentType.objects.filter(
                    app_label=self.object._meta.app_label,
                    model=self.object._meta.model_name,
                ).first(),
                object_id=self.object.pk,
            ).exclude(organization=self.organization)

            if org_relations.exists():
                organizations_name = list(
                    org_relations.values_list("organization__name", flat=True)
                )
                msg_delete += " %s %s." % (
                    _("The related organizations are: "),
                    str(organizations_name)[1:-1],
                )

            msg_delete += _(
                " Are you sure you want to delete this laboratory? This action is irreversible."
            )

        context["msg_delete"] = msg_delete
        return context

    def form_valid(self, form):
        user = self.request.user
        success_url = self.get_success_url()
        general_relation_list = []
        exclude_fields = [
            "LabOrgLogEntry",
            "LogEntry",
            "Permission",
            "ProfilePermission",
        ]
        cc = ContentType.objects.filter(
            app_label=self.object._meta.app_label, model=self.object._meta.model_name
        ).first()
        relations_filters = {"content_type": cc, "object_id": self.object.pk}
        orgrel_filters = {}
        orgrel_filters.update(relations_filters)
        if self.org == self.object.organization.pk:
            utils.organilab_logentry(
                user, self.object, DELETION, "laboratory", relobj=self.organization
            )
            FeedbackEntry.objects.filter(laboratory_id=self.object.pk).delete()
            for ro in cc._meta.related_objects:
                if ro.related_model.__name__ not in exclude_fields:
                    query = ro.related_model.objects.filter(
                        content_type=cc, object_id=self.object.pk
                    )
                    if query.exists():
                        general_relation_list.append(
                            {
                                "list": query,
                                "model_name": ro.related_model.__name__,
                                "change_message": "The relation in contenttype between %s and %s was deleted.",
                            },
                        )
                    # delete_relation_between_laboratory_with_other_models(
                    #    general_relation_list, user, self.object)
        else:
            relations_filters.update({"rol__organizationstructure": self.organization})
            orgrel_filters["organization"] = self.organization
            for ro in cc._meta.related_objects:
                if ro.related_model.__name__ not in exclude_fields:
                    try:
                        ro.related_model._meta.get_field("organization")
                        query = ro.related_model.objects.filter(**orgrel_filters)
                        if query.exists():
                            general_relation_list.append(
                                {
                                    "list": query,
                                    "model_name": ro.related_model.__name__,
                                    "change_message": "The relation in contenttype between %s and %s was deleted.",
                                },
                            )
                    except FieldDoesNotExist as e:
                        pass

                    # delete_relation_between_laboratory_with_other_models(
                    #    general_relation_list, user, self.object)

        # All profilepermissions related to this laboratory
        profilepermissions_list = ProfilePermission.objects.filter(**relations_filters)

        if profilepermissions_list:
            delete_profile_roles_related_to_laboratory(
                profilepermissions_list, self.organization, self.object
            )

        """
        relations_list = OrganizationStructureRelations.objects.filter(**orgrel_filters)
        myprocedure_list = MyProcedure.objects.filter(**orgrel_filters)
        inform_list = Inform.objects.filter(**orgrel_filters)

        general_relation_list = [
            {"list": relations_list, "model_name": "organization structure relations",
             "change_message": "The relation between %s and %s was deleted."},
            {"list": myprocedure_list, "model_name": "my procedure",
             "change_message": "My procedure %s in %s laboratory related to %s organization was deleted."},
            {"list": inform_list, "model_name": "inform",
             "change_message": "Inform %s in %s laboratory related to %s organization was deleted."}
        ]
        """
        delete_relation_between_laboratory_with_other_models(
            general_relation_list, user, self.object
        )

        if self.org == self.object.organization.pk:
            self.object.delete()

        return HttpResponseRedirect(success_url)


@method_decorator(permission_required("laboratory.do_report"), name="dispatch")
class HCodeReports(ListView):
    paginate_by = 15
    template_name = "laboratory/h_code_report.html"

    def get_queryset(self):
        q = None
        form = H_CodeForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data["hcode"]
        lista_reactivos = []
        if q:
            lista_reactivos = filter_by_user_and_hcode(self.request.user, q)
        return lista_reactivos

    def get_filter_params(self):
        dev = ""
        form = H_CodeForm(self.request.GET)
        if form.is_valid():
            for code in form.cleaned_data["hcode"]:
                dev += "&hcode=" + code.code
        return dev

    def get_context_data(self, **kwargs):
        context = super(HCodeReports, self).get_context_data(**kwargs)
        context["form"] = H_CodeForm(self.request.GET)
        context["params"] = self.get_filter_params()
        context["org_pk"] = self.org
        return context


@permission_required("laboratory.view_registeruserqr")
def get_pdf_register_user_qr(request, org_pk, lab_pk, pk):
    template = get_template("pdf/qr_pdf.html")

    lab = get_object_or_404(Laboratory, pk=lab_pk)
    obj_qr = get_object_or_404(RegisterUserQR, pk=pk)

    context = {
        "user": request.user,
        "datetime": now(),
        "title": _("Register User"),
        "rel_obj_title": _("Laboratory"),
        "rel_obj_msg": _("Use following QR code to register user in laboratory"),
        "rel_obj": lab,
        "rel_obj_name": lab.name,
        "obj_qr": obj_qr,
        "org_pk": org_pk,
        "domain": "file://%s" % (str(settings.MEDIA_ROOT).replace("/media/", ""),),
    }

    html = template.render(context=context)
    page = HTML(
        string=html, base_url=request.build_absolute_uri(), encoding="utf-8"
    ).write_pdf()
    response = HttpResponse(page, content_type="application/pdf")
    response["Content-Disposition"] = (
        'attachment; filename="register_user_qr_%s%s%s.pdf"' % (org_pk, lab_pk, pk)
    )
    return response


@method_decorator(
    permission_required("laboratory.view_registeruserqr"), name="dispatch"
)
class RegisterUserQRList(ListView):
    model = RegisterUserQR
    template_name = "laboratory/register_user_qr/register_user_qr_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        content_type = ContentType.objects.filter(
            app_label="laboratory", model="laboratory"
        ).first()

        organization = OrganizationStructure.objects.get(pk=self.org)
        org_base_list = list(organization.descendants(include_self=True))

        if self.org and self.lab:
            queryset = queryset.filter(
                organization_register__in=org_base_list,
                content_type=content_type,
                object_id=self.lab,
            ).order_by("creation_date", "last_update", "organization_register__name")
        else:
            queryset = queryset.none()
        return queryset


@permission_required("laboratory.add_registeruserqr")
def manage_register_qr(request, org_pk, lab_pk, pk=None):
    obj = None
    user = request.user
    schema = request.scheme + "://"
    domain = schema + request.get_host()
    action = ADDITION
    new_obj = True

    if pk:
        obj = get_object_or_404(RegisterUserQR, pk=pk)
        action = CHANGE
        new_obj = False

    if request.method == "POST":
        form = RegisterUserQRForm(
            request.POST,
            instance=obj,
            obj=obj,
            org_pk=org_pk,
            lab_pk=lab_pk,
            new_obj=new_obj,
        )
        if form.is_valid():
            organization_register = form.cleaned_data["organization_register"]
            instance = form.save()
            url = domain + reverse(
                "laboratory:login_register_user_qr",
                kwargs={
                    "org_pk": organization_register.pk,
                    "lab_pk": lab_pk,
                    "pk": instance.pk,
                },
            )
            instance.url = url
            img, file = utils.generate_QR_img_file(
                url, user, extension_file=".svg", file_name="qrcode"
            )
            instance.register_user_qr = img
            instance.save()
            file.close()
            messages.success(request, _("Element saved successfully"))
            utils.organilab_logentry(
                request.user,
                instance,
                action,
                "register user QR",
                changed_data=form.changed_data,
                relobj=lab_pk,
            )
            return redirect(
                reverse(
                    "laboratory:list_register_user_qr",
                    kwargs={"org_pk": org_pk, "lab_pk": lab_pk},
                )
            )
        else:
            messages.error(request, _("Error, form is invalid"))
    else:

        if obj:
            form = RegisterUserQRForm(
                instance=obj, obj=obj, org_pk=org_pk, lab_pk=lab_pk, new_obj=new_obj
            )
        else:
            content_type = ContentType.objects.filter(
                app_label="laboratory", model="laboratory"
            ).first()

            initial_form = {
                "created_by": user,
                "organization_creator": org_pk,
                "object_id": lab_pk,
                "content_type": content_type.pk,
                "code": str(uuid.uuid4())[-4:],
            }

            form = RegisterUserQRForm(
                initial=initial_form,
                obj=obj,
                org_pk=org_pk,
                lab_pk=lab_pk,
                new_obj=new_obj,
            )

    context = {"form": form, "obj": obj, "org_pk": org_pk, "laboratory": lab_pk}

    return render(
        request, "laboratory/register_user_qr/manage_register_qr.html", context=context
    )


@method_decorator(
    permission_required("laboratory.delete_registeruserqr"), name="dispatch"
)
class RegisterUserQRDeleteView(DeleteView):
    model = RegisterUserQR
    template_name = "laboratory/register_user_qr/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "laboratory:list_register_user_qr",
            kwargs={"org_pk": self.org, "lab_pk": self.lab},
        )

    def form_valid(self, form):
        success_url = self.get_success_url()
        utils.organilab_logentry(
            self.request.user, self.object, DELETION, "register user QR"
        )
        self.object.delete()
        messages.success(self.request, _("Element was deleted successfully"))
        return HttpResponseRedirect(success_url)


def get_logentry_from_registeruserqr(request, org_pk, lab_pk, pk):
    register_qr = get_object_or_404(RegisterUserQR, pk=pk)
    return render(
        request,
        "laboratory/register_user_qr/logentry_list.html",
        context={
            "org_pk": org_pk,
            "laboratory": lab_pk,
            "qr_obj": register_qr.pk,
        },
    )


def login_register_user_qr(request, org_pk, lab_pk, pk):
    user_qr = get_object_or_404(RegisterUserQR, pk=pk)
    return render(
        request,
        "laboratory/register_user_qr/login_register_user.html",
        context={
            "pk": pk,
            "org_pk": org_pk,
            "lab_pk": lab_pk,
            "login_form": LoginForm(),
            "password_form": PasswordCodeForm(user=None, code=user_qr.code),
            "register_form": RegisterForm(obj=None),
            "instance": 0,
            "next": reverse(
                "laboratory:redirect_user_to_labindex",
                kwargs={"org_pk": org_pk, "lab_pk": lab_pk, "pk": pk},
            ),
        },
    )


def add_user_to_rel_obj(request, user, org_pk, lab_pk, qr_obj, id_card=None):
    login(request, user)
    lab = get_object_or_404(Laboratory, pk=lab_pk)
    org = get_object_or_404(OrganizationStructure, pk=org_pk)
    content_type = ContentType.objects.filter(
        app_label="laboratory", model="laboratory"
    ).first()

    has_profile = utils.check_has_profile(user)

    if not has_profile and id_card:
        profile = Profile.objects.create(
            user=user, id_card=id_card, job_position=_("Student")
        )
        organilab_logentry(
            user,
            profile,
            ADDITION,
            "profile",
            changed_data=["user", "phone_number", "id_card", "job_position"],
            relobj=org_pk,
        )

        # Register Log - relobj(USER) - action(ADDITION)
        organilab_logentry(
            user,
            user,
            ADDITION,
            "user",
            changed_data=["Register", qr_obj.pk],
            relobj=org,
        )
    else:
        profile = user.profile

    profile.laboratories.add(lab)

    pp = ProfilePermission.objects.filter(
        profile=profile, content_type=content_type, object_id=lab_pk
    )

    if not pp.exists():

        pp = ProfilePermission.objects.create(
            profile=profile, content_type=content_type, object_id=lab_pk
        )
        pp.save()
        organilab_logentry(
            user,
            pp,
            ADDITION,
            "profile permission",
            changed_data=["profile", "content_type", "object_id"],
            relobj=org_pk,
        )
    else:
        pp = pp.first()
        organilab_logentry(
            user, pp, CHANGE, "profile permission", changed_data=["rol"], relobj=org_pk
        )
    pp.rol.add(qr_obj.role)

    user_org = UserOrganization.objects.filter(organization=org, user=user)

    if not user_org.exists():
        user_org = UserOrganization.objects.create(organization=org, user=user)
        organilab_logentry(
            user,
            user_org,
            ADDITION,
            "user organization",
            changed_data=["organization", "user"],
            relobj=org_pk,
        )

    # Login Log - relobj(USER) - action(CHANGE)
    organilab_logentry(
        user, user, CHANGE, "user", changed_data=["Login", qr_obj.pk], relobj=org
    )


def redirect_user_to_labindex(request, org_pk, lab_pk, pk):
    user_qr = get_object_or_404(RegisterUserQR, pk=pk)
    add_user_to_rel_obj(request, request.user, org_pk, lab_pk, user_qr, id_card=None)
    return redirect(
        reverse("laboratory:labindex", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
    )


def create_user_qr(request, org_pk, lab_pk, pk, user=None):
    user_qr = get_object_or_404(RegisterUserQR, pk=pk)
    password_form = PasswordCodeForm(user=None, code=user_qr.code)
    register_form = RegisterForm(obj=None)
    instance, obj, context = None, None, {}

    if request.method == "POST":
        if user:
            instance = get_object_or_404(User, pk=user)
            obj = instance.pk
            context.update({"instance": instance.pk})
        register_form = RegisterForm(request.POST, instance=instance, obj=obj)

        if register_form.is_valid():
            instance = register_form.save(commit=False)
            instance.username = register_form.cleaned_data["email"]
            if not user_qr.activate_user:
                instance.is_active = False
            instance.save()
            if not user:
                organilab_logentry(
                    instance,
                    instance,
                    ADDITION,
                    "user",
                    changed_data=[
                        "username",
                        "first_name",
                        "last_name",
                        "email",
                        "password",
                    ],
                    relobj=org_pk,
                )

                id_card = register_form.cleaned_data["id_card"]
                add_user_to_rel_obj(request, instance, org_pk, lab_pk, user_qr, id_card)

            password_form = PasswordCodeForm(
                request.POST, user=instance, code=user_qr.code
            )
            if password_form.is_valid():
                instance.set_password(password_form.cleaned_data["password"])
                instance.save()
                login(request, instance)
                return redirect(
                    reverse(
                        "laboratory:labindex",
                        kwargs={"org_pk": org_pk, "lab_pk": lab_pk},
                    )
                )

    context.update(
        {
            "pk": pk,
            "org_pk": org_pk,
            "lab_pk": lab_pk,
            "login_form": LoginForm(),
            "password_form": password_form,
            "register_form": register_form,
            "next": reverse(
                "laboratory:redirect_user_to_labindex",
                kwargs={"org_pk": org_pk, "lab_pk": lab_pk, "pk": pk},
            ),
        }
    )
    return render(
        request, "laboratory/register_user_qr/login_register_user.html", context=context
    )
