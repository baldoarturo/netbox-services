from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from .models import Service
import django_filters


class ServiceFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Service
        fields = (
            'tenant',
            'description',
            'status',
            'order_date',
            'planned_activation',
            'installed',
            'contract_start',
            'contract_end',
            'requested_disconnect',
            'decommissioned',
        )

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(service_id__icontains=value) |
            Q(description__icontains=value)
        )
