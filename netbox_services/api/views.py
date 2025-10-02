from netbox.api.viewsets import NetBoxModelViewSet

from .. import models
from .serializers import ServiceSerializer

class ServiceViewSet(NetBoxModelViewSet):
    queryset = models.Service.objects.prefetch_related('tags')
    serializer_class = ServiceSerializer
