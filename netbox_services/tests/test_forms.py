from django.test import TestCase

from tenancy.models import Tenant

from netbox_services.forms import NewServiceForm
from netbox_services.models import Service


class NewServiceFormTestCase(TestCase):

    def test_valid_minimal_data(self):
        form = NewServiceForm(data={
            'type': 'dia',
            'service_id': 'NW-1',
            'status': 'active',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields_is_invalid(self):
        form = NewServiceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('type', form.errors)
        self.assertIn('service_id', form.errors)

    def test_duplicate_service_id_is_invalid(self):
        Service.objects.create(service_id='NW-1', type='dia')
        form = NewServiceForm(data={
            'type': 'l3vpn',
            'service_id': 'NW-1',
            'status': 'active',
        })
        self.assertFalse(form.is_valid())

    def test_contract_end_before_start_is_invalid(self):
        form = NewServiceForm(data={
            'type': 'dia',
            'service_id': 'NW-1',
            'status': 'active',
            'contract_start': '2026-06-01',
            'contract_end': '2026-01-01',
        })
        self.assertFalse(form.is_valid())

    def test_accepts_tenant(self):
        tenant = Tenant.objects.create(name='Acme', slug='acme')
        form = NewServiceForm(data={
            'type': 'dia',
            'service_id': 'NW-1',
            'status': 'active',
            'tenant': tenant.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)
