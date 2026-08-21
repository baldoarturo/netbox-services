from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from netbox_services.models import Service

class ServiceSerializer(NetBoxModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_services-api:service-detail'
    )
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
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
