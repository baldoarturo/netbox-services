from django import forms
from utilities.forms.fields import CommentField

from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from .models import Service, ServiceTypeChoices

from tenancy.models import Tenant
from dcim.models import Device, Interface, Cable
from ipam.models import VRF, Prefix, VLAN, ASN, RouteTarget
from vpn.models import L2VPN, Tunnel
from virtualization.models import VirtualMachine


class NewServiceForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = Service
        fields = ('type', 'service_id', 'tenant')


class ServiceRelatedDevicesForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('devices',)

class ServiceRelatedInterfacesForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['interfaces']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        related_devices = self.instance.devices.all()
        if related_devices.exists():
            self.fields['interfaces'].queryset = Interface.objects.filter(device__in=related_devices)
        else:
            self.fields['interfaces'].queryset = Interface.objects.none()
        # Show device name in the interface choices
        self.fields['interfaces'].label_from_instance = lambda obj: f"{obj} ({obj.device})"

class ServiceRelatedCablesForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('cables',)


class ServiceRelatedVLANsForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('vlans',)

class ServiceRelatedPrefixesForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('prefixes',)

class ServiceRelatedVRFsForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('vrfs',)

class ServiceRelatedASNsForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('asns',)


class ServiceRelatedRouteTargetsForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('route_targets',)

class ServiceRelatedL2VPNsForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('l2vpns',)

class ServiceRelatedTunnelsForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('tunnels',)

class ServiceRelatedVirtualMachinesForm(forms.ModelForm):

    class Meta:
        model = Service
        fields = ('virtual_machines',)


class ServiceFilterForm(NetBoxModelFilterSetForm):
    comments = CommentField()
    model = Service
    type = forms.MultipleChoiceField(
        choices=ServiceTypeChoices,
        required=False
    )
    service_id = forms.CharField(
        required=False
    )
    tenant = forms.ModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    devices = forms.ModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False
    )
    interfaces = forms.ModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        required=False
    )
    cables = forms.ModelMultipleChoiceField(
        queryset=Cable.objects.all(),
        required=False
    )
    vlans = forms.ModelMultipleChoiceField(
        queryset=VLAN.objects.all(),
        required=False
    )
    prefixes = forms.ModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False
    )
    vrf = forms.ModelMultipleChoiceField(
        queryset=VRF.objects.all(),
        required=False
    )
    asns = forms.ModelMultipleChoiceField(
        queryset=ASN.objects.all(),
        required=False
    )
    route_targets = forms.ModelMultipleChoiceField(
        queryset=RouteTarget.objects.all(),
        required=False
    )
    l2vpns = forms.ModelMultipleChoiceField(
        queryset=L2VPN.objects.all(),
        required=False
    )
    tunnels = forms.ModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    virtual_machines = forms.ModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False
    )
