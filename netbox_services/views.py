from django.shortcuts import get_object_or_404

from utilities.views import register_model_view
from netbox.views.generic import (
    ObjectView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    BulkDeleteView,
)

from .models import Service, ServiceAttachment
from .tables import ServiceListTable
from .forms import NewServiceForm, ServiceAttachmentForm
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
from .forms import ServiceFilterSetForm

from .filtersets import ServiceFilterSet

#
#   GENERIC VIEWS
#


@register_model_view(Service, name='view', path='', detail=True)
class ServiceView(ObjectView):
    queryset = Service.objects.prefetch_related('attachments', 'images', 'tags')
    template_name = 'netbox_services/service.html'

@register_model_view(Service, name='list', path='', detail=False)
class ServiceListView(ObjectListView):
    queryset = Service.objects.all()
    table = ServiceListTable
    template_name = 'generic/object_list.html'
    filterset = ServiceFilterSet
    filterset_form = ServiceFilterSetForm

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


@register_model_view(Service, name='bulk_delete', path='delete', detail=False)
class ServiceBulkDeleteView(BulkDeleteView):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet
    table = ServiceListTable


class ServiceAttachmentEditView(ObjectEditView):
    queryset = ServiceAttachment.objects.all()
    form = ServiceAttachmentForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        if not obj.pk:
            obj.service = get_object_or_404(Service, pk=url_kwargs.get('pk'))
        return obj

    def get_object(self, **kwargs):
        if attachment_pk := kwargs.get('attachment_pk'):
            return get_object_or_404(self.queryset, pk=attachment_pk)
        return self.queryset.model()


class ServiceAttachmentDeleteView(ObjectDeleteView):
    queryset = ServiceAttachment.objects.all()

    def get_object(self, **kwargs):
        return get_object_or_404(self.queryset, pk=kwargs.get('attachment_pk'))

#
#   TREE VIEWS
#
@register_model_view(Service, name='tree', detail=True)
class ServiceTreeView(ObjectView):
    queryset = Service.objects.all()
    template_name = 'netbox_services/tree.html'

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
