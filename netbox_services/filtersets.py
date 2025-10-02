from netbox.filtersets import NetBoxModelFilterSet
from .models import Service

class ServiceFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Service
        fields = '__all__'
