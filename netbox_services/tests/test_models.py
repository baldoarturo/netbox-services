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
        service = Service(service_id='NW-1', type=ServiceTypeChoices.CHOICES[0][0])
        self.assertEqual(str(service), 'NW-1')

    def test_get_absolute_url(self):
        service = Service.objects.create(service_id='NW-1', type='dia')
        self.assertEqual(service.get_absolute_url(), f'/plugins/services/{service.pk}/')

    def test_get_status_color(self):
        service = Service.objects.create(
            service_id='NW-1', type='dia', status=CircuitStatusChoices.STATUS_ACTIVE
        )
        self.assertEqual(
            service.get_status_color(),
            CircuitStatusChoices.colors.get(CircuitStatusChoices.STATUS_ACTIVE),
        )

    def test_clean_allows_valid_dates(self):
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
        service = Service(
            service_id='NW-1',
            type='dia',
            contract_start=date(2026, 6, 1),
            contract_end=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_rejects_decommissioned_before_installed(self):
        service = Service(
            service_id='NW-1',
            type='dia',
            installed=date(2026, 6, 1),
            decommissioned=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_rejects_decommissioned_before_requested_disconnect(self):
        service = Service(
            service_id='NW-1',
            type='dia',
            requested_disconnect=date(2026, 6, 1),
            decommissioned=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_allows_cir_equal_to_bandwidth(self):
        service = Service(service_id='NW-1', type='dia', bandwidth=1000, cir=1000)
        service.clean()

    def test_clean_rejects_cir_above_bandwidth(self):
        service = Service(service_id='NW-1', type='dia', bandwidth=500, cir=1000)
        with self.assertRaises(ValidationError):
            service.clean()

    def test_can_set_sla_uptime_percent(self):
        service = Service.objects.create(
            service_id='NW-1', type='dia', sla_uptime_percent='99.90'
        )
        self.assertEqual(str(service.sla_uptime_percent), '99.90')

    def test_can_set_decommission_reason(self):
        service = Service.objects.create(
            service_id='NW-1', type='dia', decommission_reason='churn'
        )
        self.assertEqual(service.decommission_reason, 'churn')

    def test_service_id_must_be_unique(self):
        Service.objects.create(service_id='NW-1', type='dia')
        with self.assertRaises(Exception):
            Service.objects.create(service_id='NW-1', type='dia')

    def test_tenant_protect_on_delete(self):
        tenant = Tenant.objects.create(name='Acme', slug='acme')
        Service.objects.create(service_id='NW-1', type='dia', tenant=tenant)
        with self.assertRaises(Exception):
            tenant.delete()


class ServiceDependencyTestCase(TestCase):

    def setUp(self):
        self.dia = Service.objects.create(service_id='DIA-1', type='dia')
        self.l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        self.voice = Service.objects.create(service_id='VOICE-1', type='voice')

    def test_can_add_a_dependency(self):
        self.l3vpn.depends_on.add(self.dia)
        self.assertIn(self.dia, self.l3vpn.depends_on.all())

    def test_dependents_is_the_reverse_relation(self):
        self.l3vpn.depends_on.add(self.dia)
        self.assertIn(self.l3vpn, self.dia.dependents.all())

    def test_cannot_depend_on_itself(self):
        with self.assertRaises(AbortRequest):
            self.dia.depends_on.add(self.dia)

    def test_cannot_create_direct_cycle(self):
        self.l3vpn.depends_on.add(self.dia)
        with self.assertRaises(AbortRequest):
            self.dia.depends_on.add(self.l3vpn)

    def test_cannot_create_indirect_cycle(self):
        # voice -> l3vpn -> dia, then dia -> voice would close the loop
        self.l3vpn.depends_on.add(self.dia)
        self.voice.depends_on.add(self.l3vpn)
        with self.assertRaises(AbortRequest):
            self.dia.depends_on.add(self.voice)

    def test_diamond_dependency_is_allowed(self):
        # voice depends on both l3vpn and dia independently; not a cycle
        self.voice.depends_on.add(self.l3vpn)
        self.voice.depends_on.add(self.dia)
        self.assertEqual(self.voice.depends_on.count(), 2)

    def test_deleting_service_clears_dependents_relation(self):
        self.l3vpn.depends_on.add(self.dia)
        self.dia.delete()
        self.assertEqual(self.l3vpn.depends_on.count(), 0)


class ServiceAttachmentTestCase(TestCase):

    def setUp(self):
        self.service = Service.objects.create(service_id='NW-1', type='dia')

    def test_str_returns_name(self):
        attachment = ServiceAttachment(service=self.service, name='Contract')
        self.assertEqual(str(attachment), 'Contract')

    def test_str_falls_back_to_file_name_when_no_name(self):
        attachment = ServiceAttachment(service=self.service, name='')
        attachment.file.name = 'contract.pdf'
        self.assertEqual(str(attachment), 'contract.pdf')

    def test_get_absolute_url_returns_service_url(self):
        attachment = ServiceAttachment.objects.create(service=self.service, name='Contract')
        self.assertEqual(attachment.get_absolute_url(), self.service.get_absolute_url())

    def test_deleting_service_cascades_to_attachment(self):
        attachment = ServiceAttachment.objects.create(service=self.service, name='Contract')
        self.service.delete()
        self.assertFalse(ServiceAttachment.objects.filter(pk=attachment.pk).exists())


class ServiceIncidentTestCase(TestCase):

    def setUp(self):
        self.service = Service.objects.create(service_id='NW-1', type='dia')

    def test_occurred_at_is_set_automatically(self):
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.assertIsNotNone(incident.occurred_at)

    def test_str_includes_service_and_event_type(self):
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.assertIn('NW-1', str(incident))
        self.assertIn('Down', str(incident))

    def test_get_absolute_url_returns_service_url(self):
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.assertEqual(incident.get_absolute_url(), self.service.get_absolute_url())

    def test_deleting_service_cascades_to_incidents(self):
        incident = ServiceIncident.objects.create(service=self.service, event_type='down')
        self.service.delete()
        self.assertFalse(ServiceIncident.objects.filter(pk=incident.pk).exists())

    def test_ordering_is_most_recent_first(self):
        first = ServiceIncident.objects.create(service=self.service, event_type='down')
        second = ServiceIncident.objects.create(service=self.service, event_type='up')
        incidents = list(self.service.incidents.all())
        self.assertEqual(incidents[0], second)
        self.assertEqual(incidents[1], first)

    def test_accepts_degraded_event_type(self):
        incident = ServiceIncident.objects.create(service=self.service, event_type='degraded')
        self.assertEqual(incident.event_type, 'degraded')

    def test_accepts_other_event_type(self):
        incident = ServiceIncident.objects.create(service=self.service, event_type='other')
        self.assertEqual(incident.event_type, 'other')


class ServiceMTTRTestCase(TestCase):
    """
    occurred_at is editable=False / server-assigned, so these tests set it
    directly after creation to control the timeline precisely.
    """

    def setUp(self):
        self.service = Service.objects.create(service_id='NW-1', type='dia', sla_uptime_percent='99.9')

    def _incident(self, event_type, occurred_at):
        incident = ServiceIncident.objects.create(service=self.service, event_type=event_type)
        incident.occurred_at = occurred_at
        incident.save()
        return incident

    def test_mttr_none_without_incidents(self):
        self.assertIsNone(self.service.mttr())

    def test_mttr_averages_down_up_pairs(self):
        now = timezone.now()
        self._incident('down', now - timedelta(hours=10))
        self._incident('up', now - timedelta(hours=9))   # 1h outage
        self._incident('down', now - timedelta(hours=5))
        self._incident('up', now - timedelta(hours=3))   # 2h outage
        mttr = self.service.mttr()
        self.assertAlmostEqual(mttr.total_seconds(), timedelta(hours=1.5).total_seconds(), delta=1)

    def test_mttr_ignores_degraded_by_default(self):
        now = timezone.now()
        self._incident('degraded', now - timedelta(hours=10))
        self._incident('up', now - timedelta(hours=2))  # would be an 8h outage if counted
        self.assertIsNone(self.service.mttr())

    def test_mttr_includes_degraded_when_requested(self):
        now = timezone.now()
        self._incident('degraded', now - timedelta(hours=10))
        self._incident('up', now - timedelta(hours=2))
        mttr = self.service.mttr(include_degraded=True)
        self.assertAlmostEqual(mttr.total_seconds(), timedelta(hours=8).total_seconds(), delta=1)

    def test_mttr_respects_days_window(self):
        now = timezone.now()
        self._incident('down', now - timedelta(days=60))
        self._incident('up', now - timedelta(days=59, hours=12))  # 12h outage, outside window
        self._incident('down', now - timedelta(hours=2))
        self._incident('up', now - timedelta(hours=1))  # 1h outage, inside window
        mttr = self.service.mttr(days=30)
        self.assertAlmostEqual(mttr.total_seconds(), timedelta(hours=1).total_seconds(), delta=1)

    def test_mttr_pairs_ongoing_outage_with_now(self):
        self._incident('down', timezone.now() - timedelta(hours=1))
        mttr = self.service.mttr()
        self.assertGreater(mttr.total_seconds(), timedelta(minutes=55).total_seconds())

    def test_uptime_percent_none_without_incidents(self):
        self.assertIsNone(self.service.uptime_percent())

    def test_uptime_percent_reflects_downtime_ratio(self):
        now = timezone.now()
        self._incident('down', now - timedelta(days=10))
        self._incident('up', now - timedelta(days=10) + timedelta(hours=24))  # 1 full day down out of 10
        uptime = self.service.uptime_percent()
        self.assertAlmostEqual(uptime, 90.0, delta=1)

    def test_uptime_percent_ignores_degraded_by_default(self):
        now = timezone.now()
        self._incident('degraded', now - timedelta(days=10))
        self._incident('up', now - timedelta(days=9))
        self.assertEqual(self.service.uptime_percent(), 100.0)

    def test_uptime_percent_includes_degraded_when_requested(self):
        now = timezone.now()
        self._incident('degraded', now - timedelta(days=10))
        self._incident('up', now - timedelta(days=9))
        uptime = self.service.uptime_percent(include_degraded=True)
        self.assertLess(uptime, 100.0)
