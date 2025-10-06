import django_tables2 as tables

from netbox.tables import NetBoxTable

from .models import Service


class ServiceListTable(NetBoxTable):
    service_id = tables.Column(
        linkify=True,
        verbose_name='Service ID',

    )

    class Meta(NetBoxTable.Meta):
        model = Service
        fields = ('pk', 'service_id', 'type', 'tenant')
        default_columns = ('pk', 'service_id', 'type', 'tenant')


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
            'tenant',
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
