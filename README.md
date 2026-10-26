# NetBox Services Plugin

[![Upload Python Package](https://github.com/baldoarturo/netbox-services/actions/workflows/python-publish.yml/badge.svg)](https://github.com/baldoarturo/netbox-services/actions/workflows/python-publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/netbox-services.svg)](https://pypi.org/project/netbox-services/)

A NetBox plugin for **service providers** who need a service-centric inventory on top of DCIM/IPAM.

It adds a `Service` object: a unique ID, a type, a tenant, a lifecycle, and links out to whatever DCIM/IPAM/VPN objects actually deliver it — the PE/CE devices, interfaces, prefixes, VRFs, whatever makes up the Cogent DIA circuit `NW-123456` or the customer's L3VPN. It's the page you open when someone asks "what does this customer's product actually run on?"

## What a Service is

Each Service has:

| Area | Fields |
| --- | --- |
| Identity | Unique `service_id`, type (L2VPN, L3VPN, DIA, IP Transit, CDN, Voice), description, status, tenant |
| Capacity | Bandwidth and CIR (Mbps), SLA uptime target |
| Lifecycle | Order date, planned activation, installed, contract start/end, requested disconnect, decommissioned, decommission reason |
| Delivery | Devices, interfaces, cables, VLANs, prefixes, IP addresses, VRFs, ASNs, route targets, L2VPNs, tunnels, VMs |
| Dependencies | Other services this one depends on, and the services that depend on it in turn |
| Incidents | Down/up events reported against the service, typically pushed by an external NMS |
| Files | PDF/other files (`ServiceAttachment`) plus NetBox image attachments (photos) on the Images tab |

Status reuses NetBox circuit statuses so services line up with how circuits are already tracked.

## Why not just tags?

A tag is a label; a Service is a record. Tagging a prefix `dia` doesn't tell you which customer it's for, when it was ordered, or which interface hands it off — a Service does.

Say you're onboarding DIA `NW-123456` for a tenant. With a Service you'd:

- Point at the PE/CE devices and the exact interfaces
- Attach the WAN prefixes, VRF, and ASN
- Log the order / install / contract dates
- Keep the signed PDF and site photos right next to the inventory

The detail page is laid out for that: technical inventory on the left, lifecycle and paperwork on the right.

## Features

- CRUD for business services from **Business Services** in the nav
- Relate/unrelate DCIM, IPAM, VPN, and virtualization objects from the service detail view
- Service-to-service dependencies (e.g. a CDN service riding over an L2L circuit), with direct and
  indirect cycle detection, visible on the detail page and the list view
- Bandwidth/CIR and an SLA uptime target per service, plus a decommission reason for churn tracking
- Incident history per service: an external NMS can `POST` a down/degraded/up/other event by
  `service_id`, and NetBox stamps the time it received it rather than trusting a caller-supplied
  timestamp. Incidents can also be logged by hand from the service detail page
- MTTR and uptime %, derived from that incident history and shown against the service's own
  `sla_uptime_percent` (Meeting SLA / Below SLA). Excludes `degraded` events by default — only a
  full `down` counts against SLA — but that's a toggle (`?include_degraded=1`), not a fixed rule
- Filter and search by service ID, description, tenant, status, dates, dependencies, bandwidth/CIR
  range, SLA uptime, decommission reason, and incident event type/severity
- A **Contract Expired** tab on the list view: services past `contract_end` that haven't been
  formally decommissioned, one click away from the full list
- **Impact Search**: pick a device, interface, cable, VLAN, prefix, IP address, VRF, ASN, route
  target, L2VPN, tunnel, or VM, and see every service that would be affected if it were
  removed — both the services that reference it directly and, through `depends_on`, the services
  that depend on those in turn
- Bulk delete from the list view
- Changelog, tags, and custom fields (`NetBoxModel`)
- REST API under `/api/plugins/services/` (list/detail include `id`, lifecycle fields, and
  dependencies; query-string filtering works the same as the UI)
- CSV export from the list view (**Export** button) and JSON export via the REST API
  (`?format=json`), both respecting whatever filters are currently applied
- File attachments and native image attachments

## Usage

1. Open **Business Services** in the plugin menu.
2. Create a service — ID and type is all you need to start.
3. On the detail page, hit **Assign** on each technical card to attach inventory.
4. Fill in lifecycle dates as the order, install, or disconnect actually happen.
5. Drop contracts/PDFs under **Attachments**; photos go on the **Images** tab.

See [examples/](examples/) for a worked tutorial per service type (L2VPN, L3VPN, DIA, IP Transit, CDN, Voice), each with the API payload to create it and the UI steps to attach its inventory.

![Plugin screenshot](https://github.com/baldoarturo/netbox-services/raw/master/02-main.png)

## Requirements

- NetBox 4.4+
- Python 3.10+

## Installation

Install the package:

```bash
pip install netbox-services
```

Or clone this repo next to your NetBox plugins and install it in editable mode if you want to hack on it.

Enable it in `configuration.py`:

```python
PLUGINS = [
    'netbox_services',
]
```

Apply migrations and restart NetBox:

```bash
python manage.py migrate netbox_services
```

The UI lives at `/plugins/services/`. The API lives at `/api/plugins/services/`.

## License

MIT

