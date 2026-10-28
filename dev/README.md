# Development environment

Two scripts that set up and run everything needed to develop a NetBox plugin,
from a fresh clone of the repository:

```
dev/run.sh      # NetBox with the plugin, on http://localhost:8000 (admin / admin)
dev/test.sh     # the plugin tests, fast
```

Only `dev/plugin.conf` is specific to this plugin: the rest is generic and can
be copied to another plugin (see [Using it in another plugin](#using-it-in-another-plugin)).

Requirements: Linux with apt or dnf, `sudo` (only to install missing packages),
Python 3.12 or newer and about 2 GB of disk. podman is installed if missing.

## dev/run.sh

```
dev/run.sh [--netbox DIR] [--reset] [--no-demo] [--no-server]
```

| Option | Effect |
| --- | --- |
| `--netbox DIR` | where NetBox is (or goes). Default: `$NETBOX_ROOT`, or `.netbox/` in the repository (git-ignored) |
| `--reset` | drop and recreate the dev database (only that one) |
| `--no-demo` | create the database empty instead of from the NetBox demo data (every migration runs: a few minutes) |
| `--no-server` | prepare everything and stop before starting the server |

It can be run as many times as wanted: each step is skipped when it is already
done (a second run takes about 15 seconds).

1. Installs podman, git, curl and the build packages with apt or dnf (asks for sudo).
2. Clones NetBox at the tag `NETBOX_REF` if `DIR` does not exist. An existing NetBox is used as it is.
3. Creates `<DIR>/venv` with NetBox's requirements, the plugin (editable, from the main checkout), podman-compose and tblib. It reinstalls only when those requirements change.
4. Starts postgres and two redis from `dev/compose.yml`, unless a compose project already runs those services. The ports are fixed: 5432, 6379 and 6380.
5. Creates the dev database from the [NetBox demo data](https://github.com/netbox-community/netbox-demo-data) of the NetBox version in use (downloaded once), migrates and makes sure the `admin` / `admin` user exists.
6. Starts the development server (`PORT`, default 8000).

The dev database is separate from any other one, so the plugin's migrations never
run against a database you care about.

## dev/test.sh

```
dev/test.sh [--netbox DIR] [--rebuild] [--own] [manage.py test arguments]
```

Runs the plugin tests (all without arguments, or the labels you pass) against a
copy of a migrated template database, instead of applying every NetBox migration
on each run (about 4 minutes). The template is built once from `TEMPLATE_REF`;
each run clones it and uses `--keepdb`, so Django only applies the migrations of
the checked out branch. It sets NetBox up like `run.sh` does if needed.

- `--rebuild` builds the template again (after merging a branch with migrations).
- `--own` runs only the hand-written tests (`OWN_TEST_PATTERNS`), a quick loop.
- `--parallel=4` is faster; a failing test then hides its error, so rerun it alone.
- Two runs at the same time share the test databases and break each other.

## Using it in another plugin

1. Copy the `dev/` folder into the plugin's repository and add `/.netbox/` to its `.gitignore`.
2. Edit `dev/plugin.conf`: the plugin's module, the dev database name, the NetBox tag, a quick test to build the template and, optionally, the `--own` patterns.
3. Run `dev/run.sh`.

The plugin must be installable with `pip install -e .` from the repository root.
Any value of `plugin.conf` can also be overridden from the environment
(`NETBOX_REF=v4.7.2 dev/run.sh`), and `DEMO_VERSION` forces another demo data version.

## Files

| File | What it is |
| --- | --- |
| `plugin.conf` | the plugin-specific settings |
| `lib.sh` | the setup steps shared by both scripts |
| `compose.yml` | postgres and redis for podman-compose |
| `configuration_dev.py` | NetBox configuration for `run.sh` (does not need the NetBox checkout's own `configuration.py`) |
| `configuration_test.py` | NetBox testing configuration plus the plugin, for `test.sh` |
