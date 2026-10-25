from django.urls import path

from .views import ServiceIncidentViewSet, ServiceViewSet

app_name = 'netbox_services'

# Plugin base_url is already "services" (/api/plugins/services/). Register the
# viewset at the plugin root so the extra /services/ segment is not repeated.
service_list = ServiceViewSet.as_view({
    'get': 'list',
    'post': 'create',
    'put': 'bulk_update',
    'patch': 'bulk_partial_update',
    'delete': 'bulk_destroy',
})
service_detail = ServiceViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})
incident_list = ServiceIncidentViewSet.as_view({
    'get': 'list',
    'post': 'create',
    'put': 'bulk_update',
    'patch': 'bulk_partial_update',
    'delete': 'bulk_destroy',
})
incident_detail = ServiceIncidentViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    # api-root is required for /api/plugins/ to link this plugin; same view as the list.
    path('', service_list, name='api-root'),
    path('', service_list, name='service-list'),
    path('<int:pk>/', service_detail, name='service-detail'),
    path('incidents/', incident_list, name='serviceincident-list'),
    path('incidents/<int:pk>/', incident_detail, name='serviceincident-detail'),
]
