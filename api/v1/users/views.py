from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import User

from .filters import UserFilter
from .permissions import IsAdminRole
from .serializers import (
    PasswordChangeSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class SelfDeleteConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("No puedes eliminar tu propia cuenta.")
    default_code = "self_delete"


class UserViewSet(viewsets.ModelViewSet):
    """CRUD de usuarios + perfil propio + cambio de contraseña."""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    filterset_class = UserFilter
    search_fields = ("username", "email", "first_name", "last_name")
    ordering_fields = ("username", "email", "role", "date_joined")
    ordering = ("username",)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        if self.action == "set_password":
            return PasswordChangeSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]
        if self.action in ("retrieve", "update", "partial_update", "set_password"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        is_admin = IsAdminRole().has_permission(request, self)
        is_self = obj.pk == request.user.pk

        if self.action in ("retrieve", "set_password"):
            if not (is_admin or is_self):
                self.permission_denied(request, message=_("No tienes permisos para esta acción."))

        if self.action in ("update", "partial_update"):
            if not (is_admin or is_self):
                self.permission_denied(request, message=_("No tienes permisos para esta acción."))
            if is_self and not is_admin:
                forbidden = {"role", "is_active", "is_staff", "is_superuser"}
                touched = forbidden.intersection(request.data.keys())
                if touched:
                    self.permission_denied(
                        request,
                        message=_("No puedes modificar tu propio rol o estado."),
                    )

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise SelfDeleteConflict()
        instance.delete()

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=True, methods=["post"], url_path="set_password")
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"request": request, "target_user": user},
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)
