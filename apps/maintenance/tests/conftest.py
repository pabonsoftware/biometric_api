import pytest
from rest_framework.test import APIClient

from apps.branches.tests.factories import BranchFactory
from apps.equipment.tests.factories import EquipmentFactory
from apps.users.tests.factories import AdminFactory, IngenieroFactory, TecnicoFactory

from .factories import MaintenanceRecordFactory


@pytest.fixture(autouse=True)
def media_storage(tmp_path, settings):
    """Aísla el storage de archivos por test usando tmp_path como MEDIA_ROOT."""
    settings.MEDIA_ROOT = tmp_path
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    yield tmp_path


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return AdminFactory()


@pytest.fixture
def auth_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def branch(db):
    return BranchFactory()


@pytest.fixture
def equipment(db, branch):
    return EquipmentFactory(branch=branch)


@pytest.fixture
def maintenance_record(db, equipment):
    return MaintenanceRecordFactory(equipment=equipment)


@pytest.fixture
def ingeniero(db):
    return IngenieroFactory()


@pytest.fixture
def tecnico(db):
    return TecnicoFactory()
