from django.test import TestCase

from tenancy.models import Tenant

from netbox_services.forms import ImpactSearchForm, NewServiceForm
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


class ImpactSearchFormTestCase(TestCase):

    def test_interface_field_scopes_to_selected_device(self):
        # The interface field must declare device -> device_id as a dynamic
        # query param so its widget only offers interfaces belonging to
        # whichever device is chosen elsewhere in the same form, the same
        # way ServiceRelatedInterfacesForm scopes interfaces to a service's
        # already-assigned devices.
        field = ImpactSearchForm().fields['interface']
        self.assertEqual(
            field.widget.attrs.get('data-dynamic-params'),
            '[{"fieldName":"device","queryParam":"device_id"}]',
        )
