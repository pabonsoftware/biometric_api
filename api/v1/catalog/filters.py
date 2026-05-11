from django_filters import rest_framework as filters

from apps.catalog.models import Brand, EquipmentModel


class BrandFilter(filters.FilterSet):
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Brand
        fields = ("is_active",)


class EquipmentModelFilter(filters.FilterSet):
    brand = filters.NumberFilter(field_name="brand_id")
    is_active = filters.BooleanFilter(field_name="is_active")
    brand_is_active = filters.BooleanFilter(field_name="brand__is_active")

    class Meta:
        model = EquipmentModel
        fields = ("brand", "is_active", "brand_is_active")
