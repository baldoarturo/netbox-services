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
