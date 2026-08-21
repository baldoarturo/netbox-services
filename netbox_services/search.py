from netbox.search import SearchIndex, register_search

from .models import Service


@register_search
class ServiceIndex(SearchIndex):
    model = Service
    fields = (
        ('service_id', 100),
        ('description', 500),
    )
    display_attrs = ('type', 'status', 'tenant', 'description')
