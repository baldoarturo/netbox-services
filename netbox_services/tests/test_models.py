from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from circuits.choices import CircuitStatusChoices
from tenancy.models import Tenant
from utilities.exceptions import AbortRequest

from netbox_services.models import Service, ServiceAttachment, ServiceIncident, ServiceTypeChoices


class ServiceTestCase(TestCase):

    def test_str_returns_service_id(self):
        """__str__ returns the service_id."""
        service = Service(service_id='NW-1', type=ServiceTypeChoices.CHOICES[0][0])
        self.assertEqual(str(service), 'NW-1')

    def test_get_absolute_url(self):
        """get_absolute_url points to the plugin's detail page for this service."""
        service = Service.objects.create(service_id='NW-1', type='dia')
        self.assertEqual(service.get_absolute_url(), f'/plugins/services/{service.pk}/')

    def test_get_status_color(self):
        """get_status_color maps the service's status to its CircuitStatusChoices color."""
        service = Service.objects.create(
            service_id='NW-1', type='dia', status=CircuitStatusChoices.STATUS_ACTIVE
        )
        self.assertEqual(
            service.get_status_color(),
            CircuitStatusChoices.colors.get(CircuitStatusChoices.STATUS_ACTIVE),
        )

    def test_clean_allows_valid_dates(self):
        """clean() raises nothing when all lifecycle dates are consistently ordered."""
        service = Service(
            service_id='NW-1',
            type='dia',
            contract_start=date(2026, 1, 1),
            contract_end=date(2026, 12, 31),
            installed=date(2026, 1, 1),
            decommissioned=date(2026, 6, 1),
        )
        service.clean()

    def test_clean_rejects_contract_end_before_start(self):
        """clean() rejects a contract_end earlier than contract_start."""
        service = Service(
            service_id='NW-1',
            type='dia',
            contract_start=date(2026, 6, 1),
            contract_end=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_rejects_decommissioned_before_installed(self):
        """clean() rejects a decommissioned date earlier than installed."""
        service = Service(
            service_id='NW-1',
            type='dia',
            installed=date(2026, 6, 1),
            decommissioned=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_rejects_decommissioned_before_requested_disconnect(self):
        """clean() rejects a decommissioned date earlier than requested_disconnect."""
        service = Service(
            service_id='NW-1',
            type='dia',
            requested_disconnect=date(2026, 6, 1),
            decommissioned=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_allows_cir_equal_to_bandwidth(self):
        """clean() allows CIR equal to bandwidth (no oversubscription, not a violation)."""
        service = Service(service_id='NW-1', type='dia', bandwidth=1000, cir=1000)
        service.clean()

    def test_clean_rejects_cir_above_bandwidth(self):
        """clean() rejects a CIR greater than the total bandwidth."""
        service = Service(service_id='NW-1', type='dia', bandwidth=500, cir=1000)
        with self.assertRaises(ValidationError):
            service.clean()

    def test_can_set_sla_uptime_percent(self):
        """sla_uptime_percent accepts and preserves a decimal value like 99.90."""
        service = Service.objects.create(
            service_id='NW-1', type='dia', sla_uptime_percent='99.90'
        )
        self.assertEqual(str(service.sla_uptime_percent), '99.90')

    def test_can_set_decommission_reason(self):
        """decommission_reason accepts a value from DecommissionReasonChoices."""
        service = Service.objects.create(
            service_id='NW-1', type='dia', decommission_reason='churn'
        )
        self.assertEqual(service.decommission_reason, 'churn')

    def test_service_id_must_be_unique(self):
        """service_id enforces a uniqueness constraint at the database level."""
        Service.objects.create(service_id='NW-1', type='dia')
        with self.assertRaises(Exception):
            Service.objects.create(service_id='NW-1', type='dia')

    def test_tenant_protect_on_delete(self):
        """Deleting a tenant with an assigned service is blocked (on_delete=PROTECT)."""
        tenant = Tenant.objects.create(name='Acme', slug='acme')
        Service.objects.create(service_id='NW-1', type='dia', tenant=tenant)
        with self.assertRaises(Exception):
            tenant.delete()


class ServiceDependencyTestCase(TestCase):

    def setUp(self):
        """Create three independent services to wire up depends_on relationships between."""
        self.dia = Service.objects.create(service_id='DIA-1', type='dia')
        self.l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        self.voice = Service.objects.create(service_id='VOICE-1', type='voice')

    def test_can_add_a_dependency(self):
        """A service can be added to another's depends_on."""
        self.l3vpn.depends_on.add(self.dia)
        self.assertIn(self.dia, self.l3vpn.depends_on.all())

    def test_dependents_is_the_reverse_relation(self):
        """dependents is the automatic reverse accessor for depends_on."""
        self.l3vpn.depends_on.add(self.dia)
        self.assertIn(self.l3vpn, self.dia.dependents.all())

    def test_cannot_depend_on_itself(self):
        """A service cannot be added as its own dependency."""
        with self.assertRaises(AbortRequest):
            self.dia.depends_on.add(self.dia)

    def test_cannot_create_direct_cycle(self):
        """Adding A as a dependency of B is rejected once B is already a dependency of A."""
        self.l3vpn.depends_on.add(self.dia)
        with self.assertRaises(AbortRequest):
            self.dia.depends_on.add(self.l3vpn)

    def test_cannot_create_indirect_cycle(self):
        """A multi-hop dependency cycle (voice -> l3vpn -> dia -> voice) is rejected."""
        # voice -> l3vpn -> dia, then dia -> voice would close the loop
        self.l3vpn.depends_on.add(self.dia)
        self.voice.depends_on.add(self.l3vpn)
        with self.assertRaises(AbortRequest):
            self.dia.depends_on.add(self.voice)

    def test_diamond_dependency_is_allowed(self):
        """A service depending on two independent services (a diamond, not a cycle) is allowed."""
        # voice depends on both l3vpn and dia independently; not a cycle
        self.voice.depends_on.add(self.l3vpn)
        self.voice.depends_on.add(self.dia)
        self.assertEqual(self.voice.depends_on.count(), 2)

    def test_deleting_service_clears_dependents_relation(self):
        """Deleting a service removes it from any other service's depends_on set."""
        self.l3vpn.depends_on.add(self.dia)
        self.dia.delete()
        self.assertEqual(self.l3vpn.depends_on.count(), 0)


class ServiceAttachmentTestCase(TestCase):

    def setUp(self):
        """Create a service to attach files to."""
        self.service = Service.objects.create(service_id='NW-1', type='dia')

    def test_str_returns_name(self):
        """__str__ returns the attachment's name when set."""
        attachment = ServiceAttachment(service=self.service, name='Contract')
        self.assertEqual(str(attachment), 'Contract')

    def test_str_falls_back_to_file_name_when_no_name(self):
        """__str__ falls back to the uploaded file's name when no name was given."""
        attachment = ServiceAttachment(service=self.service, name='')
        attachment.file.name = 'contract.pdf'
        self.assertEqual(str(attachment), 'contract.pdf')

    def test_get_absolute_url_returns_service_url(self):
        """get_absolute_url redirects to the parent service's detail page."""
        attachment = ServiceAttachment.objects.create(service=self.service, name='Contract')
        self.assertEqual(attachment.get_absolute_url(), self.service.get_absolute_url())

    def test_deleting_service_cascades_to_attachment(self):
        """Deleting a service deletes its attachments too (on_delete=CASCADE)."""
        attachment = ServiceAttachment.objects.create(service=self.service, name='Contract')
        self.service.delete()
        self.assertFalse(ServiceAttachment.objects.filter(pk=attachment.pk).exists())


class ServiceIncidentTestCase(TestCase):

    def setUp(self):
        """Create a service to log incidents against."""
        self.service = Service.objects.create(service_id='NW-1', type='dia')

    def test_occurred_at_is_set_automatically(self):
        """occurred_at is populated automatically on creation."""
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.assertIsNotNone(incident.occurred_at)

    def test_str_includes_service_and_event_type(self):
        """__str__ includes the service id and the human-readable event type."""
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.assertIn('NW-1', str(incident))
        self.assertIn('Down', str(incident))

    def test_get_absolute_url_returns_service_url(self):
        """get_absolute_url redirects to the parent service's detail page."""
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.assertEqual(incident.get_absolute_url(), self.service.get_absolute_url())

    def test_deleting_service_cascades_to_incidents(self):
        """Deleting a service deletes its incidents too (on_delete=CASCADE)."""
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.service.delete()
        self.assertFalse(ServiceIncident.objects.filter(pk=incident.pk).exists())

    def test_ordering_is_most_recent_first(self):
        """The default ordering is most-recently-occurred incident first."""
        first = ServiceIncident.objects.create(service=self.service, event_type='down')
        second = ServiceIncident.objects.create(service=self.service, event_type='up')
        incidents = list(self.service.incidents.all())
        self.assertEqual(incidents[0], second)
        self.assertEqual(incidents[1], first)

    def test_accepts_degraded_event_type(self):
        """event_type accepts 'degraded' as a valid choice."""
        incident = ServiceIncident.objects.create(service=self.service, event_type='degraded')
        self.assertEqual(incident.event_type, 'degraded')

    def test_accepts_other_event_type(self):
        """event_type accepts 'other' as a valid choice."""
        incident = ServiceIncident.objects.create(service=self.service, event_type='other')
        self.assertEqual(incident.event_type, 'other')


class ServiceMTTRTestCase(TestCase):
    """
    occurred_at is editable=False / server-assigned, so these tests set it
    directly after creation to control the timeline precisely.
    """

    def setUp(self):
        """Create a service with an SLA target to compute MTTR/uptime against."""
        self.service = Service.objects.create(service_id='NW-1', type='dia', sla_uptime_percent='99.9')

    def _incident(self, event_type, occurred_at):
        """Create an incident and force its occurred_at to a specific timestamp for the test."""
        incident = ServiceIncident.objects.create(service=self.service, event_type=event_type)
        incident.occurred_at = occurred_at
        incident.save()
        return incident

    def test_mttr_none_without_incidents(self):
        """mttr() returns None when the service has no incidents at all."""
        self.assertIsNone(self.service.mttr())

    def test_mttr_averages_down_up_pairs(self):
        """mttr() averages the duration of each down->up outage pair."""
        now = timezone.now()
        self._incident('down', now - timedelta(hours=10))
        self._incident('up', now - timedelta(hours=9))   # 1h outage
        self._incident('down', now - timedelta(hours=5))
        self._incident('up', now - timedelta(hours=3))   # 2h outage
        mttr = self.service.mttr()
        self.assertAlmostEqual(mttr.total_seconds(), timedelta(hours=1.5).total_seconds(), delta=1)

    def test_mttr_ignores_degraded_by_default(self):
        """mttr() excludes degraded-only outages unless include_degraded is set."""
        now = timezone.now()
        self._incident('degraded', now - timedelta(hours=10))
        self._incident('up', now - timedelta(hours=2))  # would be an 8h outage if counted
        self.assertIsNone(self.service.mttr())

    def test_mttr_includes_degraded_when_requested(self):
        """mttr(include_degraded=True) counts degraded->up windows as outages."""
        now = timezone.now()
        self._incident('degraded', now - timedelta(hours=10))
        self._incident('up', now - timedelta(hours=2))
        mttr = self.service.mttr(include_degraded=True)
        self.assertAlmostEqual(mttr.total_seconds(), timedelta(hours=8).total_seconds(), delta=1)

    def test_mttr_respects_days_window(self):
        """mttr(days=N) only averages outages that occurred within the last N days."""
        now = timezone.now()
        self._incident('down', now - timedelta(days=60))
        self._incident('up', now - timedelta(days=59, hours=12))  # 12h outage, outside window
        self._incident('down', now - timedelta(hours=2))
        self._incident('up', now - timedelta(hours=1))  # 1h outage, inside window
        mttr = self.service.mttr(days=30)
        self.assertAlmostEqual(mttr.total_seconds(), timedelta(hours=1).total_seconds(), delta=1)

    def test_mttr_pairs_ongoing_outage_with_now(self):
        """An unresolved 'down' with no following 'up' is paired with the current time."""
        self._incident('down', timezone.now() - timedelta(hours=1))
        mttr = self.service.mttr()
        self.assertGreater(mttr.total_seconds(), timedelta(minutes=55).total_seconds())

    def test_uptime_percent_none_without_incidents(self):
        """uptime_percent() returns None when the service has no incidents at all."""
        self.assertIsNone(self.service.uptime_percent())

    def test_uptime_percent_reflects_downtime_ratio(self):
        """uptime_percent() reflects accumulated downtime over the elapsed period since the first incident."""
        now = timezone.now()
        self._incident('down', now - timedelta(days=10))
        self._incident('up', now - timedelta(days=10) + timedelta(hours=24))  # 1 full day down out of 10
        uptime = self.service.uptime_percent()
        self.assertAlmostEqual(uptime, 90.0, delta=1)

    def test_uptime_percent_ignores_degraded_by_default(self):
        """uptime_percent() doesn't count degraded-only windows as downtime by default."""
        now = timezone.now()
        self._incident('degraded', now - timedelta(days=10))
        self._incident('up', now - timedelta(days=9))
        self.assertEqual(self.service.uptime_percent(), 100.0)

    def test_uptime_percent_includes_degraded_when_requested(self):
        """uptime_percent(include_degraded=True) counts degraded windows as downtime."""
        now = timezone.now()
        self._incident('degraded', now - timedelta(days=10))
        self._incident('up', now - timedelta(days=9))
        uptime = self.service.uptime_percent(include_degraded=True)
        self.assertLess(uptime, 100.0)
