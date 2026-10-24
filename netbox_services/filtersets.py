import django_filters
from django.db.models import Q

from netbox.filtersets import NetBoxModelFilterSet
from tenancy.models import Tenant

from .models import Service, ServiceTypeChoices


class ServiceFilterSet(NetBoxModelFilterSet):
    type = django_filters.MultipleChoiceFilter(
        choices=ServiceTypeChoices,
        null_value=None,
    )
    service_id = django_filters.CharFilter(
        lookup_expr='icontains',
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant',
        queryset=Tenant.objects.all(),
        label='Tenant (ID)',
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant__slug',
        queryset=Tenant.objects.all(),
        to_field_name='slug',
        label='Tenant (slug)',
    )
    depends_on_id = django_filters.ModelMultipleChoiceFilter(
        field_name='depends_on',
        queryset=Service.objects.all(),
        label='Depends on (ID)',
    )
    dependent_id = django_filters.ModelMultipleChoiceFilter(
        field_name='dependents',
        queryset=Service.objects.all(),
        label='Dependent (ID)',
    )

    class Meta:
        model = Service
        fields = (
            'id',
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
