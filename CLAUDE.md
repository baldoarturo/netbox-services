# NetBox Services plugin

## Dev server (hard rule)

- Keep the Django dev server running on port 8000 for the duration of the work: `cd netbox/ && python manage.py runserver 0.0.0.0:8000` (venv active, `NETBOX_CONFIGURATION` set).
- If nothing is listening on port 8000, start it in the background and leave it running.
- Do not stop, kill, or restart an already-running server on 8000 unless the user asks.

## Verify after every change (hard rule)

- After any code change in this plugin, confirm the app still runs: check the server process is up, hit the plugin's UI page (`/plugins/services/`) and/or run relevant tests.
- If the server errored out or the page 500s, treat that as a regression to fix before considering the change done — don't just report the edit as complete.

## Migrations

- May propose `makemigrations`/`migrate` after model changes, but do not run them without explicit user approval.

## Edit scope

- Prefer changes scoped to `netbox_services/`; avoid touching core NetBox unless explicitly asked.
