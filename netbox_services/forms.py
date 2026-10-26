from django import forms
from utilities.forms.fields import CommentField, DynamicModelChoiceField
from utilities.forms.widgets import DatePicker

from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from tenancy.models import Tenant
from dcim.models import Cable, Device, Interface
from ipam.models import ASN, VRF, IPAddress, Prefix, RouteTarget, VLAN
from vpn.models import L2VPN, Tunnel
from virtualization.models import VirtualMachine

from .models import Service, ServiceAttachment, ServiceIncident, ServiceTypeChoices


class NewServiceForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = Service
        fields = (
            'type',
            'service_id',
            'description',
            'status',
            'bandwidth',
            'cir',
            'sla_uptime_percent',
            'tenant',
            'order_date',
            'planned_activation',
            'installed',
            'contract_start',
            'contract_end',
            'requested_disconnect',
            'decommissioned',
            'decommission_reason',
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
ServiceRelatedIPAddressesForm = related_objects_form('ip_addresses')
ServiceRelatedVRFsForm = related_objects_form('vrfs')
ServiceRelatedASNsForm = related_objects_form('asns')
ServiceRelatedRouteTargetsForm = related_objects_form('route_targets')
ServiceRelatedL2VPNsForm = related_objects_form('l2vpns')
ServiceRelatedTunnelsForm = related_objects_form('tunnels')
ServiceRelatedVirtualMachinesForm = related_objects_form('virtual_machines')


class ServiceRelatedDependsOnForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['depends_on']

    def __init__(self, *args, **kwargs):
        """Exclude the service itself from its own depends_on choices to prevent a trivial self-reference."""
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['depends_on'].queryset = Service.objects.exclude(pk=self.instance.pk)


class ServiceRelatedInterfacesForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['interfaces']

    def __init__(self, *args, **kwargs):
        """Scope the interfaces choices to the devices already assigned to this service."""
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


class ServiceIncidentForm(forms.ModelForm):

    class Meta:
        model = ServiceIncident
        fields = ('event_type', 'severity', 'description', 'source')


# Maps each tab on the impact-search page to the Service field it searches
# against. Order here drives the order of the tabs in the template.
IMPACT_SEARCH_FIELDS = (
    'device',
    'interface',
    'cable',
    'vlan',
    'prefix',
    'ip_address',
    'vrf',
    'asn',
    'route_target',
    'l2vpn',
    'tunnel',
    'virtual_machine',
)

# The Service M2M field each tab's result should be matched against.
IMPACT_SEARCH_SERVICE_FIELD = {
    'device': 'devices',
    'interface': 'interfaces',
    'cable': 'cables',
    'vlan': 'vlans',
    'prefix': 'prefixes',
    'ip_address': 'ip_addresses',
    'vrf': 'vrfs',
    'asn': 'asns',
    'route_target': 'route_targets',
    'l2vpn': 'l2vpns',
    'tunnel': 'tunnels',
    'virtual_machine': 'virtual_machines',
}


class ImpactSearchForm(forms.Form):
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        query_params={'device_id': '$device'},
    )
    cable = DynamicModelChoiceField(queryset=Cable.objects.all(), required=False)
    vlan = DynamicModelChoiceField(queryset=VLAN.objects.all(), required=False)
    prefix = DynamicModelChoiceField(queryset=Prefix.objects.all(), required=False)
    ip_address = DynamicModelChoiceField(queryset=IPAddress.objects.all(), required=False)
    vrf = DynamicModelChoiceField(queryset=VRF.objects.all(), required=False)
    asn = DynamicModelChoiceField(queryset=ASN.objects.all(), required=False)
    route_target = DynamicModelChoiceField(queryset=RouteTarget.objects.all(), required=False)
    l2vpn = DynamicModelChoiceField(queryset=L2VPN.objects.all(), required=False)
    tunnel = DynamicModelChoiceField(queryset=Tunnel.objects.all(), required=False)
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)
