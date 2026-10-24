from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from circuits.choices import CircuitStatusChoices
from tenancy.models import Tenant

from netbox_services.models import Service, ServiceAttachment, ServiceTypeChoices


class ServiceTestCase(TestCase):

    def test_str_returns_service_id(self):
        service = Service(service_id='NW-1', type=ServiceTypeChoices.CHOICES[0][0])
        self.assertEqual(str(service), 'NW-1')

    def test_get_absolute_url(self):
        service = Service.objects.create(service_id='NW-1', type='dia')
        self.assertEqual(service.get_absolute_url(), f'/plugins/services/{service.pk}/')

    def test_get_status_color(self):
        service = Service.objects.create(
            service_id='NW-1', type='dia', status=CircuitStatusChoices.STATUS_ACTIVE
        )
        self.assertEqual(
            service.get_status_color(),
            CircuitStatusChoices.colors.get(CircuitStatusChoices.STATUS_ACTIVE),
        )

    def test_clean_allows_valid_dates(self):
        service = Service(
            service_id='NW-1',
            type='dia',
            contract_start=date(2026, 1, 1),
            contract_end=date(2026, 12, 31),
            installed=date(2026, 1, 1),
            decommissioned=date(2026, 6, 1),
        )
        service.clean()

    def test_clean_rejects_contract_end_before_start(self):
        service = Service(
            service_id='NW-1',
            type='dia',
            contract_start=date(2026, 6, 1),
            contract_end=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_rejects_decommissioned_before_installed(self):
        service = Service(
            service_id='NW-1',
            type='dia',
            installed=date(2026, 6, 1),
            decommissioned=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_clean_rejects_decommissioned_before_requested_disconnect(self):
        service = Service(
            service_id='NW-1',
            type='dia',
            requested_disconnect=date(2026, 6, 1),
            decommissioned=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            service.clean()

    def test_service_id_must_be_unique(self):
        Service.objects.create(service_id='NW-1', type='dia')
        with self.assertRaises(Exception):
            Service.objects.create(service_id='NW-1', type='dia')

    def test_tenant_protect_on_delete(self):
        tenant = Tenant.objects.create(name='Acme', slug='acme')
        Service.objects.create(service_id='NW-1', type='dia', tenant=tenant)
        with self.assertRaises(Exception):
            tenant.delete()


class ServiceAttachmentTestCase(TestCase):

    def setUp(self):
        self.service = Service.objects.create(service_id='NW-1', type='dia')

    def test_str_returns_name(self):
        attachment = ServiceAttachment(service=self.service, name='Contract')
        self.assertEqual(str(attachment), 'Contract')

    def test_str_falls_back_to_file_name_when_no_name(self):
        attachment = ServiceAttachment(service=self.service, name='')
        attachment.file.name = 'contract.pdf'
        self.assertEqual(str(attachment), 'contract.pdf')

    def test_get_absolute_url_returns_service_url(self):
        attachment = ServiceAttachment.objects.create(service=self.service, name='Contract')
        self.assertEqual(attachment.get_absolute_url(), self.service.get_absolute_url())

    def test_deleting_service_cascades_to_attachment(self):
        attachment = ServiceAttachment.objects.create(service=self.service, name='Contract')
        self.service.delete()
        self.assertFalse(ServiceAttachment.objects.filter(pk=attachment.pk).exists())
