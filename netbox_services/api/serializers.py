from dcim.models import Cable, Device, Interface
from ipam.models import ASN, VRF, IPAddress, Prefix, RouteTarget, VLAN
from rest_framework import serializers
from virtualization.models import VirtualMachine
from vpn.models import L2VPN, Tunnel

from netbox.api.serializers import NetBoxModelSerializer
from netbox.api.serializers.base import ValidatedModelSerializer
from netbox_services.models import Service, ServiceIncident

class ServiceSerializer(NetBoxModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_services-api:service-detail'
    )
    devices = serializers.PrimaryKeyRelatedField(many=True, queryset=Device.objects.all(), required=False)
    interfaces = serializers.PrimaryKeyRelatedField(many=True, queryset=Interface.objects.all(), required=False)
    cables = serializers.PrimaryKeyRelatedField(many=True, queryset=Cable.objects.all(), required=False)
    vlans = serializers.PrimaryKeyRelatedField(many=True, queryset=VLAN.objects.all(), required=False)
    prefixes = serializers.PrimaryKeyRelatedField(many=True, queryset=Prefix.objects.all(), required=False)
    ip_addresses = serializers.PrimaryKeyRelatedField(many=True, queryset=IPAddress.objects.all(), required=False)
    vrfs = serializers.PrimaryKeyRelatedField(many=True, queryset=VRF.objects.all(), required=False)
    asns = serializers.PrimaryKeyRelatedField(many=True, queryset=ASN.objects.all(), required=False)
    route_targets = serializers.PrimaryKeyRelatedField(
        many=True, queryset=RouteTarget.objects.all(), required=False
    )
    l2vpns = serializers.PrimaryKeyRelatedField(many=True, queryset=L2VPN.objects.all(), required=False)
    tunnels = serializers.PrimaryKeyRelatedField(many=True, queryset=Tunnel.objects.all(), required=False)
    virtual_machines = serializers.PrimaryKeyRelatedField(
        many=True, queryset=VirtualMachine.objects.all(), required=False
    )
    depends_on = serializers.PrimaryKeyRelatedField(many=True, queryset=Service.objects.all(), required=False)
    dependents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    mttr_seconds = serializers.SerializerMethodField()
    uptime_percent = serializers.SerializerMethodField()

    def _include_degraded(self):
        """Read the ?include_degraded=1 query param from the current request, if any."""
        request = self.context.get('request')
        return bool(request) and request.query_params.get('include_degraded') == '1'

    def get_mttr_seconds(self, obj):
        """Serialize Service.mttr() as a float number of seconds, or None if there's nothing to average."""
        mttr = obj.mttr(include_degraded=self._include_degraded())
        return mttr.total_seconds() if mttr is not None else None

    def get_uptime_percent(self, obj):
        """Serialize Service.uptime_percent(), honoring the include_degraded toggle."""
        return obj.uptime_percent(include_degraded=self._include_degraded())

    class Meta:
        model = Service
        fields = (
            'id',
            'url',
            'type',
            'service_id',
            'description',
            'status',
            'bandwidth',
            'cir',
            'sla_uptime_percent',
            'tenant',
            'order_date',
            'planned_activation',
            'installed',
            'contract_start',
            'contract_end',
            'requested_disconnect',
            'decommissioned',
            'decommission_reason',
            'devices',
            'interfaces',
            'cables',
            'vlans',
            'prefixes',
            'ip_addresses',
            'vrfs',
            'asns',
            'route_targets',
            'l2vpns',
            'tunnels',
            'virtual_machines',
            'depends_on',
            'dependents',
            'mttr_seconds',
            'uptime_percent',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )


class ServiceIncidentSerializer(ValidatedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_services-api:serviceincident-detail'
    )
    service = serializers.SlugRelatedField(
        slug_field='service_id',
        queryset=Service.objects.all(),
    )

    class Meta:
        model = ServiceIncident
        fields = (
            'id',
            'url',
            'service',
            'event_type',
            'severity',
            'description',
            'source',
            'occurred_at',
            'created',
            'last_updated',
        )
        read_only_fields = ('occurred_at',)
