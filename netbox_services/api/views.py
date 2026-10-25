from netbox.api.viewsets import NetBoxModelViewSet

from .. import models
from ..filtersets import ServiceFilterSet, ServiceIncidentFilterSet
from .serializers import ServiceIncidentSerializer, ServiceSerializer

class ServiceViewSet(NetBoxModelViewSet):
    queryset = models.Service.objects.prefetch_related('tags')
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilterSet


class ServiceIncidentViewSet(NetBoxModelViewSet):
    queryset = models.ServiceIncident.objects.all()
    serializer_class = ServiceIncidentSerializer
    filterset_class = ServiceIncidentFilterSet
