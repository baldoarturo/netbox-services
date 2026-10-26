import django_filters
from django.db.models import Q
from django.utils import timezone

from netbox.filtersets import ChangeLoggedModelFilterSet, NetBoxModelFilterSet
from tenancy.models import Tenant

from .models import (
    DecommissionReasonChoices,
    IncidentEventTypeChoices,
    IncidentSeverityChoices,
    Service,
    ServiceIncident,
    ServiceTypeChoices,
)


class ServiceFilterSet(NetBoxModelFilterSet):
    type = django_filters.MultipleChoiceFilter(
        choices=ServiceTypeChoices,
        null_value=None,
    )
    service_id = django_filters.CharFilter(
        lookup_expr='icontains',
    )
    decommission_reason = django_filters.MultipleChoiceFilter(
        choices=DecommissionReasonChoices,
        null_value=None,
    )
    bandwidth_min = django_filters.NumberFilter(
        field_name='bandwidth',
        lookup_expr='gte',
        label='Bandwidth (Mbps, minimum)',
    )
    bandwidth_max = django_filters.NumberFilter(
        field_name='bandwidth',
        lookup_expr='lte',
        label='Bandwidth (Mbps, maximum)',
    )
    cir_min = django_filters.NumberFilter(
        field_name='cir',
        lookup_expr='gte',
        label='CIR (Mbps, minimum)',
    )
    cir_max = django_filters.NumberFilter(
        field_name='cir',
        lookup_expr='lte',
        label='CIR (Mbps, maximum)',
    )
    sla_uptime_percent_min = django_filters.NumberFilter(
        field_name='sla_uptime_percent',
        lookup_expr='gte',
        label='SLA uptime % (minimum)',
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
    contract_expired = django_filters.BooleanFilter(
        method='filter_contract_expired',
        label='Contract expired',
    )

    def filter_contract_expired(self, queryset, name, value):
        expired = Q(contract_end__lt=timezone.localdate()) & ~Q(status='decommissioned')
        return queryset.filter(expired) if value else queryset.exclude(expired)

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


class ServiceIncidentFilterSet(ChangeLoggedModelFilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    service_id = django_filters.ModelMultipleChoiceFilter(
        field_name='service',
        queryset=Service.objects.all(),
        label='Service (ID)',
    )
    service = django_filters.ModelMultipleChoiceFilter(
        field_name='service__service_id',
        queryset=Service.objects.all(),
        to_field_name='service_id',
        label='Service (service ID)',
    )
    event_type = django_filters.MultipleChoiceFilter(
        choices=IncidentEventTypeChoices,
        null_value=None,
    )
    severity = django_filters.MultipleChoiceFilter(
        choices=IncidentSeverityChoices,
        null_value=None,
    )

    class Meta:
        model = ServiceIncident
        fields = ('id', 'description', 'source', 'occurred_at')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(description__icontains=value) |
            Q(source__icontains=value)
        )
