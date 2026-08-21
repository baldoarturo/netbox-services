from django import forms
from utilities.forms.fields import CommentField
from utilities.forms.widgets import DatePicker

from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from tenancy.models import Tenant
from dcim.models import Interface

from .models import Service, ServiceAttachment, ServiceTypeChoices


class NewServiceForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = Service
        fields = (
            'type',
            'service_id',
            'description',
            'status',
            'tenant',
            'order_date',
            'planned_activation',
            'installed',
            'contract_start',
            'contract_end',
            'requested_disconnect',
            'decommissioned',
        )
        widgets = {
            'order_date': DatePicker(),
            'planned_activation': DatePicker(),
            'installed': DatePicker(),
            'contract_start': DatePicker(),
            'contract_end': DatePicker(),
            'requested_disconnect': DatePicker(),
            'decommissioned': DatePicker(),
        }


class ServiceFilterSetForm(NetBoxModelFilterSetForm):
    model = Service
    type = forms.MultipleChoiceField(
        choices=ServiceTypeChoices,
        required=False
    )
    service_id = forms.CharField(
        required=False
    )
    tenant_id = forms.ModelMultipleChoiceField(
        queryset=Tenant.objects.filter(service__isnull=False).distinct(),
        required=False,
        label='Tenant'
    )


def related_objects_form(field_name):
    """
    Build a single-field ModelForm for assigning one of Service's related-object
    M2M fields (devices, cables, vlans, etc). Avoids ~10 near-identical ModelForm
    subclasses that differ only in which field they expose.
    """
    return type(
        f'ServiceRelated{field_name.title().replace("_", "")}Form',
        (forms.ModelForm,),
        {'Meta': type('Meta', (), {'model': Service, 'fields': (field_name,)})}
    )


ServiceRelatedDevicesForm = related_objects_form('devices')
ServiceRelatedCablesForm = related_objects_form('cables')
ServiceRelatedVLANsForm = related_objects_form('vlans')
ServiceRelatedPrefixesForm = related_objects_form('prefixes')
ServiceRelatedVRFsForm = related_objects_form('vrfs')
ServiceRelatedASNsForm = related_objects_form('asns')
ServiceRelatedRouteTargetsForm = related_objects_form('route_targets')
ServiceRelatedL2VPNsForm = related_objects_form('l2vpns')
ServiceRelatedTunnelsForm = related_objects_form('tunnels')
ServiceRelatedVirtualMachinesForm = related_objects_form('virtual_machines')


class ServiceRelatedInterfacesForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['interfaces']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        related_devices = self.instance.devices.all()
        if related_devices.exists():
            self.fields['interfaces'].queryset = Interface.objects.filter(
                device__in=related_devices)
        else:
            self.fields['interfaces'].queryset = Interface.objects.none()
        # Show device name in the interface choices
        self.fields['interfaces'].label_from_instance = lambda obj: f"{obj} ({obj.device})"


class ServiceAttachmentForm(forms.ModelForm):

    class Meta:
        model = ServiceAttachment
        fields = ('name', 'file', 'description')
