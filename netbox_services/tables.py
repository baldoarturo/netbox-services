import django_tables2 as tables

from netbox.tables import NetBoxTable, columns

from .models import Service


class ServiceListTable(NetBoxTable):
    pk = columns.ToggleColumn(accessor='pk')
    service_id = tables.Column(
        linkify=True,
        verbose_name='Service ID',

    )
    depends_on = columns.ManyToManyColumn(
        linkify_item=True,
        verbose_name='Depends On',
    )

    class Meta(NetBoxTable.Meta):
        model = Service
        fields = (
            'pk',
            'service_id',
            'type',
            'description',
            'status',
            'bandwidth',
            'cir',
            'sla_uptime_percent',
            'tenant',
            'order_date',
            'planned_activation',
            'installed',
            'contract_end',
            'decommissioned',
            'decommission_reason',
            'depends_on',
        )
        default_columns = ('pk', 'service_id', 'type', 'description', 'status', 'tenant', 'installed', 'depends_on')
