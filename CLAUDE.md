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

## Auth for manual testing

- Use `admin` / `admin` when logging in to check something manually in the browser.

## Release workflow (hard rule)

- Every version bump in `pyproject.toml` that adds features must update `README.md` in the same change (feature list and/or the "What a Service is" table). Pure `chore`/`fix` bumps with no user-facing feature don't need it.
- Before tagging a release, check the commit log since the last tag for `feat:` commits — if any exist, the README update is mandatory, not optional.
- A version bump always gets a matching git tag (`vX.Y.Z`) on the commit that contains both the `pyproject.toml` bump and the README update (if any), so the tag's `pyproject.toml` version always matches the tag name — the `python-publish.yml` workflow checks this and fails otherwise.

## NetBox core repo (hard rule)

- Never commit anything to the NetBox core repo (the parent `netbox/` checkout one level up from this plugin). It always tracks upstream `netbox-community/netbox` as-is — no local commits, ever.
- Local-only dev tooling for the core repo (`setup-dev.sh`, `compose.yml`, `scripts/*_database.sh`, `netbox/netbox/configuration.py`, `netbox/netbox/configuration_testing.py`) lives there but is gitignored/untracked on purpose. Edit it freely to make the dev environment work, but never try to commit it.
- If `manage.py test netbox_services` needs `netbox_services` added to `configuration_testing.py`'s `PLUGINS`, patch that file locally (or have `setup-dev.sh` do it) — don't ask the user to do it, and don't commit it.

## Dev environment setup (`setup-dev.sh`, one level up from this plugin)

- Must stay idempotent: safe to re-run with containers/venv already up, must tear down and recreate the test DB on every demo-data load (don't assume a clean DB).
- Must support bringing up the environment at an arbitrary NetBox version via `--netbox-version <tag>` (does a `git fetch --tags` + `git checkout` in the core repo) and an arbitrary demo-data version via `--demo-version <version>`. This is so any dev can reproduce an environment against any NetBox release, not just whatever is currently checked out.
- Database and Redis run in podman containers (`compose.yml`, one level up); NetBox itself runs natively in a venv on the host — the user explicitly rejected running NetBox itself in a container. Don't reintroduce a NetBox container.
- Postgres container password and `configuration.py`/`configuration_testing.py` DB credentials must stay in sync (`netbox`/`netbox`) — a mismatch here is a common source of "it works for dev but tests can't connect" bugs.
- Different NetBox versions can require different minimum Python versions (check `requires-python` in the checked-out `pyproject.toml`); the script must pick/recreate the venv's Python version accordingly instead of assuming whatever `python3` resolves to on the host.

## Git/push workflow (hard rule)

- Claude's shell in this environment has no GitHub credentials — `git push` here always fails with "could not read Username for 'https://github.com'". Never spend time trying to find or configure credentials for this; just commit locally and tell the user the exact `git push` command to run themselves.
