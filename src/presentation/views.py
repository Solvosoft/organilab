import json
import logging
import re

from async_notifications.utils import send_email_from_template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from auth_and_perms.models import ProfilePermission
from presentation.forms import DonateForm, FeedbackEntryForm
from presentation.models import (
    Donation,
    FeedbackEntry,
    Tutorial,
    TutorialProgress,
)

logger = logging.getLogger("organilab")


@never_cache
@login_required
@permission_required("auth_and_perms.institution_can_access", raise_exception=True)
def index_tutorial(request, org_pk):
    user = request.user
    user_rol_ids = set()
    try:
        from laboratory.models import OrganizationStructure

        org_ct = ContentType.objects.get_for_model(OrganizationStructure)
        for pp in ProfilePermission.objects.filter(
            profile=user.profile, content_type=org_ct, object_id=org_pk
        ):
            user_rol_ids.update(pp.rol.values_list("id", flat=True))
    except Exception:
        pass

    tutorials = (
        Tutorial.objects.filter(is_active=True)
        .prefetch_related("steps", "target_roles")
        .order_by("chapter", "order")
    )

    filtered = []
    for t in tutorials:
        target_ids = set(t.target_roles.values_list("id", flat=True))
        if target_ids and not target_ids.intersection(user_rol_ids):
            continue
        filtered.append(t)

    progress_map = {}
    for tp in TutorialProgress.objects.filter(user=user):
        progress_map[tp.tutorial_id] = tp

    # Get first lab of the org to resolve lab-dependent URLs
    lab_pk = None
    try:
        from laboratory.models import Laboratory

        lab = Laboratory.objects.filter(organization=org_pk).first()
        if lab:
            lab_pk = lab.pk
    except Exception:
        pass

    effective_org_pk = org_pk
    if not effective_org_pk:
        try:
            from laboratory.models import OrganizationStructure

            root_ct = ContentType.objects.get_for_model(OrganizationStructure)
            effective_org_pk = (
                ProfilePermission.objects.filter(
                    profile=user.profile,
                    content_type=root_ct,
                )
                .values_list("object_id", flat=True)
                .first()
            )
        except Exception:
            pass

    # Get first procedure of the lab to resolve procedure-dependent URLs
    procedure_pk = None
    if lab_pk:
        try:
            from academic.models import Procedure

            proc = Procedure.objects.filter(laboratory__pk=lab_pk).first()
            if proc:
                procedure_pk = proc.pk
        except Exception:
            pass

    def resolve_tutorial_url(url_name):
        kwargs_candidates = [
            {"org_pk": effective_org_pk, "lab_pk": lab_pk} if lab_pk else None,
            {"pk": procedure_pk} if procedure_pk else None,
            {"org_pk": effective_org_pk, "pk": effective_org_pk},
            {"org_pk": effective_org_pk, "status": 0},
            {"org_pk": effective_org_pk},
            {"pk": effective_org_pk},
            {},
        ]
        for kwargs in kwargs_candidates:
            if kwargs is None:
                continue
            try:
                url = reverse(url_name, kwargs=kwargs)
                if not kwargs.get("org_pk"):
                    url = f"{url}?org_pk={effective_org_pk}"
                return url
            except Exception:
                continue
        return None

    chapters = {}
    for t in filtered:
        chapter = t.get_chapter_display()
        if chapter not in chapters:
            chapters[chapter] = []
        tp = progress_map.get(t.id)
        first_url_name = t.url_name.split(",")[0].strip()
        target_url = resolve_tutorial_url(first_url_name)
        chapters[chapter].append(
            {
                "tutorial": t,
                "progress": tp,
                "step_count": t.steps.count(),
                "target_url": target_url,
            }
        )

    return render(
        request,
        "tutorial.html",
        context={
            "org_pk": org_pk,
            "chapters": chapters,
            "capacitation_url": settings.CAPACITATION_URL,
        },
    )


@login_required
@require_POST
def tutorial_progress_api(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    tutorial_id = data.get("tutorial_id")
    step_order = data.get("step_order", 0)
    completed = data.get("completed", False)
    dismissed = data.get("dismissed", False)

    if not tutorial_id:
        return JsonResponse({"error": "tutorial_id required"}, status=400)

    try:
        tutorial = Tutorial.objects.get(pk=tutorial_id)
    except Tutorial.DoesNotExist:
        return JsonResponse({"error": "Tutorial not found"}, status=404)

    progress, created = TutorialProgress.objects.get_or_create(
        user=request.user,
        tutorial=tutorial,
    )

    progress.current_step = step_order
    if completed:
        progress.completed = True
        progress.completed_at = timezone.now()
    if dismissed:
        progress.dismissed = True
    progress.save()

    return JsonResponse({"ok": True})


@login_required
@require_POST
def tutorial_toggle_api(request):
    try:
        profile = request.user.profile
    except Exception:
        return JsonResponse({"error": "No profile"}, status=400)

    profile.show_tutorials = not profile.show_tutorials
    profile.save(update_fields=["show_tutorials"])

    return JsonResponse({"show_tutorials": profile.show_tutorials})


@login_required
@require_POST
def tutorial_reactivate_api(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    tutorial_id = data.get("tutorial_id")
    if not tutorial_id:
        return JsonResponse({"error": "tutorial_id required"}, status=400)

    TutorialProgress.objects.filter(user=request.user, tutorial_id=tutorial_id).update(
        dismissed=False, completed=False, current_step=0, completed_at=None
    )

    response = JsonResponse({"ok": True})
    response.set_cookie(
        "tutorial_reactivated", tutorial_id, max_age=300, samesite="Lax"
    )
    return response


@method_decorator(login_required, name="dispatch")
class FeedbackView(PermissionRequiredMixin, CreateView):
    template_name = "feedback/feedbackentry_form.html"
    model = FeedbackEntry
    permission_required = "auth_and_perms.institution_can_access"
    form_class = FeedbackEntryForm

    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if "org_pk" in request.GET:
            self.org = int(request.GET["org_pk"])
        if "lab_pk" in request.GET:
            self.lab = int(request.GET["lab_pk"])
        return CreateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FeedbackView, self).get_context_data()
        context["lab_pk"] = self.lab
        context["org_pk"] = self.org
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            lab_pk = int(self.request.POST.get("lab_pk", 0))
            org_pk = int(self.request.POST.get("org_pk", 0))
        except Exception as e:
            logger.error("Error parsing organization or lab id", exc_info=e)
            lab_pk = 0
            org_pk = 0
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
        if lab_pk and org_pk:
            self.object.laboratory_id = lab_pk
        self.object.save()
        upfile = self.object.related_file if self.object.related_file else None
        admin_path = reverse(
            "admin:presentation_feedbackentry_change", args=[self.object.pk]
        )
        admin_url = self.request.build_absolute_uri(admin_path)
        explanation = self._make_images_absolute(self.object.explanation or "")
        file_url = self.request.build_absolute_uri(upfile.url) if upfile else None
        try:
            send_email_from_template(
                "New feedback",
                settings.DEFAULT_FROM_EMAIL,
                context={
                    "feedback": self.object,
                    "admin_url": admin_url,
                    "explanation": explanation,
                    "file_url": file_url,
                },
                enqueued=False,
                user=None,
                upfile=upfile,
            )
        except Exception as e:
            logger.error("Error sending feedback email notification", exc_info=e)
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("Thank you for your help. We will check your problem as soon as we can"),
        )
        return redirect(self.get_success_url())

    def _make_images_absolute(self, html):
        base = self.request.build_absolute_uri("/").rstrip("/")
        html = html.replace("../media/", f"{base}/media/")
        html = re.sub(r'src=(["\'])/media/', rf"src=\g<1>{base}/media/", html)
        return html

    def get_success_url(self):
        try:
            lab_pk = int(self.request.POST.get("lab_pk", 0))
            org_pk = int(self.request.POST.get("org_pk", 0))
        except Exception:
            lab_pk = 0
            org_pk = 0
            print("exeption")
        if lab_pk and org_pk:
            print("reverse 1")
            return reverse(
                "laboratory:labindex", kwargs={"lab_pk": lab_pk, "org_pk": org_pk}
            )
        print("reverse 2")
        return reverse("index")


def index_organilab(request):
    if request.user.is_authenticated:
        return redirect(reverse("pending_tasks:view_task"))
    return render(request, "index.html")


def general_information(request):
    return render(request, "general_information.html")


def error_view(request):
    raw_status = request.GET.get("status")
    try:
        status = int(raw_status) if raw_status else None
    except (TypeError, ValueError):
        status = None

    if status not in (403, 404):
        status = None

    context = {
        "status": status or 404,
    }

    return render(request, "error_view.html", context=context, status=context["status"])
