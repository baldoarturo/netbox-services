from netbox.api.viewsets import NetBoxModelViewSet

from .. import models
from ..filtersets import ServiceFilterSet
from .serializers import ServiceSerializer

class ServiceViewSet(NetBoxModelViewSet):
    queryset = models.Service.objects.prefetch_related('tags')
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilterSet
