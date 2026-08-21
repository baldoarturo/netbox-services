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
            self.fields['interfaces'].queryset = Interface.objects.filter(
                device__in=related_devices)
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


class ServiceAttachmentForm(forms.ModelForm):

    class Meta:
        model = ServiceAttachment
        fields = ('name', 'file', 'description')
