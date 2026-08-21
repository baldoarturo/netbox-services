from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from .models import Service
import django_filters


class ServiceFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Service
        fields = ('tenant', 'description')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(service_id__icontains=value) |
            Q(description__icontains=value)
        )
