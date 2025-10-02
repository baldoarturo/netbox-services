from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from netbox_services.models import Service

class ServiceSerializer(NetBoxModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_services-api:service-detail'
    )
    class Meta:
        model = Service
        fields = ('type',
                  'service_id',
                  'tenant',
                  'tags',
                  'custom_fields',
                  'created',
                  'last_updated',
                  )
