from netbox.filtersets import NetBoxModelFilterSet
from .models import Service
import django_filters


class ServiceFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Service
        fields = ('tenant',)

    def search(self, queryset, name, value):
        return queryset.filter(service_id__icontains=value)
