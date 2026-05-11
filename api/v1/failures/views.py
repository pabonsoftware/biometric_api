from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.failures.models import FailureRecord

from .filters import FailureRecordFilter
from .serializers import FailureRecordSerializer, ResolveFailureSerializer


class FailureRecordViewSet(viewsets.ModelViewSet):
    """CRUD de reportes de falla + acción `resolve` para marcarlos como resueltos."""

    queryset = FailureRecord.objects.all()
    serializer_class = FailureRecordSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = FailureRecordFilter
    search_fields = ("description", "resolution_notes", "equipment__asset_tag")
    ordering_fields = ("reported_at", "severity", "resolved_at")
    ordering = ("-reported_at",)

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        failure = self.get_object()
        body = ResolveFailureSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        notes = body.validated_data.get("resolution_notes", "").strip()
        failure.mark_resolved(notes=notes)
        return Response(self.get_serializer(failure).data)
