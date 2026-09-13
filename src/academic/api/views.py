from django.conf import settings
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.template.loader import render_to_string, get_template
from django.utils import timezone
from django.utils.decorators import method_decorator
from weasyprint import HTML
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.admin.models import ADDITION, DELETION
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from djgentelella.objectmanagement import BaseInlineObjectManagement
from djgentelella.permission_management import AllPermissionByAction
from rest_framework.authentication import TokenAuthentication

from academic.api import serializers, filterset
from academic.api.forms import CommentProcedureStepForm
from academic.models import (
    CommentProcedureStep,
    ProcedureStep,
    MyProcedure,
    Procedure,
    ProcedureRequiredObject,
    ProcedureObservations,
)
from laboratory.utils import organilab_logentry
from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from auth_and_perms.organization_utils import (
    user_is_allowed_on_organization,
    organization_can_change_laboratory,
)
from laboratory.models import OrganizationStructure, Laboratory
from .serializers import (
    ProcedureStepCommentSerializer,
    ProcedureStepCommentDatatableSerializer,
    ProcedureStepCommentFilterSet,
    ValidateUserAccessOrgSerializer,
)

FORMIO_SKIP_TYPES = {"button", "columns", "panel", "well", "htmlelement", "content"}


def _extract_form_fields(components, submission_data):
    """Recursively extract (label, value) pairs from formio components."""
    fields = []
    for comp in components:
        comp_type = comp.get("type", "")
        if comp_type in FORMIO_SKIP_TYPES:
            nested = comp.get("components", [])
            if nested:
                fields.extend(_extract_form_fields(nested, submission_data))
            for col in comp.get("columns", []):
                fields.extend(_extract_form_fields(col.get("components", []), submission_data))
            continue
        key = comp.get("key")
        label = comp.get("label", key)
        if key:
            value = submission_data.get(key, "")
            fields.append({"label": label, "value": value})
        nested = comp.get("components", [])
        if nested:
            fields.extend(_extract_form_fields(nested, submission_data))
    return fields


class ProcedureStepCommentTableView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    serializer_class = ProcedureStepCommentDatatableSerializer
    queryset = CommentProcedureStep.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "comment",
        "created_by__username",
        "created_by_at",
    ]  # for the global search
    filterset_class = ProcedureStepCommentFilterSet
    ordering_fields = [
        "created_by_at",
    ]
    ordering = ("-created_by_at",)  # default order

    def get_queryset(self):
        queryset = super().get_queryset()
        procedure_step = self.request.GET.get("procedure_step", None)
        my_procedure = self.request.GET.get("my_procedure", None)
        if procedure_step:
            queryset = queryset.filter(
                procedure_step=procedure_step, my_procedure=my_procedure
            )
        else:
            queryset = queryset.filter(my_procedure=my_procedure)
        return queryset

    def list(self, request, org_pk, lab_pk, *args, **kwargs):
        self.organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        self.laboratory = get_object_or_404(
            Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk
        )
        records_total = self.get_queryset().count()
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": records_total,
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class ProcedureStepCommentAPI(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = CommentProcedureStep.objects.all()
    serializer_class = ProcedureStepCommentSerializer
    permissions_by_endpoint = {
        "add_comment": [
            "academic.view_procedure",
            "academic.view_procedurestep",
            "academic.add_commentprocedurestep",
        ],
        "list_comments": [
            "academic.view_procedure",
            "academic.view_procedurestep",
            "academic.view_commentprocedurestep",
        ],
        "update_comment": [
            "academic.view_procedure",
            "academic.view_procedurestep",
            "academic.change_commentprocedurestep",
        ],
        "delete_comment": [
            "academic.view_procedure",
            "academic.view_procedurestep",
            "academic.delete_commentprocedurestep",
        ],
    }

    def _check_permission_on_laboratory(self, request, org_pk, lab_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[method_name]):
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk,
            )
            self.laboratory = get_object_or_404(
                Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk
            )
            user_is_allowed_on_organization(request.user, self.organization)
            organization_can_change_laboratory(
                self.laboratory, self.organization, raise_exec=True
            )
        else:
            raise PermissionDenied()

    @action(detail=False, methods=["post"])
    def add_comment(self, request, org_pk, lab_pk):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "add_comment")
        serializer = ProcedureStepCommentSerializer(data=request.data)
        if serializer.is_valid():
            procedure_step = get_object_or_404(
                ProcedureStep, pk=request.data["procedure_step"]
            )
            my_procedure = get_object_or_404(
                MyProcedure, pk=request.data["my_procedure"]
            )

            CommentProcedureStep.objects.create(
                created_by=request.user,
                comment=serializer.data["comment"],
                procedure_step=procedure_step,
                my_procedure=my_procedure,
            )

            comments = (
                self.get_queryset().filter(procedure_step=procedure_step).order_by("pk")
            )
            template = render_to_string(
                "academic/comment.html",
                {"comments": comments, "user": request.user},
                request,
            )
            return Response({"data": template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def list_comments(self, request, org_pk, lab_pk):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "list_comments")
        queryset = self.get_queryset()
        comments = queryset.none()

        if request.method == "GET":
            form = CommentProcedureStepForm(request.GET)

            if form.is_valid():
                comments = queryset.filter(
                    procedure_step__pk=form.cleaned_data["procedure_step"]
                ).order_by("pk")

        template = render_to_string(
            "academic/comment.html",
            {"comments": comments, "user": request.user},
            request,
        )
        return Response({"data": template})

    @action(detail=True, methods=["put"])
    def update_comment(self, request, org_pk, lab_pk, pk=None):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "update_comment")
        comment = None

        if pk:
            serializer = ProcedureStepCommentSerializer(data=request.data)
            if serializer.is_valid():
                comment = get_object_or_404(CommentProcedureStep, pk=pk)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if comment:
                comment.comment = request.data["comment"]
                comment.save()
                query = (
                    self.get_queryset()
                    .filter(procedure_step=comment.procedure_step)
                    .order_by("pk")
                )
                template = render_to_string(
                    "academic/comment.html",
                    {"comments": query, "user": request.user},
                    request,
                )

                return Response({"data": template}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"])
    def delete_comment(self, request, org_pk, lab_pk, pk=None):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "delete_comment")
        if pk:
            comment = get_object_or_404(
                CommentProcedureStep.objects.using(settings.READONLY_DATABASE), pk=pk
            )
            procedure_step = comment.procedure_step
            comment.delete()
            template = render_to_string(
                "academic/comment.html",
                {
                    "comments": self.get_queryset()
                    .filter(procedure_step=procedure_step)
                    .order_by("pk"),
                    "user": request.user,
                },
                request,
            )

            return Response({"data": template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("academic.view_myprocedure", raise_exception=True),
    name="dispatch",
)
class MyProceduresAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.MyProcedureDataTableSerializer
    queryset = MyProcedure.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "name",
        "custom_procedure__title",
        "status",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
    ]
    filterset_class = filterset.MyProcedureFilterSet
    ordering_fields = ["pk"]
    ordering = ("-pk",)
    organization = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.organization:
            queryset = queryset.filter(organization=self.organization).order_by("-pk")
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, org_pk, lab_pk, *args, **kwargs):
        self.organization = org_pk
        queryset = self.filter_queryset(self.get_queryset())
        validate_serializer = ValidateUserAccessOrgLabSerializer(
            data={"laboratory": lab_pk, "organization": org_pk},
            context={"user": self.request.user},
        )
        if validate_serializer.is_valid():
            data = self.paginate_queryset(queryset)
            response = {
                "data": data,
                "recordsTotal": self.get_queryset().count(),
                "recordsFiltered": queryset.count(),
                "draw": self.request.GET.get("draw", 1),
            }
            return Response(self.get_serializer(response).data)
        else:
            return Response(
                validate_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["get"])
    def download_my_procedures(self, request, org_pk, lab_pk, pk=None):
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, organization)
        laboratory = get_object_or_404(
            Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk
        )
        organization_can_change_laboratory(
            laboratory, organization, raise_exec=True
        )
        my_procedure = get_object_or_404(MyProcedure, pk=pk)
        steps = ProcedureStep.objects.filter(procedure=my_procedure.custom_procedure)
        saved_data = my_procedure.schema.get("steps_data", {})

        steps_data = []
        for step in steps:
            fields = []
            if step.form and step.form.schema:
                step_submission = saved_data.get(str(step.pk), {})
                fields = _extract_form_fields(
                    step.form.schema.get("components", []), step_submission
                )
            comments = CommentProcedureStep.objects.filter(
                my_procedure=my_procedure, procedure_step=step
            ).order_by("created_by_at")
            steps_data.append({
                "title": step.title,
                "fields": fields,
                "comments": comments,
            })

        context = {
            "my_procedure": my_procedure,
            "steps_data": steps_data,
            "title": my_procedure.name,
            "user": request.user,
            "datetime": timezone.now(),
        }
        template = get_template("academic/my_procedure_pdf.html")
        html = template.render(context=context)
        pdf = HTML(
            string=html, encoding="utf-8", base_url=request.build_absolute_uri()
        ).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="procedure_{my_procedure.pk}.pdf"'
        )
        return response


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("academic.view_procedure", raise_exception=True),
    name="dispatch",
)
class ProcedureAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ProcedureDataTableSerializer
    queryset = Procedure.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["title", "description"]
    filterset_class = filterset.ProcedureFilterSet
    ordering_fields = ["pk"]
    ordering = ("-pk",)
    organization = None

    def get_queryset(self):
        queryset = super().get_queryset()

        content = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )

        if self.organization:
            queryset = queryset.filter(
                object_id=self.organization, content_type=content
            ).order_by("-pk")
        else:
            queryset = queryset.none()

        return queryset

    def list(self, request, org_pk, *args, **kwargs):
        self.organization = org_pk
        queryset = self.filter_queryset(self.get_queryset())
        validate_serializer = ValidateUserAccessOrgSerializer(
            data={"organization": org_pk}, context={"user": self.request.user}
        )

        if validate_serializer.is_valid():
            user_is_allowed_on_organization(
                self.request.user, validate_serializer.validated_data["organization"]
            )
            data = self.paginate_queryset(queryset)
            response = {
                "data": data,
                "recordsTotal": self.get_queryset().count(),
                "recordsFiltered": queryset.count(),
                "draw": self.request.GET.get("draw", 1),
            }
            return Response(self.get_serializer(response).data)
        else:
            return Response(
                validate_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class ProcedureStepInlineManagement(BaseInlineObjectManagement):
    """CRUDAL de los hijos de un ProcedureStep (reemplazo de los FBV
    save_object/remove_object/save_observation/remove_observation).

    El padre se resuelve por URL (``parent_pk``) y se acota a la organización
    del prefijo; se admiten procedimientos legados sin organización
    (content_type nulo), que es como operaba el flujo anterior."""

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (AllPermissionByAction,)
    parent_model = ProcedureStep
    parent_field = "step"
    pagination_class = LimitOffsetPagination
    filter_backends = (OrderingFilter,)
    ordering = ("pk",)

    def get_parent_queryset(self):
        org_pk = self.kwargs.get("org_pk")
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk,
        )
        user_is_allowed_on_organization(self.request.user, organization)
        content_type = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )
        return ProcedureStep.objects.filter(
            Q(procedure__content_type__isnull=True)
            | Q(procedure__content_type=content_type, procedure__object_id=org_pk)
        )


class ProcedureRequiredObjectViewSet(ProcedureStepInlineManagement):
    serializer_class = {
        "list": serializers.ProcedureRequiredObjectDataTableSerializer,
        "create": serializers.AddProcedureRequiredObjectSerializer,
    }
    perms = {
        "list": ["academic.view_procedure"],
        "create": ["academic.add_procedurerequiredobject"],
        "destroy": ["academic.delete_procedurerequiredobject"],
    }
    queryset = ProcedureRequiredObject.objects.all()

    def perform_create(self, serializer):
        instance = serializer.save(step=self.get_parent_object())
        organilab_logentry(
            self.request.user,
            instance,
            ADDITION,
            changed_data=list(serializer.validated_data.keys()),
            change_message=_(
                "Added required object '%(obj)s' (%(qty)s %(unit)s) to procedure step"
            )
            % {
                "obj": str(instance.object),
                "qty": instance.quantity,
                "unit": str(instance.measurement_unit),
            },
            relobj=self.kwargs.get("org_pk"),
        )

    def perform_destroy(self, instance):
        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            changed_data=["object", "quantity", "measurement_unit", "step"],
            change_message=_("Removed required object '%(obj)s' from procedure step")
            % {"obj": str(instance.object)},
        )
        instance.delete()


class ProcedureObservationViewSet(ProcedureStepInlineManagement):
    serializer_class = {
        "list": serializers.ProcedureObservationDataTableSerializer,
        "create": serializers.AddProcedureObservationSerializer,
    }
    perms = {
        "list": ["academic.view_procedure"],
        "create": ["academic.add_procedureobservations"],
        "destroy": ["academic.delete_procedureobservations"],
    }
    queryset = ProcedureObservations.objects.all()

    def perform_create(self, serializer):
        instance = serializer.save(step=self.get_parent_object())
        organilab_logentry(
            self.request.user,
            instance,
            ADDITION,
            changed_data=["description", "step"],
            change_message=_("Added observation to procedure step '%(title)s'")
            % {"title": instance.step.title},
        )

    def perform_destroy(self, instance):
        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            changed_data=["description", "step"],
            change_message=_("Removed observation from procedure step"),
        )
        instance.delete()
