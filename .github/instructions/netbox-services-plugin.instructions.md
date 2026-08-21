---
description: "Use when building, editing, debugging, or testing the NetBox Services plugin (netbox_services, netbox-services). Covers plugin-only code changes, Django runserver on port 8000, and migrations."
name: NetBox Services Plugin
applyTo:
  - "netbox/netbox-services/netbox_services/**"
  - "netbox_services/**"
---

# NetBox Services plugin work

This workspace includes core NetBox plus the **NetBox Services** plugin. When working on the plugin, follow these hard rules.

## Edit scope (hard rule)

- **Only modify code under** `netbox/netbox-services/netbox_services/`.
- Do **not** edit core NetBox, other plugins, configuration, docs, or files outside that directory unless the user explicitly asks.
- Prefer proposing plugin-local changes over touching NetBox internals.

## Django dev server (hard rule)

- **Keep the Django development server running on port 8000** for the duration of the work.
- If nothing is listening on port 8000, **start** `runserver` on 8000 (from `netbox/`, with the project venv) and leave it running.
- Do **not** stop, kill, or restart an already-running server on 8000 unless the user asks.
- If you need another process, use a different terminal; do not take over port 8000.

## Migrations (hard rule)

- You **may propose** creating migrations (`makemigrations` / `migrate`) after model changes.
- **Do not run** `makemigrations`, `migrate`, or otherwise apply migrations without asking first — even in autopilot / agent mode.
- Wait for explicit user approval before executing any migration command.
