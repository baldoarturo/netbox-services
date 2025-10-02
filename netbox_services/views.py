from utilities.views import register_model_view
from netbox.views.generic import ObjectView, ObjectDeleteView, ObjectEditView, ObjectListView

from .models import Service
from .tables import ServiceListTable
from .forms import NewServiceForm
from .forms import (
    ServiceRelatedDevicesForm,
    ServiceRelatedInterfacesForm,
    ServiceRelatedCablesForm,
    ServiceRelatedVLANsForm,
    ServiceRelatedPrefixesForm,
    ServiceRelatedVRFsForm,
    ServiceRelatedASNsForm,
    ServiceRelatedRouteTargetsForm,
    ServiceRelatedL2VPNsForm,
    ServiceRelatedTunnelsForm,
    ServiceRelatedVirtualMachinesForm
)

#
#   GENERIC VIEWS
#


@register_model_view(Service, name='view', path='', detail=True)
class ServiceView(ObjectView):
    queryset = Service.objects.all()
    template_name = 'netbox_services/service.html'


@register_model_view(Service, name='list', path='', detail=False)
class ServiceListView(ObjectListView):
    queryset = Service.objects.all()
    table = ServiceListTable
    template_name = 'generic/object_list.html'


@register_model_view(Service, name='add', path='add', detail=False)
class ServiceAddView(ObjectEditView):
    queryset = Service.objects.all()
    form = NewServiceForm


@register_model_view(Service, name='edit', detail=True)
class ServiceEditView(ObjectEditView):
    queryset = Service.objects.all()
    form = NewServiceForm


@register_model_view(Service, name='delete', detail=True)
class ServiceDeleteView(ObjectDeleteView):
    queryset = Service.objects.all()

#
#   RELATION VIEWS
#


class ServiceRelatedDevicesView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedDevicesForm


class ServiceRelatedInterfacesView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedInterfacesForm


class ServiceRelatedCablesView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedCablesForm


class ServiceRelatedVLANsView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedVLANsForm


class ServiceRelatedPrefixesView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedPrefixesForm


class ServiceRelatedVRFsView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedVRFsForm


class ServiceRelatedASNsView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedASNsForm


class ServiceRelatedRouteTargetsView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedRouteTargetsForm


class ServiceRelatedL2VPNsView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedL2VPNsForm


class ServiceRelatedTunnelsView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedTunnelsForm


class ServiceRelatedVirtualMachinesView(ObjectEditView):
    queryset = Service.objects.all()
    form = ServiceRelatedVirtualMachinesForm
