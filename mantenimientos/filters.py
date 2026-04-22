import django_filters

from .models import Mantenimiento, Reporte

class MantenimientoFilter(django_filters.FilterSet):

    estado = django_filters.CharFilter()
    tipo = django_filters.CharFilter()
    equipo = django_filters.NumberFilter(field_name="equipo__id")

    class Meta:
        model = Mantenimiento
        fields = [
            "estado",
            "tipo",
            "equipo"
        ]

class ReporteFilter(django_filters.FilterSet):

    nombre = django_filters.CharFilter(lookup_expr='icontains')

    tipo = django_filters.CharFilter(lookup_expr='icontains')

    fechaGeneracion = django_filters.DateFilter()

    equipo = django_filters.NumberFilter(field_name='equipo__id')

    class Meta:
        model = Reporte 
        fields = [
            "nombre",
            "tipo",
            "fechaGeneracion",
            "equipo"
        ]