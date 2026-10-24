from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from utilities.testing import APITestCase

from netbox_services.models import Service


class ServiceAPITestCase(APITestCase):
    model = Service

    @classmethod
    def setUpTestData(cls):
        Service.objects.create(service_id='NW-1', type='dia')
        Service.objects.create(service_id='NW-2', type='l3vpn')

    def test_list_services(self):
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_get_service(self):
        self.add_permissions('netbox_services.view_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_id'], 'NW-1')

    def test_create_service(self):
        self.add_permissions('netbox_services.add_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        data = {
            'type': 'cdn',
            'service_id': 'NW-3',
            'status': 'active',
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Service.objects.filter(service_id='NW-3').exists())

    def test_create_service_without_permission_is_forbidden(self):
        url = reverse('plugins-api:netbox_services-api:service-list')
        data = {
            'type': 'cdn',
            'service_id': 'NW-4',
            'status': 'active',
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_service(self):
        self.add_permissions('netbox_services.change_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.patch(url, {'description': 'Updated'}, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.description, 'Updated')

    def test_delete_service(self):
        self.add_permissions('netbox_services.delete_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Service.objects.filter(pk=service.pk).exists())


class ServiceDependencyAPITestCase(APITestCase):
    model = Service

    @classmethod
    def setUpTestData(cls):
        cls.dia = Service.objects.create(service_id='DIA-1', type='dia')
        cls.l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        cls.l3vpn.depends_on.add(cls.dia)

    def test_depends_on_is_exposed_in_detail(self):
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': self.l3vpn.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['depends_on'], [self.dia.pk])

    def test_dependents_is_exposed_in_detail(self):
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': self.dia.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dependents'], [self.l3vpn.pk])

    def test_filter_by_depends_on_id(self):
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        response = self.client.get(url, {'depends_on_id': self.dia.pk}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['service_id'], 'L3VPN-1')


class ServiceCapacityAPITestCase(APITestCase):
    model = Service

    @classmethod
    def setUpTestData(cls):
        Service.objects.create(
            service_id='NW-1', type='dia', bandwidth=1000, cir=500, sla_uptime_percent='99.90'
        )

    def test_capacity_fields_exposed_in_detail(self):
        self.add_permissions('netbox_services.view_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bandwidth'], 1000)
        self.assertEqual(response.data['cir'], 500)
        self.assertEqual(response.data['sla_uptime_percent'], Decimal('99.90'))

    def test_filter_by_bandwidth_min(self):
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        response = self.client.get(url, {'bandwidth_min': 500}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_service_rejects_cir_above_bandwidth(self):
        self.add_permissions('netbox_services.add_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        data = {
            'type': 'dia',
            'service_id': 'NW-2',
            'bandwidth': 100,
            'cir': 200,
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
