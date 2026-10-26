from django.test import RequestFactory, TestCase

from netbox_services.models import Service
from netbox_services.tables import ServiceListTable


class ServiceListTableTestCase(TestCase):

    def setUp(self):
        """Build a bare GET request for rendering the table against."""
        self.request = RequestFactory().get('/')

    def test_depends_on_column_renders_linked_service(self):
        """The depends_on column renders a link to the depended-on service."""
        dia = Service.objects.create(service_id='DIA-1', type='dia')
        l3vpn = Service.objects.create(service_id='L3VPN-1', type='l3vpn')
        l3vpn.depends_on.add(dia)

        table = ServiceListTable(Service.objects.all())
        table_html = table.as_html(self.request)
        self.assertIn('DIA-1', table_html)

    def test_depends_on_column_empty_when_no_dependency(self):
        """The depends_on column renders the empty-value placeholder when there's no dependency."""
        Service.objects.create(service_id='DIA-1', type='dia')

        table = ServiceListTable(Service.objects.all())
        self.assertEqual(table.rows[0].get_cell('depends_on'), '—')
