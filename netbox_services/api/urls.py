from netbox.api.routers import NetBoxRouter
from .views import ServiceViewSet
app_name = 'netbox_services'
router = NetBoxRouter()
router.register('services', ServiceViewSet)

urlpatterns = router.urls
