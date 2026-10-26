from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from dcim.models import Device, DeviceRole, DeviceType, Interface, Manufacturer, Site
from users.models import ObjectPermission

from netbox_services.models import Service, ServiceIncident

User = get_user_model()


class ServiceViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(service_id='NW-1', type='dia')

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.client = Client()
        self.client.force_login(self.user)

    def _grant(self, *actions):
        permission = ObjectPermission.objects.create(
            name='Service permission',
            actions=list(actions),
        )
        permission.object_types.add(
            __import__('django.contrib.contenttypes.models', fromlist=['ContentType'])
            .ContentType.objects.get_for_model(Service)
        )
        permission.users.add(self.user)

    def test_list_view_requires_permission(self):
        url = reverse('plugins:netbox_services:service_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_list_view_with_permission(self):
        self._grant('view')
        url = reverse('plugins:netbox_services:service_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NW-1')

    def test_list_view_csv_export(self):
        self._grant('view')
        url = reverse('plugins:netbox_services:service_list')
        response = self.client.get(url, {'export': 'table'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('NW-1', response.content.decode())

    def test_list_view_csv_export_respects_filters(self):
        Service.objects.create(service_id='NW-2', type='l3vpn')
        self._grant('view')
        url = reverse('plugins:netbox_services:service_list')
        response = self.client.get(url, {'export': 'table', 'type': 'dia'})
        content = response.content.decode()
        self.assertIn('NW-1', content)
        self.assertNotIn('NW-2', content)

    def test_detail_view_with_permission(self):
        self._grant('view')
        url = reverse('plugins:netbox_services:service_view', kwargs={'pk': self.service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_view_creates_service(self):
        self._grant('view', 'add')
        url = reverse('plugins:netbox_services:service_add')
        response = self.client.post(url, {
            'type': 'dia',
            'service_id': 'NW-2',
            'status': 'active',
        })
        self.assertEqual(Service.objects.filter(service_id='NW-2').count(), 1)

    def test_delete_view_removes_service(self):
        self._grant('view', 'delete')
        url = reverse('plugins:netbox_services:service_delete', kwargs={'pk': self.service.pk})
        self.client.post(url, {'confirm': True})
        self.assertFalse(Service.objects.filter(pk=self.service.pk).exists())


class ImpactSearchViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        manufacturer = Manufacturer.objects.create(name='Acme', slug='acme')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Router', slug='router')
        role = DeviceRole.objects.create(name='Router', slug='router')
        site = Site.objects.create(name='Site 1', slug='site-1')
        cls.device = Device.objects.create(
            name='router-1', site=site, device_type=device_type, role=role
        )
        cls.interface = Interface.objects.create(device=cls.device, name='eth0', type='1000base-t')

        cls.dia = Service.objects.create(service_id='DIA-1', type='dia')
        cls.dia.interfaces.add(cls.interface)
        cls.cdn = Service.objects.create(service_id='CDN-1', type='cdn')
        cls.cdn.depends_on.add(cls.dia)
        cls.unrelated = Service.objects.create(service_id='UNRELATED-1', type='voice')

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser')
        self.client = Client()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('plugins:netbox_services:impact_search'))
        self.assertEqual(response.status_code, 302)

    def test_no_query_params_shows_empty_form(self):
        response = self.client.get(reverse('plugins:netbox_services:impact_search'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Directly affected', response.content.decode())

    def test_search_by_interface_finds_direct_and_cascaded(self):
        response = self.client.get(
            reverse('plugins:netbox_services:impact_search'),
            {'interface': self.interface.pk},
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        direct_idx = content.find('Directly affected')
        cascaded_idx = content.find('Also affected')
        self.assertIn('DIA-1', content[direct_idx:cascaded_idx])
        self.assertIn('CDN-1', content[cascaded_idx:])
        self.assertNotIn('UNRELATED-1', content)

    def test_search_by_device_finds_only_direct_match(self):
        self.dia.devices.add(self.device)
        response = self.client.get(
            reverse('plugins:netbox_services:impact_search'),
            {'device': self.device.pk},
        )
        content = response.content.decode()
        direct_idx = content.find('Directly affected')
        cascaded_idx = content.find('Also affected')
        self.assertIn('DIA-1', content[direct_idx:cascaded_idx])
        self.assertIn('CDN-1', content[cascaded_idx:])


class ServiceIncidentAddViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(service_id='NW-1', type='dia')

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.client = Client()
        self.client.force_login(self.user)

    def _grant(self, *actions):
        from django.contrib.contenttypes.models import ContentType
        permission = ObjectPermission.objects.create(
            name='Incident permission',
            actions=list(actions),
        )
        permission.object_types.add(ContentType.objects.get_for_model(ServiceIncident))
        permission.users.add(self.user)

    def test_add_view_requires_permission(self):
        url = reverse('plugins:netbox_services:service_incident_add', kwargs={'pk': self.service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_add_view_form_excludes_occurred_at(self):
        self._grant('add')
        url = reverse('plugins:netbox_services:service_incident_add', kwargs={'pk': self.service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="occurred_at"')

    def test_post_creates_incident_and_redirects_to_service(self):
        self._grant('add')
        url = reverse('plugins:netbox_services:service_incident_add', kwargs={'pk': self.service.pk})
        response = self.client.post(url, {
            'event_type': 'down',
            'severity': 'critical',
            'description': 'Fiber cut',
            'source': 'Manual (NOC)',
        })
        incident = ServiceIncident.objects.get(service=self.service)
        self.assertEqual(incident.description, 'Fiber cut')
        self.assertIsNotNone(incident.occurred_at)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.service.get_absolute_url())


class ContractsViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        from datetime import date, timedelta
        today = date.today()
        Service.objects.create(
            service_id='EXPIRED-1', type='dia', status='active',
            contract_start=date(2024, 1, 1), contract_end=date(2025, 1, 1),
        )
        Service.objects.create(
            service_id='DECOM-EXPIRED-1', type='dia', status='decommissioned',
            contract_start=date(2024, 1, 1), contract_end=date(2025, 1, 1),
        )
        Service.objects.create(
            service_id='EXPIRING-SOON-1', type='dia', status='active',
            contract_start=date(2026, 1, 1), contract_end=today + timedelta(days=5),
        )
        Service.objects.create(
            service_id='FAR-FUTURE-1', type='dia', status='active',
            contract_start=date(2026, 1, 1), contract_end=today + timedelta(days=400),
        )

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.client = Client()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('plugins:netbox_services:contracts'))
        self.assertEqual(response.status_code, 302)

    def test_no_filter_shows_empty_table(self):
        response = self.client.get(reverse('plugins:netbox_services:contracts'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('EXPIRED-1', content)
        self.assertNotIn('FAR-FUTURE-1', content)

    def test_already_expired_excludes_decommissioned(self):
        response = self.client.get(
            reverse('plugins:netbox_services:contracts'), {'contract_expired': 'true'}
        )
        content = response.content.decode()
        self.assertIn('EXPIRED-1', content)
        self.assertNotIn('DECOM-EXPIRED-1', content)
        self.assertNotIn('FAR-FUTURE-1', content)

    def test_custom_date_filters_to_window(self):
        from datetime import date, timedelta
        cutoff = date.today() + timedelta(days=30)
        response = self.client.get(
            reverse('plugins:netbox_services:contracts'),
            {'contract_end_before': cutoff.isoformat()},
        )
        content = response.content.decode()
        self.assertIn('EXPIRING-SOON-1', content)
        self.assertNotIn('FAR-FUTURE-1', content)
        self.assertNotIn('EXPIRED-1', content)
