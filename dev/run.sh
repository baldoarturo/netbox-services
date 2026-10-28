#!/bin/bash
set -euo pipefail

# Usage: dev/run.sh [--netbox DIR] [--reset] [--no-demo] [--no-server]
#   --netbox DIR  where NetBox is (default: $NETBOX_ROOT, or .netbox/ inside this
#                 repository); cloned there at a pinned tag if it does not exist
#   --reset       drop and recreate the dev database (never any other)
#   --no-demo     create the database empty (every migration runs, a few minutes)
#                 instead of from the NetBox demo data
#   --no-server   prepare everything but do not start the server
#
# Runs NetBox with this plugin against its own database ($PLUGIN_DEV_DB). It takes
# care of everything it needs, so it works on a fresh clone of the repository,
# and it can be run as many times as wanted (every step is skipped when it is
# already done):
#   1. installs podman and the build packages with apt or dnf (sudo) if missing
#   2. clones NetBox (tag $NETBOX_REF) if DIR does not exist
#   3. creates the virtualenv there, with NetBox's requirements, this plugin
#      (editable, from the main checkout) and podman-compose
#   4. starts postgres and redis from dev/compose.yml if they are not running
#   5. creates the database from the NetBox demo data (the version matching
#      NetBox, downloaded) if it is missing;
#      --reset drops it first
#   6. migrates, makes sure an admin/admin user exists and starts the server
#
# The plugin-specific settings are in dev/plugin.conf. Environment: NETBOX_ROOT
# (same as --netbox), PORT (default: 8000), DEMO_VERSION, and the values of
# plugin.conf (PLUGIN_DEV_DB, NETBOX_REF...).

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

RESET=""
DEMO=1
SERVER=1
while [ $# -gt 0 ]; do
    case "$1" in
        --reset) RESET=1 ;;
        --no-demo) DEMO="" ;;
        --no-server) SERVER="" ;;
        --netbox) [ $# -ge 2 ] || die "--netbox needs a directory"; NETBOX_ROOT="$2"; shift ;;
        --netbox=*) NETBOX_ROOT="${1#--netbox=}" ;;
        *) die "unknown argument: $1" ;;
    esac
    shift
done

DEV_DB="$PLUGIN_DEV_DB"
PORT="${PORT:-8000}"

dev_setup
psql_() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 "$@"; }

if [ -n "$RESET" ]; then
    say "Dropping $DEV_DB"
    psql_ -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DEV_DB' AND pid <> pg_backend_pid()" >/dev/null
    psql_ -c "DROP DATABASE IF EXISTS \"$DEV_DB\""
fi

if [ "$(psql_ -Atc "SELECT count(*) FROM pg_database WHERE datname = '$DEV_DB'")" = 0 ]; then
    if [ -n "$DEMO" ]; then
        demo_sql
        say "Loading the demo data $DEMO_VERSION into $DEV_DB"
    fi
    psql_ -c "CREATE DATABASE \"$DEV_DB\""
    if [ -n "$DEMO" ]; then
        # Two fixes to the dump: it is owned by the postgres role, which this container
        # does not have, and it empties the search_path, so the ltree operators used
        # by its triggers cannot be found
        grep -v '^\\restrict\|^\\unrestrict' "$DEMO_SQL" \
            | sed "s/OWNER TO postgres;/OWNER TO netbox;/; s/set_config('search_path', '', false)/set_config('search_path', 'public', false)/" \
            | podman exec -i "$POSTGRES" psql -U netbox -d "$DEV_DB" -v ON_ERROR_STOP=1 >/dev/null \
            || { psql_ -c "DROP DATABASE \"$DEV_DB\"" >/dev/null; die "loading the demo data failed (the incomplete database was dropped)"; }
    else
        say "Created $DEV_DB empty"
    fi
fi

export PYTHONPATH="$DEV_DIR${PYTHONPATH:+:$PYTHONPATH}"
export NETBOX_CONFIGURATION=configuration_dev
cd "$NETBOX_ROOT/netbox"

say "Migrating $DEV_DB"
"$PYTHON" manage.py migrate

say "Ensuring a superuser exists (admin/admin)"
"$PYTHON" manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('created admin/admin')
else:
    print('admin already exists')
"

if [ -n "$SERVER" ]; then
    say "NetBox on http://localhost:$PORT (database: $DEV_DB)"
    exec "$PYTHON" manage.py runserver "0.0.0.0:$PORT"
fi
