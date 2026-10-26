# CDN: edge node riding over an existing circuit

**Scenario:** a CDN caching/edge service deployed on hardware at a customer site, delivered over an L2L or DIA circuit you already provide. This is the canonical example for `depends_on`: the CDN node doesn't work without the circuit underneath it.

## 1. Create the service

```bash
curl -s -X POST "$NETBOX_URL/api/plugins/services/" \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "cdn",
    "service_id": "CDN-EDGE-301",
    "description": "CDN edge node, riding over L2L-10042",
    "status": "active",
    "bandwidth": 500,
    "cir": 250,
    "sla_uptime_percent": "99.90",
    "tenant": 3,
    "order_date": "2026-09-25",
    "installed": "2026-10-02",
    "contract_start": "2026-10-02",
    "contract_end": "2027-10-02"
  }'
```

Suppose this comes back as `id: 46`, and the L2L circuit it depends on (from the [L2VPN example](l2vpn.md)) is `id: 42`.

## 2. Attach the inventory

Open `/plugins/services/46/`:

1. **Virtual Machines** → Assign → the CDN edge VM, if it runs virtualized rather than on dedicated hardware.
2. **Devices** → Assign → the physical appliance, if it's dedicated hardware instead.
3. **Interfaces** → Assign → the uplink interface the edge node uses.

## 3. Record the dependency

This is the step that matters most for a CDN service: without it, deleting or disrupting the underlying L2L looks unrelated to the CDN node in NetBox, when in reality the CDN goes down the moment the circuit does.

On `/plugins/services/46/`, find the **Dependencies** card → **Assign** next to "Depends on" → select `L2L-10042` (service PK `42`).

```bash
# Equivalent isn't exposed via the API — depends_on is read-only there too,
# just like the other relation fields. Use the UI "Assign" button.
```

## Result

`CDN-EDGE-301` now shows `L2L-10042` under "Depends on", and `L2L-10042` shows `CDN-EDGE-301` under "Dependents". Running **Impact Search** (`/plugins/services/impact/`) on the L2L's device or interface will list `CDN-EDGE-301` under "Also affected" — exactly the chain you'd want to see before touching that circuit.
