from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from utilities.testing import APITestCase

from netbox_services.models import Service, ServiceIncident


class ServiceAPITestCase(APITestCase):
    model = Service

    @classmethod
    def setUpTestData(cls):
        """Create two services to list/retrieve/update/delete against."""
        Service.objects.create(service_id='NW-1', type='dia')
        Service.objects.create(service_id='NW-2', type='l3vpn')

    def test_list_services(self):
        """GET the list endpoint returns both services."""
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_list_services_as_json_export(self):
        """?format=json returns the same list as a plain JSON response."""
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        response = self.client.get(url, {'format': 'json'}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.data['count'], 2)

    def test_get_service(self):
        """GET the detail endpoint returns the requested service."""
        self.add_permissions('netbox_services.view_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_id'], 'NW-1')

    def test_create_service(self):
        """POST with add permission creates a new service."""
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
        """POST without add permission is rejected with 403."""
        url = reverse('plugins-api:netbox_services-api:service-list')
        data = {
            'type': 'cdn',
            'service_id': 'NW-4',
            'status': 'active',
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_service(self):
        """PATCH with change permission updates the service."""
        self.add_permissions('netbox_services.change_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.patch(url, {'description': 'Updated'}, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.description, 'Updated')

    def test_delete_service(self):
        """DELETE with delete permission removes the service."""
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
        """Create a DIA and an L3VPN, with the L3VPN depending on the DIA."""
        cls.dia = Service.objects.create(service_id='DIA-1', type='dia')
        cls.l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        cls.l3vpn.depends_on.add(cls.dia)

    def test_depends_on_is_exposed_in_detail(self):
        """The detail response includes the service's depends_on PKs."""
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': self.l3vpn.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['depends_on'], [self.dia.pk])

    def test_dependents_is_exposed_in_detail(self):
        """The detail response includes the service's dependents PKs (reverse of depends_on)."""
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': self.dia.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dependents'], [self.l3vpn.pk])

    def test_filter_by_depends_on_id(self):
        """?depends_on_id=<pk> filters the list to services depending on that service."""
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
        """Create a service with bandwidth/CIR/SLA fields set."""
        Service.objects.create(
            service_id='NW-1', type='dia', bandwidth=1000, cir=500, sla_uptime_percent='99.90'
        )

    def test_capacity_fields_exposed_in_detail(self):
        """The detail response includes bandwidth, cir, and sla_uptime_percent."""
        self.add_permissions('netbox_services.view_service')
        service = Service.objects.get(service_id='NW-1')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': service.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bandwidth'], 1000)
        self.assertEqual(response.data['cir'], 500)
        self.assertEqual(response.data['sla_uptime_percent'], Decimal('99.90'))

    def test_filter_by_bandwidth_min(self):
        """?bandwidth_min=<value> filters the list to services at or above that bandwidth."""
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-list')
        response = self.client.get(url, {'bandwidth_min': 500}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_service_rejects_cir_above_bandwidth(self):
        """POSTing a CIR greater than bandwidth is rejected with 400 (model clean() enforced by the serializer)."""
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


class ServiceIncidentAPITestCase(APITestCase):
    model = ServiceIncident

    @classmethod
    def setUpTestData(cls):
        """Create a service to log incidents against."""
        cls.service = Service.objects.create(service_id='NW-1', type='dia')

    def test_create_incident_by_service_id(self):
        """POSTing an incident identifies the service by its service_id, not its numeric PK."""
        self.add_permissions('netbox_services.add_serviceincident')
        url = reverse('plugins-api:netbox_services-api:serviceincident-list')
        data = {
            'service': 'NW-1',
            'event_type': 'down',
            'severity': 'critical',
            'description': 'Interface down',
            'source': 'LibreNMS',
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['service'], 'NW-1')
        self.assertIsNotNone(response.data['occurred_at'])

    def test_create_incident_ignores_supplied_occurred_at(self):
        """A caller-supplied occurred_at in the payload is ignored in favor of the server's own clock."""
        self.add_permissions('netbox_services.add_serviceincident')
        url = reverse('plugins-api:netbox_services-api:serviceincident-list')
        fake_past = datetime(2000, 1, 1, tzinfo=dt_timezone.utc).isoformat()
        data = {
            'service': 'NW-1',
            'event_type': 'down',
            'occurred_at': fake_past,
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('2000-01-01', response.data['occurred_at'])

    def test_create_incident_for_unknown_service_is_400(self):
        """POSTing an incident for a nonexistent service_id is rejected with 400."""
        self.add_permissions('netbox_services.add_serviceincident')
        url = reverse('plugins-api:netbox_services-api:serviceincident-list')
        data = {
            'service': 'DOES-NOT-EXIST',
            'event_type': 'down',
        }
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_incident_without_permission_is_forbidden(self):
        """POSTing an incident without add permission is rejected with 403."""
        url = reverse('plugins-api:netbox_services-api:serviceincident-list')
        data = {'service': 'NW-1', 'event_type': 'down'}
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_incidents_filtered_by_service(self):
        """?service=<service_id> filters the incident list to that service's own incidents."""
        other_service = Service.objects.create(service_id='NW-2', type='l3vpn')
        ServiceIncident.objects.create(service=self.service, event_type='down')
        ServiceIncident.objects.create(service=other_service, event_type='down')

        self.add_permissions('netbox_services.view_serviceincident')
        url = reverse('plugins-api:netbox_services-api:serviceincident-list')
        response = self.client.get(url, {'service': 'NW-1'}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class ServiceMTTRAPITestCase(APITestCase):
    model = Service

    @classmethod
    def setUpTestData(cls):
        """Create a service to compute MTTR/uptime against."""
        cls.service = Service.objects.create(service_id='NW-1', type='dia')

    def _incident(self, event_type, occurred_at):
        """Create an incident and force its occurred_at to a specific timestamp for the test."""
        incident = ServiceIncident.objects.create(service=self.service, event_type=event_type)
        incident.occurred_at = occurred_at
        incident.save()
        return incident

    def test_fields_are_none_without_incidents(self):
        """mttr_seconds and uptime_percent are both null when the service has no incidents."""
        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': self.service.pk})
        response = self.client.get(url, **self.header)
        self.assertIsNone(response.data['mttr_seconds'])
        self.assertIsNone(response.data['uptime_percent'])

    def test_mttr_excludes_degraded_unless_requested(self):
        """mttr_seconds is null by default for a degraded-only outage, but populated with ?include_degraded=1."""
        now = timezone.now()
        self._incident('degraded', now - timedelta(hours=5))
        self._incident('up', now - timedelta(hours=1))

        self.add_permissions('netbox_services.view_service')
        url = reverse('plugins-api:netbox_services-api:service-detail', kwargs={'pk': self.service.pk})

        response = self.client.get(url, **self.header)
        self.assertIsNone(response.data['mttr_seconds'])

        response = self.client.get(url, {'include_degraded': '1'}, **self.header)
        self.assertIsNotNone(response.data['mttr_seconds'])
