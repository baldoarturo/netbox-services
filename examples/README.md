# Service Examples

A tutorial per service type, showing how to create and fully set up a `Service` end to end: the API call that creates it, and the UI steps to attach the technical inventory that actually delivers it.

- [L2VPN](l2vpn.md) — a point-to-point L2L circuit between two sites
- [L3VPN](l3vpn.md) — a routed VPN over MPLS
- [DIA](dia.md) — dedicated internet access for a single customer site
- [IP Transit](transit.md) — wholesale internet transit for a downstream ISP
- [CDN](cdn.md) — a CDN edge node riding over an existing circuit
- [Voice](voice.md) — a hosted voice trunk

## Create-then-attach, or one shot?

`POST /api/plugins/services/` creates the `Service` and sets its business fields (`service_id`, `type`, `tenant`, dates, bandwidth, SLA, etc.). The technical inventory fields — `devices`, `interfaces`, `cables`, `vlans`, `prefixes`, `ip_addresses`, `vrfs`, `asns`, `route_targets`, `l2vpns`, `tunnels`, `virtual_machines`, `depends_on` — are writable too, either in that same payload or on a later `PATCH`.

Every example below still shows the two-step flow (create, then attach), since that's the clearer way to read a tutorial and matches the UI's own "Assign" buttons per card. But if you already know the PKs up front, you can pass them directly in the `POST` body and skip the follow-up step entirely:

```bash
curl -s -X POST "$NETBOX_URL/api/plugins/services/" \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "type": "dia", "service_id": "DIA-100", "devices": [12], "interfaces": [34] }'
```

1. Create the service via the API (or the **Add** button in the UI — same form either way).
2. Attach inventory either in that same call, a follow-up `PATCH`, or from the service's detail page using **Assign** on each relevant card.

## Prerequisites

- A NetBox API token with `add_service` permission (`Admin > API Tokens` or `/user/api-tokens/`).
- The IDs referenced below (device PKs, prefix PKs, etc.) are examples — substitute the actual PKs from your own NetBox instance. You can find them from each object's detail page URL, or by browsing `/api/dcim/devices/`, `/api/ipam/prefixes/`, etc.

```bash
export NETBOX_URL="https://netbox.example.com"
export NETBOX_TOKEN="<your-api-token>"
```

Every example uses this pattern:

```bash
curl -s -X POST "$NETBOX_URL/api/plugins/services/" \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

## Exporting what you've built

Once you have services set up, pull them back out:

- **CSV**, from the list view: open `/plugins/services/`, apply whatever filters you want (type, tenant, status, etc.), then use the **Export** button. The CSV only contains the filtered rows.
- **JSON**, from the API: `GET /api/plugins/services/?format=json` — filters work exactly like the UI, e.g. `?type=dia&status=active` for just the active DIA circuits.

```bash
# All active DIA services, as JSON
curl -s "$NETBOX_URL/api/plugins/services/?type=dia&status=active&format=json" \
  -H "Authorization: Token $NETBOX_TOKEN"
```
