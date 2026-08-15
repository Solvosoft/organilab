import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django_celery_results.models import TaskResult
from djgentelella.models import ChunkedUpload
from django.contrib.auth.decorators import permission_required, login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from djgentelella.decorators.perms import any_permission_required
from weasyprint import HTML

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from sga.forms import (
    ProviderSGAForm,
    RecipientSizeForm,
)
from sga.models import Substance, DisplayLabel, SGAComplement, SecurityLeaf
from sga.models import SubstanceCharacteristics, TemplateSGA, Label, ReviewSubstance
from sga.models import SubstanceObservation
from sga.models import WarningWord, DangerIndication, PrudenceAdvice
from .forms import (
    DangerIndicationForm,
    WarningWordForm,
    PrudenceAdviceForm,
    SendToReviewForm,
)
from .forms import (
    ObservationForm,
    SecurityLeafForm,
    SustanceObjectForm,
    SustanceCharacteristicsForm,
    ReviewSubstanceForm,
)
from ...api.serializers import (
    SubstanceObservationSerializer,
    SubstanceObservationDescriptionSerializer,
)
from ...tasks import extract_sds_for_characteristics
from ...utils import notify_request_created, create_object_notification


@login_required
@permission_required(
    ("laboratory.change_object", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def create_edit_sustance(request, org_pk, pk=None):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    instance = None
    suscharobj = None
    postdata = None
    filesdata = None

    if pk:
        instance = Substance.objects.filter(pk=pk, organization=organization).first()

    if instance:
        suscharobj = SubstanceCharacteristics.objects.filter(
            substance=instance
        ).first()

    if request.method == "POST":
        postdata = request.POST
        filesdata = request.FILES

    objform = SustanceObjectForm(postdata, instance=instance)
    suschacform = SustanceCharacteristicsForm(
        postdata, files=filesdata, instance=suscharobj
    )
    if request.method == "POST":

        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.created_by = request.user
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.substance = obj
            label, created = Label.objects.get_or_create(substance=obj)
            complement, complement_created = SGAComplement.objects.get_or_create(
                substance=obj
            )
            leaf, leaf_created = SecurityLeaf.objects.get_or_create(substance=obj)
            template = TemplateSGA.objects.filter(is_default=True).first()
            personal, created = DisplayLabel.objects.get_or_create(
                label=label, template=template, created_by=request.user
            )

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            # if isValidate_molecular_formula(molecular_formula):
            # #suscharinst.valid_molecular_formula = True
            instance = obj
            suscharinst.save()
            suschacform.save_m2m()
            organilab_logentry(
                request.user,
                obj,
                CHANGE,
                "substance",
                changed_data=objform.changed_data,
                change_message=_("Updated substance '%(name)s'")
                % {"name": obj.comercial_name},
            )
            organilab_logentry(
                request.user,
                suscharinst,
                CHANGE,
                "substance characteristics",
                changed_data=suschacform.changed_data,
                change_message=_("Updated characteristics of substance '%(name)s'")
                % {"name": obj.comercial_name},
            )

            return redirect(
                reverse(
                    "sga:step_four", kwargs={"org_pk": org_pk, "substance": instance.pk}
                )
            )

    # Abrir el asistente no crea nada: la sustancia nace en el primer POST válido
    # o al subir la ficha. Crearla al entrar dejaría una fila muerta por cada
    # persona que mira el formulario y se va sin guardar.
    template_pk = None
    if instance:
        label, created_label = Label.objects.get_or_create(substance=instance)
        template = TemplateSGA.objects.filter(is_default=True).first()
        personal, created = DisplayLabel.objects.get_or_create(
            label=label, template=template, created_by=request.user
        )
        SecurityLeaf.objects.get_or_create(substance=instance)
        template_pk = personal.pk

    return render(
        request,
        "sga/substance/create_sustance.html",
        {
            "objform": objform,
            "suschacform": suschacform,
            "instance": instance,
            "step": 1,
            "template": template_pk,
            "substance": instance.pk if instance else None,
            "pk": instance.pk if instance else None,
            "org_pk": org_pk,
        },
    )


@login_required
@permission_required(
    ("sga.view_substance", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def get_substances(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    context = {"org_pk": org_pk}
    return render(request, "sga/substance/list_substance.html", context=context)


@login_required
@permission_required(
    ("sga.view_substance", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def get_list_substances(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    showapprove = True if request.GET.get("showapprove") else False
    form = ReviewSubstanceForm()
    context = {"form": form, "org_pk": org_pk, "showapprove": showapprove}
    return render(request, "sga/substance/check_substances.html", context=context)


@login_required
@permission_required(
    ("sga.change_substance", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def approve_substances(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    review_subs = get_object_or_404(ReviewSubstance, pk=pk)
    substance_name = (
        review_subs.substance.comercial_name if review_subs.substance else ""
    )

    # La vista es alcanzable por GET, así que un doble clic o una precarga del
    # navegador la ejecutarían dos veces y crearían dos objetos de inventario
    # para la misma sustancia.
    if review_subs.is_approved:
        messages.info(
            request,
            _("Substance '%(name)s' was already approved.") % {"name": substance_name},
        )
        return redirect(reverse("sga:approved_substance", kwargs={"org_pk": org_pk}))

    with transaction.atomic():
        review_subs.is_approved = True
        review_subs.created_by = request.user
        review_subs.save()

        if review_subs.substance:
            review_subs.substance.status = Substance.APPROVED
            review_subs.substance.save(update_fields=["status"])
            create_object_notification(review_subs.substance, user=request.user)

    organilab_logentry(
        request.user,
        review_subs,
        CHANGE,
        "review substance",
        changed_data=["is_approved", "created_by", "status"],
        change_message=_("Approved substance '%(name)s'") % {"name": substance_name},
    )
    messages.success(
        request,
        _("Substance '%(name)s' has been approved.") % {"name": substance_name},
    )
    return redirect(reverse("sga:approved_substance", kwargs={"org_pk": org_pk}))


@login_required
@permission_required(
    ("sga.delete_substance", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def delete_substance(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    substance = get_object_or_404(Substance, pk=pk)
    substance_name = substance.comercial_name
    Label.objects.filter(substance=substance).delete()
    organilab_logentry(
        request.user,
        substance,
        DELETION,
        "substance",
        changed_data=["comercial_name", "uipa_name", "cas_id_number"],
        change_message=_("Deleted substance '%(name)s'") % {"name": substance_name},
    )
    substance.delete()
    messages.success(request, _("The substance is removed successfully"))
    return redirect(reverse("sga:get_substance", kwargs={"org_pk": org_pk}))


@login_required
@permission_required(
    ("sga.change_substance", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def detail_substance(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    substance = get_object_or_404(Substance, pk=pk)

    step = 1
    if "step" in request.session:
        step = request.session["step"]
        del request.session["step"]

    observation = SubstanceObservation.objects.filter(
        substance=substance, substance__organization=org_pk
    )
    context = {
        "object": substance,
        "observations": observation,
        "observationForm": ObservationForm(),
        "step": step,
        "url": reverse(
            "sga:add_observation", kwargs={"org_pk": org_pk, "substance": pk}
        ),
        "org_pk": org_pk,
    }
    return render(request, "sga/substance/detail.html", context=context)


@login_required
@permission_required(
    ("sga.change_securityleaf", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def step_four(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    security_leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    if request.method == "POST":
        form = SecurityLeafForm(request.POST, instance=security_leaf)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(
                request.user,
                obj,
                CHANGE,
                "security leaf",
                changed_data=form.changed_data,
            )

            return redirect(
                reverse(
                    "sga:send_to_review",
                    kwargs={"org_pk": org_pk, "substance": substance},
                )
            )

    form = SecurityLeafForm(instance=security_leaf)

    context = {
        "step": 2,
        "form": form,
        "provider_form": ProviderSGAForm(),
        "substance": substance,
        "org_pk": org_pk,
        "pk": substance,
    }
    return render(request, "sga/substance/step_four.html", context=context)


@login_required
@permission_required("auth_and_perms.institution_can_access", raise_exception=True)
def security_leaf_pdf(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    component = SGAComplement.objects.filter(substance__pk=substance).first()

    if leaf:
        template = get_template("sga/substance/security_leaf_pdf.html")
        context = {
            "leaf": leaf,
            "substance": leaf.substance,
            "provider": leaf.provider,
            "component": component,
            "date_print": timezone.now(),
            "user": request.user,
            "date_check": leaf.created_at.strftime("%Y-%m-%d"),
            "org_pk": org_pk,
        }
        html_template = template.render(context)
        pdf = HTML(
            string=html_template, base_url=request.build_absolute_uri()
        ).write_pdf()
        return HttpResponse(pdf, content_type="application/pdf")


@login_required
@any_permission_required(
    ["sga.add_prudenceadvice", "sga.add_dangerindication", "sga.add_warningword"],
    raise_exception=True,
)
def add_sga_complements(request, org_pk, element):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    perm = {
        "warning": "sga.add_warningword",
        "danger": "sga.add_dangerindication",
        "prudence": "sga.add_prudenceadvice",
    }

    if not request.user.has_perm(perm[element]):
        raise PermissionDenied

    urls = {
        "warning": "sga:add_warning_word",
        "danger": "sga:add_danger_indication",
        "prudence": "sga:add_prudence_advice",
    }
    view_urls = {
        "warning": "sga:warning_words",
        "danger": "sga:danger_indications",
        "prudence": "sga:prudence_advices",
    }
    titles = {
        "warning": _("Create Warning Word"),
        "danger": _("Create Danger Indication"),
        "prudence": _("Create Prudence Advice"),
    }

    forms = {
        "warning": WarningWordForm(),
        "danger": DangerIndicationForm(),
        "prudence": PrudenceAdviceForm(),
    }
    if request.method == "POST":
        forms = {
            "warning": WarningWordForm(request.POST),
            "danger": DangerIndicationForm(request.POST),
            "prudence": PrudenceAdviceForm(request.POST),
        }
        form = forms[element]

        if form.is_valid():
            form.save()
            return redirect(reverse(view_urls[element], kwargs={"org_pk": org_pk}))

    else:
        form = forms[element]

    context = {
        "form": form,
        "url": reverse(urls[element], kwargs={"org_pk": org_pk}),
        "view_url": reverse(view_urls[element], kwargs={"org_pk": org_pk}),
        "title": titles[element],
    }

    return render(request, "sga/substance/sga_components.html", context=context)


@login_required
@permission_required("sga.view_dangerindication", raise_exception=True)
def view_danger_indications(request, org_pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    listado = DangerIndication.objects.all()
    return render(
        request,
        "sga/substance/danger_indication.html",
        context={"listado": listado, "org_pk": org_pk},
    )


@login_required
@permission_required("sga.view_warningword", raise_exception=True)
def view_warning_words(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    form = WarningWordForm
    return render(
        request,
        "sga/substance/warning_words.html",
        context={"form": form, "org_pk": org_pk},
    )


@permission_required(
    ("auth_and_perms.institution_can_access", "sga.view_recipientsize"),
    raise_exception=True,
)
def view_recipient_size(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    return render(
        request,
        "sga/recipient_size.html",
        context={"org_pk": org_pk, "form": RecipientSizeForm},
    )


@login_required
@permission_required("sga.view_prudenceadvice", raise_exception=True)
def view_prudence_advices(request, org_pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    form = PrudenceAdviceForm
    return render(
        request,
        "sga/substance/prudence_advice.html",
        context={"form": form, "org_pk": org_pk},
    )


@login_required
@permission_required("sga.view_substanceobservation", raise_exception=True)
def add_observation(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    substance_obj = get_object_or_404(
        Substance, pk=substance, organization__pk=org_pk
    )
    # Ojo: este "step" es la pestaña del detalle de la sustancia (1=Detalle,
    # 2=Observaciones), no un paso del asistente. Lo consume detail_substance.
    request.session["step"] = 2

    if substance and request.method == "POST":
        form = ObservationForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.substance = substance_obj
            obj.created_by = request.user
            obj.save()
            organilab_logentry(
                request.user,
                obj,
                ADDITION,
                "substance observation",
                changed_data=form.changed_data,
                change_message=_("Added observation to substance '%(name)s'")
                % {"name": substance_obj.comercial_name},
            )
            messages.success(request, _("Observation was saved successfully"))
        else:
            messages.error(request, _("Invalid Form"))
    return redirect(
        reverse("sga:detail_substance", kwargs={"org_pk": org_pk, "pk": substance})
    )


@login_required
@permission_required("sga.change_substanceobservation", raise_exception=True)
def update_observation(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    response = {"status": False}

    if request.method == "POST":
        serializer = SubstanceObservationDescriptionSerializer(
            data=request.POST, context={"organization_id": org_pk}
        )

        if serializer.is_valid():
            substance_obj = serializer.validated_data["pk"]
            substance_obj.description = serializer.validated_data["description"]
            substance_obj.save()
            organilab_logentry(
                request.user,
                substance_obj,
                CHANGE,
                "substance observation",
                changed_data=["description"],
                change_message=_("Updated substance observation description"),
            )
            request.session["step"] = 2
            response["status"] = True
    return JsonResponse(response)


@login_required
@permission_required("sga.delete_substanceobservation", raise_exception=True)
def delete_observation(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    response = {"status": False}

    if request.method == "POST":
        serializer = SubstanceObservationSerializer(
            data=request.POST, context={"organization_id": org_pk}
        )

        if serializer.is_valid():
            substance_obj = serializer.validated_data["pk"]
            organilab_logentry(
                request.user,
                substance_obj,
                DELETION,
                "substance observation",
                changed_data=["description", "substance"],
                change_message=_("Deleted substance observation"),
            )
            substance_obj.delete()
            request.session["step"] = 2
            response["status"] = True
    return JsonResponse(response)


@login_required
@permission_required("sga.change_warningword", raise_exception=True)
def change_warning_word(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    instance = get_object_or_404(WarningWord, pk=pk)
    context = {}

    if request.method == "POST":
        form = WarningWordForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(
                request.user,
                obj,
                CHANGE,
                "warning word",
                changed_data=form.changed_data,
                change_message=_("Updated warning word '%(name)s'")
                % {"name": obj.name},
            )
            return redirect(reverse("sga:warning_words", kwargs={"org_pk": org_pk}))
    else:
        form = WarningWordForm(instance=instance)
        context = {
            "form": form,
            "view_url": reverse("sga:warning_words", kwargs={"org_pk": org_pk}),
            "title": _("Update the Warning Word") + " " + instance.name,
            "url": reverse(
                "sga:update_warning_word", kwargs={"org_pk": org_pk, "pk": instance.pk}
            ),
            "org_pk": org_pk,
        }
    return render(request, "sga/substance/sga_components.html", context=context)


@login_required
@permission_required("sga.change_prudenceadvice", raise_exception=True)
def change_prudence_advice(request, org_pk, pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    instance = get_object_or_404(PrudenceAdvice, pk=pk)
    context = {}

    if request.method == "POST":
        form = PrudenceAdviceForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(
                request.user,
                obj,
                CHANGE,
                "prudence advice",
                changed_data=form.changed_data,
                change_message=_("Updated prudence advice '%(code)s'")
                % {"code": obj.code},
            )
            return redirect(
                reverse(
                    "sga:prudence_advices",
                    kwargs={
                        "org_pk": org_pk,
                    },
                )
            )
    else:
        form = PrudenceAdviceForm(instance=instance)
        context = {
            "form": form,
            "view_url": reverse(
                "sga:prudence_advices",
                kwargs={
                    "org_pk": org_pk,
                },
            ),
            "title": _("Update the Prudence Advice") + " " + instance.name,
            "url": reverse(
                "sga:update_prudence_advice",
                kwargs={"org_pk": org_pk, "pk": instance.pk},
            ),
        }
    return render(request, "sga/substance/sga_components.html", context=context)


@login_required
@permission_required("sga.change_dangerindication", raise_exception=True)
def change_danger_indication(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    instance = get_object_or_404(DangerIndication, pk=pk)
    context = {}

    if request.method == "POST":
        form = DangerIndicationForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(
                request.user,
                obj,
                CHANGE,
                "danger indication",
                changed_data=form.changed_data,
                change_message=_("Updated danger indication '%(code)s'")
                % {"code": obj.code},
            )
            return redirect(
                reverse("sga:danger_indications", kwargs={"org_pk": org_pk})
            )
    else:
        form = DangerIndicationForm(instance=instance)
        context = {
            "form": form,
            "view_url": reverse("sga:danger_indications", kwargs={"org_pk": org_pk}),
            "title": _("Update the Danger indication") + " " + instance.code,
            "url": reverse(
                "sga:update_danger_indication",
                kwargs={"org_pk": org_pk, "pk": instance.pk},
            ),
            "org_pk": org_pk,
        }
    return render(request, "sga/substance/sga_components.html", context=context)


@login_required
@permission_required("sga.add_provider", raise_exception=True)
def add_sga_provider(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    response = {"status": False}

    if request.method == "POST":
        form = ProviderSGAForm(request.POST)

        if form.is_valid():
            provider = form.save(commit=False)
            provider.save()
            organilab_logentry(
                request.user,
                provider,
                ADDITION,
                "provider",
                changed_data=form.changed_data,
            )
            response.update(
                {"result": True, "provider_pk": provider.pk, "provider": provider.name}
            )
    return JsonResponse(response)


@login_required
@permission_required(
    ("sga.change_substance", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def sent_to_review(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    substance = get_object_or_404(Substance, pk=substance, organization__pk=org_pk)
    user = request.user

    characteristics = SubstanceCharacteristics.objects.filter(
        substance=substance
    ).first()
    has_security_sheet = bool(characteristics and characteristics.security_sheet)
    form = None

    if request.method == "POST":
        if not has_security_sheet:
            messages.error(
                request,
                _(
                    "You must upload a security sheet (SDS) before sending the substance for review."
                ),
            )
            # La ficha se sube en el paso 1, no aquí: se devuelve al usuario al
            # sitio donde puede aportarla.
            return redirect(
                reverse(
                    "sga:update_substance",
                    kwargs={"pk": substance.pk, "org_pk": org_pk},
                )
            )

        form = SendToReviewForm(
            request.POST, instance=substance, user=request.user, org_pk=org_pk
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = Substance.UNDER_REVIEW
            obj.save()
            form.save_m2m()

            rev_sub = ReviewSubstance.objects.create(
                substance=obj,
                organization=form.cleaned_data["organization"],
                created_by=request.user,
            )
            notify_request_created(
                {"name": rev_sub.substance.comercial_name},
                request.user,
                url=reverse("sga:approved_substance", kwargs={"org_pk": org_pk}),
            )
            organilab_logentry(
                user,
                obj,
                CHANGE,
                "substance",
                changed_data=form.changed_data + ["status"],
                change_message=_("Sent substance '%(name)s' for review")
                % {"name": substance.comercial_name},
            )
            organilab_logentry(
                request.user,
                rev_sub,
                ADDITION,
                "review substance",
                changed_data=["substance", "organization", "create_by"],
                change_message=_("Created review substance"),
            )

            messages.success(
                request,
                _("Substance '%(name)s' has been sent for review.")
                % {"name": substance.comercial_name},
            )
            return redirect(
                reverse(
                    "sga:get_substance",
                    kwargs={
                        "org_pk": org_pk,
                    },
                )
            )

    if not has_security_sheet:
        messages.warning(
            request,
            _("Security sheet (SDS) is required to send this substance for review."),
        )

    context = {
        # Si el POST no validó se reutiliza el formulario ligado, para que el
        # usuario vea los errores en lugar de una página recargada en blanco.
        "form": form
        or SendToReviewForm(
            instance=substance, user=request.user, org_pk=org_pk
        ),
        "organization": org_pk,
        "substance": substance.pk,
        "org_pk": org_pk,
        "step": 3,
        "has_security_sheet": has_security_sheet,
    }
    return render(request, "sga/substance/send_to_review.html", context)


def _resolve_uploaded_sheet(request):
    """Obtiene la ficha tanto del widget de gentelella como de un envío directo.

    El widget `genwidgets.FileInput` sube el archivo por trozos a su propio
    endpoint y deja en el POST un token JSON que apunta al `ChunkedUpload`; ese
    es el camino normal desde el asistente. Se acepta además un fichero directo
    en `request.FILES` para poder llamar al endpoint sin pasar por el widget.
    """
    token = request.POST.get("security_sheet") or request.POST.get("token")
    if token:
        try:
            upload_id = json.loads(token).get("token")
        except (TypeError, ValueError):
            upload_id = token
        chunked = ChunkedUpload.objects.filter(upload_id=upload_id).first()
        if chunked:
            uploaded = chunked.get_uploaded_file()
            chunked.delete()
            return uploaded

    return request.FILES.get("security_sheet")


@login_required
@permission_required(
    ("sga.change_substancecharacteristics", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def upload_sds(request, org_pk, pk=None):
    """Recibe la ficha de seguridad del paso 1 y encola su extracción.

    Si todavía no hay sustancia, se crea aquí. La ficha necesita colgar de algo
    para guardarse, y subirla es un acto deliberado: por eso es uno de los dos
    momentos —junto al primer guardado— en que la sustancia nace.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": _("Method not allowed")}, status=405)

    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    uploaded = _resolve_uploaded_sheet(request)
    if not uploaded:
        return JsonResponse(
            {"ok": False, "message": _("No security sheet was received.")}, status=400
        )

    substance = None
    if pk:
        substance = get_object_or_404(Substance, pk=pk, organization=organization)

    with transaction.atomic():
        if substance is None:
            substance = Substance.objects.create(
                created_by=request.user, organization=organization
            )
            organilab_logentry(
                request.user,
                substance,
                ADDITION,
                "substance",
                changed_data=["created_by", "organization"],
                change_message=_("Created new substance"),
            )

        characteristics, _created = SubstanceCharacteristics.objects.get_or_create(
            substance=substance
        )
        characteristics.security_sheet = uploaded
        characteristics.save(update_fields=["security_sheet"])

    task = extract_sds_for_characteristics.delay(
        characteristics.pk, user_pk=request.user.pk
    )

    return JsonResponse(
        {
            "ok": True,
            "substance_pk": substance.pk,
            "sc_pk": characteristics.pk,
            "task_id": task.task_id,
        }
    )


@login_required
@permission_required(
    ("sga.view_substancecharacteristics", "auth_and_perms.institution_can_access"),
    raise_exception=True,
)
def sds_task_status(request, org_pk):
    """Estado de la extracción encolada, para que el paso 1 pueda sondearla."""
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    user_is_allowed_on_organization(request.user, organization)

    task_id = request.GET.get("task_id")
    if not task_id:
        return JsonResponse({"state": "PENDING", "end": False})

    result = TaskResult.objects.filter(task_id=task_id).first()
    state = result.status if result else "PENDING"
    response = {"state": state, "end": state in ("SUCCESS", "FAILURE", "REVOKED")}

    if state == "SUCCESS" and result:
        try:
            response["result"] = json.loads(result.result)
        except (TypeError, ValueError):
            response["result"] = None

    return JsonResponse(response)
