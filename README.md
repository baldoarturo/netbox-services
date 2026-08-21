# NetBox Services Plugin

A NetBox plugin for **service providers** who need a service-centric inventory on top of DCIM/IPAM.

NetBox already models devices, prefixes, circuits, and VRFs. What it does not model natively is the **commercial / operational service** that those objects deliver — the Cogent DIA circuit `NW-123456`, the customer L3VPN, the IP transit handoff.

This plugin adds a `Service` object: a unique service ID, a type, a tenant, a lifecycle, and many-to-many links to the NetBox objects that implement it. Tags are still useful for loose labels; a Service is the object you open when someone asks “what does this customer product actually run on?”

## What a Service is

Each Service has:

| Area | Fields |
| --- | --- |
| Identity | Unique `service_id`, type (L2VPN, L3VPN, DIA, IP Transit, CDN, Voice), description, status, tenant |
| Lifecycle | Order date, planned activation, installed, contract start/end, requested disconnect, decommissioned |
| Delivery | Devices, interfaces, cables, VLANs, prefixes, VRFs, ASNs, route targets, L2VPNs, tunnels, VMs |
| Files | PDF/other files (`ServiceAttachment`) plus NetBox image attachments (photos) on the Images tab |

Status reuses NetBox circuit statuses so services line up with how circuits are already tracked.

Date checks: contract end cannot precede start; decommissioned cannot precede installed or requested disconnect.

## Why not just tags?

Tagging a prefix `dia` does not tell you which customer product it belongs to, when it was ordered, or which handoff interface delivers it.

With a Service you can, for example, create DIA `NW-123456` for a tenant and then:

- Point at the PE/CE devices and the exact interfaces
- Attach the WAN prefixes, VRF, and ASN
- Record order / install / contract dates
- Store the signed PDF and site photos next to the inventory

The detail page is split for that workflow: **technical inventory on the left**, **lifecycle and attachments on the right**.

## Features

- CRUD for business services from **Business Services** in the nav
- Relate/unrelate DCIM, IPAM, VPN, and virtualization objects from the service detail view
- Filter and search by service ID, description, tenant, status, and dates
- Bulk delete from the list view
- Changelog, tags, and custom fields (`NetBoxModel`)
- REST API under `/api/plugins/services/` (list/detail include `id` and lifecycle fields)
- File attachments and native image attachments

## Usage

1. Open **Business Services** in the plugin menu.
2. Create a service (ID + type at minimum).
3. On the detail page, use **Assign** on each technical card to attach inventory.
4. Fill lifecycle dates when the order, install, or disconnect happens.
5. Add contracts/PDFs under **Attachments**; photos go on the **Images** tab.

![Plugin screenshot](https://github.com/baldoarturo/netbox-services/raw/master/02-main.png)

## Requirements

- NetBox 4.4+
- Python 3.10+

## Installation

Install the package:

```bash
pip install netbox-services
```

Or clone this repo next to your NetBox plugins and install in editable mode.

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

The UI lives at `/plugins/services/`. The API lives at `/api/plugins/services/` (no extra `/services/` segment).

## License

MIT

