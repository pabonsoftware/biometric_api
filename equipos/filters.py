import django_filters

from .models import EquipoBiomedico, TipoTecnologia, EstadoEquipo


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

    tipo_tecnologia = django_filters.ChoiceFilter(choices=TipoTecnologia.choices)

    estado_equipo = django_filters.ChoiceFilter(choices=EstadoEquipo.choices)

    class Meta:

        model = EquipoBiomedico

        fields = [
            "nombre",
            "serie",
            "marca",
            "modelo",
            "ubicacion",
            "tipo_tecnologia",
            "estado_equipo"
        ]