from taggit.managers import TaggableManager

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from netbox.models import ChangeLoggedModel, NetBoxModel
from netbox.models.features import ImageAttachmentsMixin

from tenancy.models import Tenant
from dcim.models import Device, Interface, Cable
from ipam.models import VRF, IPAddress, Prefix, VLAN, ASN, RouteTarget
from vpn.models import L2VPN, Tunnel
from virtualization.models import VirtualMachine
from circuits.choices import CircuitStatusChoices

from utilities.choices import ChoiceSet


def service_attachment_upload(instance, filename):
    """Build the storage path for a ServiceAttachment's uploaded file, namespaced by service pk."""
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


class DecommissionReasonChoices(ChoiceSet):
    CHOICES = [
        ('churn', 'Customer churn'),
        ('nonpayment', 'Non-payment'),
        ('upgrade', 'Upgrade/migration'),
        ('site_closure', 'Site closure'),
        ('other', 'Other'),
    ]


class IncidentEventTypeChoices(ChoiceSet):
    CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('degraded', 'Degraded'),
        ('other', 'Other'),
    ]


class IncidentSeverityChoices(ChoiceSet):
    CHOICES = [
        ('critical', 'Critical'),
        ('major', 'Major'),
        ('minor', 'Minor'),
        ('warning', 'Warning'),
    ]


class Service(ImageAttachmentsMixin, NetBoxModel):
    """
    A commercial/operational service (e.g. a DIA circuit, L3VPN, or CDN node)
    delivered on top of the DCIM/IPAM/VPN objects that actually implement it.
    Tracks identity, capacity, lifecycle dates, technical inventory links,
    dependencies on other services, and incident history.
    """
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
        blank=True
    )
    bandwidth = models.PositiveIntegerField(
        verbose_name='Bandwidth',
        blank=True,
        null=True,
        help_text='Total circuit bandwidth, in Mbps'
    )
    cir = models.PositiveIntegerField(
        verbose_name='CIR',
        blank=True,
        null=True,
        help_text='Committed Information Rate, in Mbps'
    )
    sla_uptime_percent = models.DecimalField(
        verbose_name='SLA uptime %',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Contracted uptime SLA, e.g. 99.90'
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
    decommission_reason = models.CharField(
        choices=DecommissionReasonChoices,
        verbose_name='Decommission reason',
        blank=True,
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
    ip_addresses = models.ManyToManyField(
        IPAddress,
        verbose_name='Related IP Addresses',
        blank=True,
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
        verbose_name='Related L2VPNs',
    )
    tunnels = models.ManyToManyField(
        Tunnel,
        verbose_name='Related Tunnels',
    )
    virtual_machines = models.ManyToManyField(
        VirtualMachine,
        verbose_name='Related Virtual Machines',
    )
    depends_on = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='dependents',
        blank=True,
        verbose_name='Depends On',
        help_text='Other services this one relies on (e.g. an L3VPN riding over a DIA circuit)',
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

    def _down_up_pairs(self, since=None, include_degraded=False):
        """
        Walk incidents chronologically and pair each outage-opening event
        with the next 'up' that follows it. 'down' always opens an outage;
        'degraded' only does if `include_degraded` is set, so callers can
        choose whether a partial outage counts against SLA/MTTR instead of
        that choice being baked in here. 'other' never opens or closes a
        window. An unpaired trailing outage (still ongoing) is paired with
        the current time.
        """
        opening_types = ['down', 'degraded'] if include_degraded else ['down']
        incidents = self.incidents.filter(
            event_type__in=opening_types + ['up']
        ).order_by('occurred_at')
        if since:
            incidents = incidents.filter(occurred_at__gte=since)
        pairs = []
        open_since = None
        for incident in incidents:
            if incident.event_type in opening_types and open_since is None:
                open_since = incident.occurred_at
            elif incident.event_type == 'up' and open_since is not None:
                pairs.append((open_since, incident.occurred_at))
                open_since = None
        if open_since is not None:
            pairs.append((open_since, timezone.now()))
        return pairs

    def mttr(self, days=None, include_degraded=False):
        """
        Mean Time To Repair: the average duration of each outage, optionally
        restricted to incidents from the last `days` days. Returns None if
        there's no resolved outage to average.
        """
        since = timezone.now() - timezone.timedelta(days=days) if days else None
        pairs = self._down_up_pairs(since=since, include_degraded=include_degraded)
        if not pairs:
            return None
        total = sum((end - start for start, end in pairs), timezone.timedelta())
        return total / len(pairs)

    def uptime_percent(self, include_degraded=False):
        """
        Availability since the service's first recorded incident: 1 minus
        accumulated downtime over the elapsed period. Returns None if the
        service has no incidents yet (nothing to measure against).
        """
        first_incident = self.incidents.order_by('occurred_at').first()
        if not first_incident:
            return None
        pairs = self._down_up_pairs(include_degraded=include_degraded)
        downtime = sum((end - start for start, end in pairs), timezone.timedelta())
        elapsed = timezone.now() - first_incident.occurred_at
        if elapsed.total_seconds() <= 0:
            return None
        return max(0.0, 100 * (1 - downtime.total_seconds() / elapsed.total_seconds()))

    def clean(self):
        """Validate date ordering across the lifecycle fields and that CIR doesn't exceed bandwidth."""
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
        if self.cir and self.bandwidth and self.cir > self.bandwidth:
            raise ValidationError({
                'cir': 'CIR cannot exceed the total bandwidth.'
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


class ServiceIncident(ChangeLoggedModel):
    """
    A down/up event reported against a Service, typically pushed by an
    external NMS via the API. occurred_at is always set to the time NetBox
    received the event, not a timestamp supplied by the caller, so the
    history reflects when we found out rather than a value we can't verify.
    """
    service = models.ForeignKey(
        to=Service,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    event_type = models.CharField(
        choices=IncidentEventTypeChoices,
        verbose_name='Event type',
    )
    severity = models.CharField(
        choices=IncidentSeverityChoices,
        verbose_name='Severity',
        blank=True,
    )
    description = models.CharField(
        verbose_name='Description',
        max_length=200,
        blank=True,
    )
    source = models.CharField(
        verbose_name='Source',
        max_length=100,
        blank=True,
        help_text='Reporting system, e.g. the NMS that sent this event'
    )
    occurred_at = models.DateTimeField(
        verbose_name='Occurred at',
        default=timezone.now,
        editable=False,
    )

    clone_fields = ('service',)

    class Meta:
        ordering = ('-occurred_at', '-pk')
        verbose_name = 'Service incident'
        verbose_name_plural = 'Service incidents'

    def __str__(self):
        return f'{self.service} {self.get_event_type_display()} ({self.occurred_at:%Y-%m-%d %H:%M})'

    def get_absolute_url(self):
        return self.service.get_absolute_url()
