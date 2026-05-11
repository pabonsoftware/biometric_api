import pytest
from django.core.exceptions import ValidationError

from apps.branches.models import Branch

from .factories import BranchFactory

pytestmark = pytest.mark.django_db


class TestBranchModel:
    def test_branch_str(self):
        branch = BranchFactory(name="Sede Norte")
        assert str(branch) == "Sede Norte"

    def test_branch_defaults(self):
        branch = BranchFactory()
        assert branch.is_active is True
        assert branch.created_at is not None
        assert branch.updated_at is not None

    def test_phone_validator_rejects_invalid_format(self):
        branch = BranchFactory.build(phone="abc")
        with pytest.raises(ValidationError):
            branch.full_clean()

    def test_phone_validator_accepts_valid_format(self):
        branch = BranchFactory.build(phone="+57 300 555 1234")
        branch.full_clean()


class TestBranchManager:
    def test_active_manager_returns_only_active(self):
        active1 = BranchFactory(name="A1", is_active=True)
        active2 = BranchFactory(name="A2", is_active=True)
        BranchFactory(name="I1", is_active=False)

        active_qs = Branch.objects.active()

        assert active_qs.count() == 2
        assert set(active_qs.values_list("id", flat=True)) == {active1.id, active2.id}

    def test_inactive_manager_returns_only_inactive(self):
        BranchFactory(name="A1", is_active=True)
        inactive = BranchFactory(name="I1", is_active=False)

        inactive_qs = Branch.objects.inactive()

        assert inactive_qs.count() == 1
        assert inactive_qs.first().id == inactive.id

    def test_by_city_filter(self):
        BranchFactory(name="B1", city="Bogota")
        BranchFactory(name="B2", city="bogota")
        BranchFactory(name="B3", city="Medellin")

        bogota_branches = Branch.objects.by_city("Bogota")

        assert bogota_branches.count() == 2

    def test_default_ordering_by_name(self):
        BranchFactory(name="Zeta")
        BranchFactory(name="Alpha")
        BranchFactory(name="Mu")

        names = list(Branch.objects.values_list("name", flat=True))

        assert names == sorted(names)
