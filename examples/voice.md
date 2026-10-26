# Voice: hosted voice trunk

**Scenario:** a SIP trunk or hosted PBX voice service for a customer — typically needs a tunnel or dedicated VLAN for QoS, and a tighter SLA than best-effort data since dropped calls are immediately noticed.

## 1. Create the service

```bash
curl -s -X POST "$NETBOX_URL/api/plugins/services/" \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "voice",
    "service_id": "VOICE-TRUNK-88",
    "description": "SIP trunk, 20 concurrent calls",
    "status": "active",
    "bandwidth": 10,
    "cir": 10,
    "sla_uptime_percent": "99.99",
    "tenant": 3,
    "order_date": "2026-10-01",
    "installed": "2026-10-10",
    "contract_start": "2026-10-10",
    "contract_end": "2027-10-10"
  }'
```

10 Mbps is plenty for 20 concurrent G.711 calls with headroom; CIR equal to bandwidth reflects that voice traffic generally shouldn't be the thing that gets dropped under congestion. Say this returns `id: 47`.

## 2. Attach the inventory

Open `/plugins/services/47/`:

1. **Devices** → Assign → the session border controller (SBC) or voice gateway handling the trunk.
2. **Interfaces** → Assign → the SBC's interface facing the customer.
3. **VLANs** → Assign → the voice VLAN, if the trunk is delivered over a tagged LAN segment (common when the circuit underneath is already shared with data).
4. **Tunnels** → Assign → if the trunk runs over an IPsec or GRE tunnel rather than a dedicated circuit.
5. **IP Addresses** → Assign → the SIP signaling IP(s) used for the trunk.

If this voice trunk rides over a circuit this plugin already tracks (e.g. the same L2L used for data), record that under **Dependencies** → **Assign**, the same way as the [CDN example](cdn.md).

## Result

`VOICE-TRUNK-88` ties the SBC, the voice VLAN or tunnel, and the SIP signaling address together — so when someone reports "calls are dropping," you can check this one service record instead of separately checking the SBC, the VLAN, and the tunnel state by hand.
