import django_filters

from .models import EquipoBiomedico

class EquipoFilter(django_filters.FilterSet):

    nombre = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains'
    )

    serie = django_filters.CharFilter(
        field_name='serie',
        lookup_expr='icontains'
    )

    marca = django_filters.CharFilter(
        field_name='marca__nombre',
        lookup_expr='icontains'
    )

    modelo = django_filters.CharFilter(
        field_name='modelo__nombre',
        lookup_expr='icontains'
    )

    class Meta:

        model = EquipoBiomedico

        fields = [
            "nombre",
            "serie",
            "marca",
            "modelo",
            "ubicacion"
        ]