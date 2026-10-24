from django.test import TestCase

from tenancy.models import Tenant

from netbox_services.filtersets import ServiceFilterSet
from netbox_services.models import Service


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
