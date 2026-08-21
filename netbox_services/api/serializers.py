from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from netbox_services.models import Service

class ServiceSerializer(NetBoxModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_services-api:service-detail'
    )
    devices = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    interfaces = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    cables = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vlans = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    prefixes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vrfs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    asns = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    route_targets = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    l2vpns = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    tunnels = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    virtual_machines = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Service
        fields = (
            'id',
            'url',
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
            'vrfs',
            'asns',
            'route_targets',
            'l2vpns',
            'tunnels',
            'virtual_machines',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
