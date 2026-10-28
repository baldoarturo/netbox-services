# NetBox Services plugin

## Dev server (hard rule)

- Keep the dev server running on port 8000 for the duration of the work: `dev/run.sh` (from the repo root). It sets up everything from scratch on a fresh clone and is safe to re-run (each step is skipped once done).
- If nothing is listening on port 8000, start it in the background and leave it running.
- Do not stop, kill, or restart an already-running server on 8000 unless the user asks. Use `dev/run.sh --reset` only when asked to rebuild the dev database.

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

- Never commit anything to the NetBox core repo. This plugin no longer depends on one living at a fixed relative path — `dev/run.sh` clones its own disposable NetBox checkout into `.netbox/` (gitignored) and is self-contained.

## Dev environment setup (`dev/`, standardized across plugins — see `dev/README.md`)

- `dev/run.sh` — sets up and runs NetBox with this plugin against its own database (`netbox_services_dev`), from a fresh clone. Idempotent: safe to re-run, each step skipped once done.
- `dev/test.sh` — runs the plugin's tests fast, against a migrated-schema template database built once from `origin/master`.
- The only plugin-specific file is `dev/plugin.conf` (`PLUGIN_MODULE`, `PLUGIN_DEV_DB`, `NETBOX_REF` — kept in sync with `NETBOX_VERSION` in `.github/workflows/test.yml`, currently `v4.7.3`). The rest of `dev/` is generic and shared verbatim with other plugins in this workspace (e.g. `netbox-routing`) — don't fork plugin-specific logic into `lib.sh`/`run.sh`/`test.sh`; it belongs in `plugin.conf` or stays generic.
- NetBox itself runs natively in a venv (`.netbox/venv`, created by `dev/run.sh`); only Postgres/Redis run in podman containers (`dev/compose.yml`). Don't reintroduce a NetBox container.
- `dev/run.sh --netbox DIR` points at an existing NetBox checkout instead of the default `.netbox/`; `--reset` rebuilds just the dev database; `--no-demo` skips seeding from NetBox demo data.

## Git/push workflow

- This sandbox has a working SSH key for GitHub. If a remote is set to HTTPS and `git push` fails with "could not read Username for 'https://github.com'", switch it to SSH first (`git remote set-url <remote> git@github.com:<owner>/<repo>.git`) rather than handing the push off to the user.
