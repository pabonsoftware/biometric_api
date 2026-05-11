import pytest
from rest_framework.test import APIClient

from .factories import BranchFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def branch(db):
    return BranchFactory()
