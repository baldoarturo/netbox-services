import calendar
from datetime import timedelta

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from utilities.views import ConditionalLoginRequiredMixin, register_model_view
from netbox.views.generic import (
    ObjectView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    BulkDeleteView,
)

from .models import Service, ServiceAttachment, ServiceIncident
from .tables import ServiceContractsTable, ServiceListTable
from .forms import (
    IMPACT_SEARCH_FIELDS,
    IMPACT_SEARCH_SERVICE_FIELD,
    ImpactSearchForm,
    NewServiceForm,
    ServiceAttachmentForm,
    ServiceFilterSetForm,
    ServiceIncidentForm,
)

from .filtersets import ServiceFilterSet

#
#   GENERIC VIEWS
#


@register_model_view(Service, name='view', path='', detail=True)
class ServiceView(ObjectView):
    queryset = Service.objects.prefetch_related('attachments', 'images', 'tags', 'incidents')
    template_name = 'netbox_services/service.html'

    def get_extra_context(self, request, instance):
        """Compute MTTR/uptime for the detail page, honoring the ?include_degraded=1 toggle."""
        include_degraded = request.GET.get('include_degraded') == '1'
        return {
            'include_degraded': include_degraded,
            'mttr': instance.mttr(include_degraded=include_degraded),
            'uptime_percent': instance.uptime_percent(include_degraded=include_degraded),
        }

@register_model_view(Service, name='list', path='', detail=False)
class ServiceListView(ObjectListView):
    queryset = Service.objects.all()
    table = ServiceListTable
    filterset = ServiceFilterSet
    filterset_form = ServiceFilterSetForm

@register_model_view(Service, name='add', path='add', detail=False)
class ServiceAddView(ObjectEditView):
    queryset = Service.objects.all()
    form = NewServiceForm


@register_model_view(Service, name='edit', detail=True)
class ServiceEditView(ObjectEditView):
    queryset = Service.objects.all()
    form = NewServiceForm


@register_model_view(Service, name='delete', detail=True)
class ServiceDeleteView(ObjectDeleteView):
    queryset = Service.objects.all()


@register_model_view(Service, name='bulk_delete', path='delete', detail=False)
class ServiceBulkDeleteView(BulkDeleteView):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet
    table = ServiceListTable


class ServiceAttachmentEditView(ObjectEditView):
    """Create or edit a ServiceAttachment nested under its parent service's URL."""
    queryset = ServiceAttachment.objects.all()
    form = ServiceAttachmentForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        """Assign the parent service (from the URL) to a newly-created attachment."""
        if not obj.pk:
            obj.service = get_object_or_404(Service, pk=url_kwargs.get('pk'))
        return obj

    def get_object(self, **kwargs):
        """Look up by attachment_pk (not the URL's service pk) when editing an existing attachment."""
        if attachment_pk := kwargs.get('attachment_pk'):
            return get_object_or_404(self.queryset, pk=attachment_pk)
        return self.queryset.model()


class ServiceAttachmentDeleteView(ObjectDeleteView):
    """Delete a ServiceAttachment nested under its parent service's URL."""
    queryset = ServiceAttachment.objects.all()

    def get_object(self, **kwargs):
        """Look up the attachment by attachment_pk rather than the URL's service pk."""
        return get_object_or_404(self.queryset, pk=kwargs.get('attachment_pk'))


class ServiceIncidentAddView(ObjectEditView):
    """
    Create-only view for logging an incident against a service from the UI.
    Incidents aren't edited or deleted once logged (occurred_at is
    server-assigned and never meant to change), so this only needs a create
    path, unlike ServiceAttachmentEditView which also handles edits.
    """
    queryset = ServiceIncident.objects.all()
    form = ServiceIncidentForm

    def dispatch(self, request, *args, **kwargs):
        """
        Force the 'add' permission check regardless of URL kwargs. The URL
        kwarg here is the Service's pk, not an incident's, so this always
        creates a new incident. ObjectEditView.dispatch() would otherwise
        read `kwargs` being non-empty as "editing" and require the 'change'
        permission instead of 'add'.
        """
        self._permission_action = 'add'
        return super(ObjectEditView, self).dispatch(request, *args, **kwargs)

    def alter_object(self, obj, request, url_args, url_kwargs):
        """Assign the parent service (from the URL) to the new incident."""
        if not obj.pk:
            obj.service = get_object_or_404(Service, pk=url_kwargs.get('pk'))
        return obj

    def get_object(self, **kwargs):
        """Always return a new, unsaved incident -- this view never edits an existing one."""
        return self.queryset.model()

#
#   TREE VIEWS
#
@register_model_view(Service, name='tree', detail=True)
class ServiceTreeView(ObjectView):
    queryset = Service.objects.all()
    template_name = 'netbox_services/tree.html'

#
#   RELATION VIEWS
#


class ServiceRelatedObjectsView(ObjectEditView):
    """
    Generic edit view for assigning one of Service's related-object M2M fields.
    The form to use (and therefore which field is being edited) is supplied
    per-URL via `.as_view(form=...)` in urls.py, avoiding ~10 near-identical
    subclasses that differed only in which form they used.
    """
    queryset = Service.objects.all()


#
#   IMPACT SEARCH
#


def _affected_services(obj, service_field):
    """Services directly linked to `obj` through `service_field`."""
    return Service.objects.filter(**{service_field: obj})


def _cascade_dependents(services):
    """
    Breadth-first walk of depends_on's reverse relation (dependents): starting
    from a set of directly-affected services, find every service that depends
    on one of them, transitively. Returns the full set including the starting
    services.
    """
    affected = {s.pk: s for s in services}
    frontier = list(services)
    while frontier:
        next_frontier = []
        for service in frontier:
            for dependent in service.dependents.all():
                if dependent.pk not in affected:
                    affected[dependent.pk] = dependent
                    next_frontier.append(dependent)
        frontier = next_frontier
    return affected


class ImpactSearchView(ConditionalLoginRequiredMixin, View):
    """
    "What breaks if I remove this?" search: pick a technical object (device,
    interface, prefix, etc.) and see every Service affected directly, plus
    any service that depends on those in turn.
    """
    template_name = 'netbox_services/impact_search.html'

    def get(self, request):
        """Resolve whichever ImpactSearchForm field was submitted and compute direct + cascaded impact."""
        form = ImpactSearchForm(request.GET or None)
        direct = []
        cascaded = []
        searched_field = None

        if form.is_valid():
            for field_name in IMPACT_SEARCH_FIELDS:
                obj = form.cleaned_data.get(field_name)
                if obj:
                    searched_field = field_name
                    service_field = IMPACT_SEARCH_SERVICE_FIELD[field_name]
                    direct = list(_affected_services(obj, service_field))
                    all_affected = _cascade_dependents(direct)
                    direct_pks = {s.pk for s in direct}
                    cascaded = [s for pk, s in all_affected.items() if pk not in direct_pks]
                    break

        return render(request, self.template_name, {
            'form': form,
            'searched_field': searched_field,
            'direct_services': direct,
            'cascaded_services': cascaded,
        })


#
#   CONTRACTS
#


class ContractsView(ConditionalLoginRequiredMixin, View):
    """
    Services grouped by contract status: already expired, or expiring by a
    chosen date (quick picks for this week/month/quarter, or an arbitrary
    date via the picker). Lives on its own page rather than as extra
    controls on the main service list, which doesn't need five buttons and
    a date field cluttering its toolbar for a need this specific.
    """
    template_name = 'netbox_services/contracts.html'

    def get(self, request):
        """Compute the week/month/quarter cutoff dates and filter services by the selected contract-status tab."""
        today = timezone.localdate()

        end_of_week = today + timedelta(days=6 - today.weekday())
        end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        quarter_end_month = 3 * ((today.month - 1) // 3 + 1)
        end_of_quarter = today.replace(
            month=quarter_end_month,
            day=calendar.monthrange(today.year, quarter_end_month)[1],
        )

        is_expired = request.GET.get('contract_expired') == 'true'
        contract_end_before = request.GET.get('contract_end_before')

        if is_expired:
            queryset = ServiceFilterSet({'contract_expired': 'true'}, Service.objects.all()).qs
        elif contract_end_before:
            queryset = ServiceFilterSet(
                {'contract_end_before': contract_end_before}, Service.objects.all()
            ).qs
        else:
            queryset = Service.objects.none()

        table = ServiceContractsTable(queryset)
        table.configure(request)

        return render(request, self.template_name, {
            'table': table,
            'contract_expired_count': ServiceFilterSet(
                {'contract_expired': 'true'}, Service.objects.all()
            ).qs.count(),
            'is_expired_tab': is_expired,
            'end_of_week': end_of_week,
            'end_of_month': end_of_month,
            'end_of_quarter': end_of_quarter,
            'is_week_tab': contract_end_before == str(end_of_week),
            'is_month_tab': contract_end_before == str(end_of_month),
            'is_quarter_tab': contract_end_before == str(end_of_quarter),
            'contract_end_before': contract_end_before,
        })
