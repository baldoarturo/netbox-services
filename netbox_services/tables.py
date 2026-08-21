import django_tables2 as tables

from netbox.tables import NetBoxTable
from netbox.tables.columns import ToggleColumn

from .models import Service


class ServiceListTable(NetBoxTable):
    pk = ToggleColumn(accessor='pk')
    service_id = tables.Column(
        linkify=True,
        verbose_name='Service ID',

    )

    class Meta(NetBoxTable.Meta):
        model = Service
        fields = (
            'pk',
            'service_id',
            'type',
            'description',
            'status',
            'tenant',
            'order_date',
            'planned_activation',
            'installed',
            'contract_end',
            'decommissioned',
        )
        default_columns = ('pk', 'service_id', 'type', 'description', 'status', 'tenant', 'installed')


class ServiceTable(NetBoxTable):
    service_id = tables.Column(
        linkify=True,
        verbose_name='Service ID',
    )

    class Meta(NetBoxTable.Meta):
        model = Service
        fields = (
            'type',
            'service_id',
            'description',
            'status',
            'tenant',
            'order_date',
            'planned_activation',
            'installed',
            'contract_start',
            'contract_end',
            'requested_disconnect',
            'decommissioned',
            'devices',
            'interfaces',
            'cables',
            'vlans',
            'prefixes',
            'vrf',
            'asns',
            'route_targets',
            'l2vpns',
            'tunnels',
            'virtual_machines',
        )
        default_columns = ('pk', 'service_id', 'type', 'tenant')
