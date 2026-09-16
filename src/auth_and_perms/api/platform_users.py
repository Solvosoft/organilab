from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.permissions import CanManagePlatformUsers
from auth_and_perms.user_merge import UserManagementError, check_can_manage, delete_user, merge_users


class PlatformUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    date_joined = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)
    actions = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_full_name()

    def get_actions(self, obj):
        try:
            check_can_manage(self.context["request"].user, obj)
        except UserManagementError:
            return {"destroy": False, "merge": False}
        return {"destroy": True, "merge": True}

    class Meta:
        model = User
        fields = ["id", "username", "name", "email", "last_login", "date_joined", "is_superuser", "actions"]


class MergeUserSerializer(serializers.Serializer):
    source = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class PlatformUserViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Usuarios de toda la plataforma: listar, eliminar y fusionar.

    `destroy` elimina conservando los datos en el usuario centinela; `merge`
    fusiona el usuario `source` en el de la URL, que es el que permanece.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, CanManagePlatformUsers]
    serializer_class = PlatformUserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["username", "first_name", "email", "last_login", "date_joined"]
    ordering = ("username",)

    def get_queryset(self):
        return User.objects.exclude(username=settings.DELETED_USER_SENTINEL_USERNAME).order_by("username")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total = queryset.count()
        queryset = self.filter_queryset(queryset)
        data = self.paginate_queryset(queryset)
        return Response(
            {
                "data": self.get_serializer(data, many=True).data,
                "recordsTotal": total,
                "recordsFiltered": queryset.count(),
                "draw": request.GET.get("draw", 1),
            }
        )

    def destroy(self, request, *args, **kwargs):
        try:
            delete_user(self.get_object(), request.user)
        except UserManagementError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def merge(self, request, pk=None):
        target = self.get_object()
        serializer = MergeUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = get_object_or_404(self.get_queryset(), pk=serializer.validated_data["source"].pk)
        try:
            merge_users(source, target, request.user)
        except UserManagementError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": True, "detail": str(target)})
