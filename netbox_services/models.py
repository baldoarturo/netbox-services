from taggit.managers import TaggableManager

from django.core.exceptions import ValidationError
from django.db import models

from netbox.models import ChangeLoggedModel, NetBoxModel
from netbox.models.features import ImageAttachmentsMixin

from tenancy.models import Tenant
from dcim.models import Device, Interface, Cable
from ipam.models import VRF, Prefix, VLAN, ASN, RouteTarget
from vpn.models import L2VPN, Tunnel
from virtualization.models import VirtualMachine
from circuits.choices import CircuitStatusChoices

from utilities.choices import ChoiceSet


def service_attachment_upload(instance, filename):
    return f'netbox_services/attachments/{instance.service.pk}/{filename}'


class ServiceTypeChoices(ChoiceSet):
    CHOICES = [
        ('l2vpn', 'L2VPN'),
        ('l3vpn', 'L3VPN'),
        ('dia', 'DIA'),
        ('transit', 'IP Transit'),
        ('cdn', 'CDN'),
        ('voice', 'Voice')
    ]


class Service(ImageAttachmentsMixin, NetBoxModel):
    type = models.CharField(
        choices=ServiceTypeChoices,
        verbose_name='Service Type',
        null=False,
        blank=False
    )
    service_id = models.CharField(
        verbose_name='Service ID',
        unique=True,
        null=False,
        blank=False
    )
    description = models.CharField(
        verbose_name='Description',
        max_length=200,
        blank=True
    )
    status = models.CharField(
        choices=CircuitStatusChoices,
        verbose_name='Status',
        default=CircuitStatusChoices.STATUS_PLANNED,
        null=True,
        blank=True
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        verbose_name='Service Tenant',
        null=True,
        blank=True
    )
    order_date = models.DateField(
        verbose_name='Order date',
        blank=True,
        null=True,
        help_text='Date the service was ordered'
    )
    planned_activation = models.DateField(
        verbose_name='Planned activation',
        blank=True,
        null=True,
        help_text='Committed / planned delivery date'
    )
    installed = models.DateField(
        verbose_name='Installed',
        blank=True,
        null=True,
        help_text='Date the service was delivered / activated'
    )
    contract_start = models.DateField(
        verbose_name='Contract start',
        blank=True,
        null=True
    )
    contract_end = models.DateField(
        verbose_name='Contract end',
        blank=True,
        null=True
    )
    requested_disconnect = models.DateField(
        verbose_name='Requested disconnect',
        blank=True,
        null=True,
        help_text='Date the customer requested termination'
    )
    decommissioned = models.DateField(
        verbose_name='Decommissioned',
        blank=True,
        null=True,
        help_text='Date the service was actually taken down'
    )
    devices = models.ManyToManyField(
        Device,
        verbose_name='Related Devices',
    )
    interfaces = models.ManyToManyField(
        Interface,
        verbose_name='Related interfaces',
    )
    cables = models.ManyToManyField(
        Cable,
        verbose_name='Related Cables/XConnects',
    )
    vlans = models.ManyToManyField(
        VLAN,
        verbose_name='Related VLANs',
    )
    prefixes = models.ManyToManyField(
        Prefix,
        verbose_name='Related IP Prefixes',
    )
    vrfs = models.ManyToManyField(
        VRF,
        verbose_name='Related VRF',
        blank=True
    )
    asns = models.ManyToManyField(
        ASN,
        verbose_name='Related Autonomous Systems',
    )
    route_targets = models.ManyToManyField(
        RouteTarget,
        verbose_name='Related Route Targets',
    )
    l2vpns = models.ManyToManyField(
        L2VPN,
        verbose_name='Related Route Targets',
    )
    tunnels = models.ManyToManyField(
        Tunnel,
        verbose_name='Related Tunnels',
    )
    virtual_machines = models.ManyToManyField(
        VirtualMachine,
        verbose_name='Related Virtual Machines',
    )
    tags = TaggableManager(
        related_name='netbox_services_service_set',
    )

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['service_id']

    def __str__(self):
        return f"{self.service_id}"

    def get_absolute_url(self):
        return f"/plugins/services/{self.pk}/"

    def get_status_color(self):
        return CircuitStatusChoices.colors.get(self.status)

    def clean(self):
        super().clean()
        if self.contract_start and self.contract_end and self.contract_end < self.contract_start:
            raise ValidationError({
                'contract_end': 'Contract end cannot be earlier than contract start.'
            })
        if self.installed and self.decommissioned and self.decommissioned < self.installed:
            raise ValidationError({
                'decommissioned': 'Decommissioned date cannot be earlier than installed date.'
            })
        if self.requested_disconnect and self.decommissioned and self.decommissioned < self.requested_disconnect:
            raise ValidationError({
                'decommissioned': 'Decommissioned date cannot be earlier than the requested disconnect date.'
            })


class ServiceAttachment(ChangeLoggedModel):
    """
    A file (contract PDF, photo, etc.) attached to a Service.
    Photos can also use NetBox image attachments on the Images tab.
    """
    service = models.ForeignKey(
        to=Service,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    name = models.CharField(
        verbose_name='Name',
        max_length=100,
        blank=True
    )
    file = models.FileField(
        upload_to=service_attachment_upload
    )
    description = models.CharField(
        verbose_name='Description',
        max_length=200,
        blank=True
    )

    clone_fields = ('service',)

    class Meta:
        ordering = ('name', 'pk')
        verbose_name = 'Service attachment'
        verbose_name_plural = 'Service attachments'

    def __str__(self):
        return self.name or getattr(self.file, 'name', '') or f'Attachment {self.pk}'

    def get_absolute_url(self):
        return self.service.get_absolute_url()

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super().delete(*args, **kwargs)
