from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.branches.models import Branch

from .filters import BranchFilter
from .serializers import BranchSerializer


class BranchViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for clinic branches."""

    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = BranchFilter
    search_fields = ("name", "address")
    ordering_fields = ("name", "city", "created_at")
    ordering = ("name",)
