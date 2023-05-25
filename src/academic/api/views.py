from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from academic.api import serializers
from academic.api.forms import ValidateReviewSubstanceForm, CommentProcedureStepForm
from sga.models import ReviewSubstance
from academic.models import CommentProcedureStep, ProcedureStep, MyProcedure
from .serializers import ProcedureStepCommentSerializer, ProcedureStepCommentDatatableSerializer, \
    ProcedureStepCommentFilterSet
from django.template.loader import render_to_string


class ProcedureStepCommentTableView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    serializer_class = ProcedureStepCommentDatatableSerializer
    queryset = CommentProcedureStep.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['comment', 'creator', 'creator_at', ]  # for the global search
    filterset_class = ProcedureStepCommentFilterSet
    ordering_fields = ['creator_at', ]
    ordering = ('-creator_at',)  # default order

    def get_queryset(self):
        queryset = super().get_queryset()
        procedure_step = self.request.GET.get('procedure_step', None)
        my_procedure = self.request.GET.get('my_procedure', None)
        if procedure_step:
            queryset = queryset.filter(procedure_step=procedure_step, my_procedure=my_procedure)
        else:
            queryset = queryset.filter(my_procedure=my_procedure)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': queryset.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class ProcedureStepCommentAPI(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = CommentProcedureStep.objects.all()
    serializer_class = ProcedureStepCommentSerializer

    def get_comment(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except CommentProcedureStep.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = ProcedureStepCommentSerializer(data=request.data)
        if serializer.is_valid():
            procedure_step = ProcedureStep.objects.filter(pk=request.data['procedure_step']).first()
            my_procedure = MyProcedure.objects.filter(pk=request.data['my_procedure']).first()

            CommentProcedureStep.objects.create(
                creator=request.user,
                comment=serializer.data['comment'],
                procedure_step=procedure_step,
                my_procedure=my_procedure
            )

            comments = self.get_queryset().filter(procedure_step=procedure_step).order_by('pk')
            template = render_to_string('academic/comment.html', {'comments': comments, 'user': request.user}, request)
            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        comments = queryset.none()

        if request.method == "GET":
            form = CommentProcedureStepForm(request.GET)

            if form.is_valid():
                comments = queryset.filter(procedure_step__pk=form.cleaned_data['procedure_step']).order_by('pk')

        template = render_to_string('academic/comment.html', {'comments': comments, 'user': request.user}, request)
        return Response({'data': template})

    def update(self, request, pk=None):
        comment = None

        if pk:
            serializer = ProcedureStepCommentSerializer(data=request.data)
            if serializer.is_valid():
                comment = CommentProcedureStep.objects.filter(pk=pk).first()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if comment:
                comment.comment = request.data['comment']
                comment.save()
                template = render_to_string('academic/comment.html',
                                            {'comments': self.get_queryset().filter(
                                                procedure_step=comment.procedure_step).order_by('pk'),
                                             'user': request.user}, request)

                return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        if pk:
            comment = self.get_comment(pk)
            procedure_step = comment.procedure_step
            comment.delete()
            template = render_to_string('academic/comment.html', {'comments': self.get_queryset().filter(
                procedure_step=procedure_step).order_by('pk'), 'user': request.user}, request)

            return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ReviewSubstanceViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ReviewSubstanceDataTableSerializer
    queryset = ReviewSubstance.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['substance__creator__username', 'substance__creator__first_name', 'substance__creator__last_name', 'substance__comercial_name']
    filterset_class = serializers.ReviewSubstanceFilterSet
    ordering_fields = ['pk']
    ordering = ('pk', )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        org_pk, showapprove = None, None

        if self.request.method == "GET":
            form = ValidateReviewSubstanceForm(self.request.GET)

            if form.is_valid():
                org_pk = form.cleaned_data['org_pk']
                showapprove = form.cleaned_data['showapprove']

        if org_pk:
            queryset = queryset.filter(substance__organization__pk=org_pk)

            if showapprove is not None:
                if showapprove:
                    queryset = queryset.filter(is_approved=True)
                else:
                    queryset = queryset.filter(is_approved=False)
                return queryset
        queryset = queryset.none()
        return queryset


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': ReviewSubstance.objects.count(), 'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)