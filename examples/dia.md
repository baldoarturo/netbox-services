# DIA: dedicated internet access

**Scenario:** a dedicated internet circuit for a single customer site — the classic example used elsewhere in this plugin's docs, e.g. circuit `NW-123456`.

## 1. Create the service

```bash
curl -s -X POST "$NETBOX_URL/api/plugins/services/" \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "dia",
    "service_id": "NW-123456",
    "description": "DIA for customer HQ",
    "status": "active",
    "bandwidth": 500,
    "cir": 500,
    "sla_uptime_percent": "99.90",
    "tenant": 5,
    "order_date": "2026-06-10",
    "planned_activation": "2026-06-24",
    "installed": "2026-06-22",
    "contract_start": "2026-06-22",
    "contract_end": "2027-06-22"
  }'
```

CIR equal to bandwidth here means the full circuit is committed — no oversubscription. If you response comes back as `id: 44`, continue below.

## 2. Attach the inventory

Open `/plugins/services/44/`:

1. **Devices** → Assign → the PE router handing off the circuit, and the customer's CE router if you model it in NetBox.
2. **Interfaces** → Assign → the exact handoff interface on the PE.
3. **Cables/XConnects** → Assign → the physical cross-connect, if tracked.
4. **Prefixes** → Assign → the WAN prefix used on the handoff (often a small point-to-point block, e.g. a /30 or /31).
5. **IP Addresses** → Assign → the specific IP(s) assigned to the customer within that prefix.
6. **ASNs** → Assign → the customer's ASN, if this is a BGP-peered DIA rather than a static route.

## 3. Attach the contract

If you have a signed service order or contract PDF, open **Attachments** → **Add**, upload the file, and give it a name. It'll sit alongside the lifecycle dates rather than in a separate document system.

## Result

Anyone looking at `NW-123456` sees the PE/CE devices and handoff interface, the WAN addressing, the contract paperwork, and the full order-to-decommission timeline in one page — the exact "what does this product actually run on?" answer this plugin exists for.
