# IP Transit: wholesale internet transit

**Scenario:** you're providing full-table BGP internet transit to a downstream ISP or large enterprise with their own ASN — different from DIA, where the customer usually doesn't run BGP.

## 1. Create the service

```bash
curl -s -X POST "$NETBOX_URL/api/plugins/services/" \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "transit",
    "service_id": "TRANSIT-7701",
    "description": "IP Transit for downstream ISP",
    "status": "active",
    "bandwidth": 10000,
    "cir": 5000,
    "sla_uptime_percent": "99.95",
    "tenant": 8,
    "order_date": "2026-05-01",
    "installed": "2026-05-15",
    "contract_start": "2026-05-15",
    "contract_end": "2027-05-15"
  }'
```

A 10 Gbps port with a 5 Gbps CIR (burstable above commit) is typical for a transit customer that pays for guaranteed capacity but occasionally exceeds it. Say this returns `id: 45`.

## 2. Attach the inventory

Open `/plugins/services/45/`:

1. **Devices** → Assign → your border router peering with the customer.
2. **Interfaces** → Assign → the peering interface (often a 10G/100G port, possibly a LAG — assign the physical member interfaces or the LAG interface depending on how you model it).
3. **ASNs** → Assign → the customer's ASN (the one you're accepting routes from and announcing the full table to).
4. **Prefixes** → Assign → any address space you've allocated to them as part of the transit agreement (not always applicable if they bring their own).
5. **Route Targets** → Assign → only if this transit is delivered inside a VRF (some providers isolate wholesale transit customers this way); leave empty for a plain global-table peering.

## Result

The service record becomes the audit trail for "who do we peer with, on what port, at what commit rate" — useful when a peering session flaps and you need to know immediately which customer and which SLA is affected, without grepping router configs.
