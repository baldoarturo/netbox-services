from taggit.managers import TaggableManager

from django.db import models

from netbox.models import NetBoxModel

from tenancy.models import Tenant
from dcim.models import Device, Interface, Cable
from ipam.models import VRF, Prefix, VLAN, ASN, RouteTarget
from vpn.models import L2VPN, Tunnel
from virtualization.models import VirtualMachine
from circuits.choices import CircuitStatusChoices

from utilities.choices import ChoiceSet


class ServiceTypeChoices(ChoiceSet):
    CHOICES = [
        ('l2vpn', 'L2VPN'),
        ('l3vpn', 'L3VPN'),
        ('dia', 'DIA'),
        ('transit', 'IP Transit'),
        ('cdn', 'CDN'),
        ('voice', 'Voice')
    ]


class Service(NetBoxModel):
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
    status = models.CharField(
        choices=CircuitStatusChoices,
        verbose_name='Status',
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
