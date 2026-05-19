"""
URLs de la API v1.

A medida que se creen las apps de dominio, se irán incluyendo aquí, por ejemplo:
    path("equipment/", include("apps.equipment.api.v1.urls")),
"""
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = "v1"

urlpatterns = [
    # JWT auth endpoints
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    # Domain routes
    path("users/", include(("api.v1.users.urls", "users"), namespace="users")),
    path("branches/", include(("api.v1.branches.urls", "branches"), namespace="branches")),
    path("catalog/", include(("api.v1.catalog.urls", "catalog"), namespace="catalog")),
    path("equipment/", include(("api.v1.equipment.urls", "equipment"), namespace="equipment")),
    path(
        "maintenance/",
        include(("api.v1.maintenance.urls", "maintenance"), namespace="maintenance"),
    ),
    path(
        "scheduling/",
        include(("api.v1.scheduling.urls", "scheduling"), namespace="scheduling"),
    ),
    path(
        "failures/",
        include(("api.v1.failures.urls", "failures"), namespace="failures"),
    ),
    path(
        "dashboard/",
        include(("api.v1.dashboard.urls", "dashboard"), namespace="dashboard"),
    ),
]
