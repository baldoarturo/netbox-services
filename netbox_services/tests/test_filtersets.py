from datetime import date, timedelta

from django.test import TestCase

from tenancy.models import Tenant

from netbox_services.filtersets import ServiceFilterSet, ServiceIncidentFilterSet
from netbox_services.models import Service, ServiceIncident


class ServiceFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create two tenants and three services (two DIA, one L3VPN) to filter/search across."""
        cls.tenant1 = Tenant.objects.create(name='Acme', slug='acme')
        cls.tenant2 = Tenant.objects.create(name='Globex', slug='globex')

        Service.objects.create(
            service_id='NW-1', type='dia', description='Primary DIA', tenant=cls.tenant1
        )
        Service.objects.create(
            service_id='NW-2', type='l3vpn', description='Core VPN', tenant=cls.tenant2
        )
        Service.objects.create(
            service_id='NW-3', type='dia', description='Backup DIA', tenant=None
        )

    def test_filter_by_type(self):
        """type filters to services of the given service type."""
        results = self.filterset({'type': ['dia']}, self.queryset).qs
        self.assertEqual(results.count(), 2)

    def test_filter_by_service_id_icontains(self):
        """service_id filters with a case-insensitive partial match."""
        results = self.filterset({'service_id': 'NW-1'}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_filter_by_tenant_id(self):
        """tenant_id filters by the tenant's numeric ID."""
        results = self.filterset({'tenant_id': [self.tenant1.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-1')

    def test_filter_by_tenant_slug(self):
        """tenant filters by the tenant's slug."""
        results = self.filterset({'tenant': ['globex']}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_search_matches_service_id(self):
        """The q search matches against service_id."""
        results = self.filterset({'q': 'NW-2'}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_search_matches_description(self):
        """The q search matches against description."""
        results = self.filterset({'q': 'Backup'}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-3')

    def test_no_filters_returns_all(self):
        """With no filters applied, every service is returned."""
        results = self.filterset({}, self.queryset).qs
        self.assertEqual(results.count(), 3)


class ServiceDependencyFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create a DIA and an L3VPN, with the L3VPN depending on the DIA."""
        cls.dia = Service.objects.create(service_id='DIA-1', type='dia')
        cls.l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        cls.l3vpn.depends_on.add(cls.dia)

    def test_filter_by_depends_on_id(self):
        """depends_on_id filters to services that depend on the given service."""
        results = self.filterset({'depends_on_id': [self.dia.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'L3VPN-1')

    def test_filter_by_dependent_id(self):
        """dependent_id filters to services that the given service depends on."""
        results = self.filterset({'dependent_id': [self.l3vpn.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'DIA-1')


class ServiceCapacityFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create services spanning a range of bandwidth/CIR/SLA/decommission values."""
        Service.objects.create(
            service_id='NW-1', type='dia', bandwidth=100, cir=50, sla_uptime_percent='99.00'
        )
        Service.objects.create(
            service_id='NW-2', type='dia', bandwidth=1000, cir=500, sla_uptime_percent='99.99'
        )
        Service.objects.create(
            service_id='NW-3', type='dia', decommission_reason='churn'
        )

    def test_filter_by_bandwidth_min(self):
        """bandwidth_min filters to services with bandwidth at or above the given value."""
        results = self.filterset({'bandwidth_min': 500}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_filter_by_bandwidth_max(self):
        """bandwidth_max filters to services with bandwidth at or below the given value."""
        results = self.filterset({'bandwidth_max': 500}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-1')

    def test_filter_by_cir_min(self):
        """cir_min filters to services with CIR at or above the given value."""
        results = self.filterset({'cir_min': 500}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_filter_by_sla_uptime_percent_min(self):
        """sla_uptime_percent_min filters to services with an SLA target at or above the given value."""
        results = self.filterset({'sla_uptime_percent_min': 99.5}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_filter_by_decommission_reason(self):
        """decommission_reason filters to services decommissioned for the given reason."""
        results = self.filterset({'decommission_reason': ['churn']}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-3')


class ServiceIncidentFilterSetTestCase(TestCase):
    queryset = ServiceIncident.objects.all()
    filterset = ServiceIncidentFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create two services, each with one incident of a different type/severity/source."""
        cls.svc1 = Service.objects.create(service_id='NW-1', type='dia')
        cls.svc2 = Service.objects.create(service_id='NW-2', type='l3vpn')
        ServiceIncident.objects.create(
            service=cls.svc1, event_type='down', severity='critical', source='LibreNMS'
        )
        ServiceIncident.objects.create(
            service=cls.svc2, event_type='up', severity='minor', source='Zabbix'
        )

    def test_filter_by_service_id(self):
        """service_id filters incidents to the given service's numeric ID."""
        results = self.filterset({'service_id': [self.svc1.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_filter_by_service_service_id(self):
        """service filters incidents by the related service's service_id."""
        results = self.filterset({'service': ['NW-2']}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service, self.svc2)

    def test_filter_by_event_type(self):
        """event_type filters to incidents of the given type."""
        results = self.filterset({'event_type': ['down']}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_filter_by_severity(self):
        """severity filters to incidents of the given severity."""
        results = self.filterset({'severity': ['critical']}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_search_matches_source(self):
        """The q search matches against the incident's source field."""
        results = self.filterset({'q': 'Zabbix'}, self.queryset).qs
        self.assertEqual(results.count(), 1)


class ServiceContractExpiredFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create services covering expired/decommissioned/current/no-contract combinations."""
        Service.objects.create(
            service_id='EXPIRED-1', type='dia', status='active',
            contract_start=date(2024, 1, 1), contract_end=date(2025, 1, 1),
        )
        Service.objects.create(
            service_id='DECOM-EXPIRED-1', type='dia', status='decommissioned',
            contract_start=date(2024, 1, 1), contract_end=date(2025, 1, 1),
        )
        Service.objects.create(
            service_id='CURRENT-1', type='dia', status='active',
            contract_start=date(2026, 1, 1), contract_end=date(2027, 1, 1),
        )
        Service.objects.create(service_id='NO-CONTRACT-1', type='dia', status='active')

    def test_contract_expired_true_excludes_decommissioned(self):
        """contract_expired=true matches only active services past their contract_end."""
        results = self.filterset({'contract_expired': 'true'}, self.queryset).qs
        self.assertEqual(list(results.values_list('service_id', flat=True)), ['EXPIRED-1'])

    def test_contract_expired_false_includes_everything_else(self):
        """contract_expired=false matches every service not caught by the expired filter."""
        results = self.filterset({'contract_expired': 'false'}, self.queryset).qs
        ids = set(results.values_list('service_id', flat=True))
        self.assertEqual(ids, {'DECOM-EXPIRED-1', 'CURRENT-1', 'NO-CONTRACT-1'})


class ServiceContractEndBeforeFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Create services with contracts ending in the past, soon, far in the future, or soon but decommissioned."""
        today = date.today()
        Service.objects.create(
            service_id='PAST-1', type='dia', status='active',
            contract_start=date(2024, 1, 1), contract_end=date(2025, 1, 1),
        )
        Service.objects.create(
            service_id='SOON-1', type='dia', status='active',
            contract_start=date(2026, 1, 1), contract_end=today + timedelta(days=5),
        )
        Service.objects.create(
            service_id='LATER-1', type='dia', status='active',
            contract_start=date(2026, 1, 1), contract_end=today + timedelta(days=400),
        )
        Service.objects.create(
            service_id='DECOM-SOON-1', type='dia', status='decommissioned',
            contract_start=date(2026, 1, 1), contract_end=today + timedelta(days=5),
        )

    def test_excludes_already_expired(self):
        """contract_end_before excludes contracts that already expired before today."""
        cutoff = date.today() + timedelta(days=30)
        results = self.filterset({'contract_end_before': cutoff.isoformat()}, self.queryset).qs
        ids = set(results.values_list('service_id', flat=True))
        self.assertEqual(ids, {'SOON-1'})

    def test_excludes_decommissioned(self):
        """contract_end_before excludes services already marked decommissioned."""
        cutoff = date.today() + timedelta(days=30)
        results = self.filterset({'contract_end_before': cutoff.isoformat()}, self.queryset).qs
        self.assertNotIn('DECOM-SOON-1', results.values_list('service_id', flat=True))

    def test_excludes_beyond_cutoff(self):
        """contract_end_before excludes contracts ending after the given cutoff date."""
        cutoff = date.today() + timedelta(days=30)
        results = self.filterset({'contract_end_before': cutoff.isoformat()}, self.queryset).qs
        self.assertNotIn('LATER-1', results.values_list('service_id', flat=True))
