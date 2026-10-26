from datetime import date

from django.test import TestCase

from tenancy.models import Tenant

from netbox_services.filtersets import ServiceFilterSet, ServiceIncidentFilterSet
from netbox_services.models import Service, ServiceIncident


class ServiceFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
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
        results = self.filterset({'type': ['dia']}, self.queryset).qs
        self.assertEqual(results.count(), 2)

    def test_filter_by_service_id_icontains(self):
        results = self.filterset({'service_id': 'NW-1'}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_filter_by_tenant_id(self):
        results = self.filterset({'tenant_id': [self.tenant1.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-1')

    def test_filter_by_tenant_slug(self):
        results = self.filterset({'tenant': ['globex']}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_search_matches_service_id(self):
        results = self.filterset({'q': 'NW-2'}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_search_matches_description(self):
        results = self.filterset({'q': 'Backup'}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-3')

    def test_no_filters_returns_all(self):
        results = self.filterset({}, self.queryset).qs
        self.assertEqual(results.count(), 3)


class ServiceDependencyFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.dia = Service.objects.create(service_id='DIA-1', type='dia')
        cls.l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        cls.l3vpn.depends_on.add(cls.dia)

    def test_filter_by_depends_on_id(self):
        results = self.filterset({'depends_on_id': [self.dia.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'L3VPN-1')

    def test_filter_by_dependent_id(self):
        results = self.filterset({'dependent_id': [self.l3vpn.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'DIA-1')


class ServiceCapacityFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
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
        results = self.filterset({'bandwidth_min': 500}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_filter_by_bandwidth_max(self):
        results = self.filterset({'bandwidth_max': 500}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-1')

    def test_filter_by_cir_min(self):
        results = self.filterset({'cir_min': 500}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_filter_by_sla_uptime_percent_min(self):
        results = self.filterset({'sla_uptime_percent_min': 99.5}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-2')

    def test_filter_by_decommission_reason(self):
        results = self.filterset({'decommission_reason': ['churn']}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service_id, 'NW-3')


class ServiceIncidentFilterSetTestCase(TestCase):
    queryset = ServiceIncident.objects.all()
    filterset = ServiceIncidentFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.svc1 = Service.objects.create(service_id='NW-1', type='dia')
        cls.svc2 = Service.objects.create(service_id='NW-2', type='l3vpn')
        ServiceIncident.objects.create(
            service=cls.svc1, event_type='down', severity='critical', source='LibreNMS'
        )
        ServiceIncident.objects.create(
            service=cls.svc2, event_type='up', severity='minor', source='Zabbix'
        )

    def test_filter_by_service_id(self):
        results = self.filterset({'service_id': [self.svc1.pk]}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_filter_by_service_service_id(self):
        results = self.filterset({'service': ['NW-2']}, self.queryset).qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().service, self.svc2)

    def test_filter_by_event_type(self):
        results = self.filterset({'event_type': ['down']}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_filter_by_severity(self):
        results = self.filterset({'severity': ['critical']}, self.queryset).qs
        self.assertEqual(results.count(), 1)

    def test_search_matches_source(self):
        results = self.filterset({'q': 'Zabbix'}, self.queryset).qs
        self.assertEqual(results.count(), 1)


class ServiceContractExpiredFilterSetTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):
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
        results = self.filterset({'contract_expired': 'true'}, self.queryset).qs
        self.assertEqual(list(results.values_list('service_id', flat=True)), ['EXPIRED-1'])

    def test_contract_expired_false_includes_everything_else(self):
        results = self.filterset({'contract_expired': 'false'}, self.queryset).qs
        ids = set(results.values_list('service_id', flat=True))
        self.assertEqual(ids, {'DECOM-EXPIRED-1', 'CURRENT-1', 'NO-CONTRACT-1'})
