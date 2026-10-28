#!/bin/bash
set -euo pipefail

# Usage: dev/test.sh [--netbox DIR] [--rebuild] [--own] [manage.py test arguments]
#   --netbox DIR  where NetBox is (default: $NETBOX_ROOT, or .netbox/ inside this
#                 repository); set up like dev/run.sh does if it is not there
#   --rebuild  build the template database again
#   --own      only the tests written by hand (models, forms, filters, migrations,
#              validation rules), not the ones inherited from NetBox's CRUD test
#              classes for the API and the GUI: a quick loop while developing
#
# Runs the plugin tests (all of them without arguments) against a copy of a
# template database that is already migrated, instead of applying every NetBox
# migration on each run, which takes about 4 minutes. The template is built once
# from $TEMPLATE_REF; each run clones it (under a second) and uses --keepdb, so
# Django only applies the migrations the checked out branch adds.
#
# Examples:
#   dev/test.sh
#   dev/test.sh <module>.tests.some_package
#   dev/test.sh --parallel=4          (a failing test then hides its error: rerun it alone)
#
# The plugin-specific settings are in dev/plugin.conf. Environment: NETBOX_ROOT
# (same as --netbox).

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

REBUILD=""
OWN=""
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --rebuild) REBUILD=1 ;;
        --own) OWN=1 ;;
        --netbox) [ $# -ge 2 ] || die "--netbox needs a directory"; NETBOX_ROOT="$2"; shift ;;
        --netbox=*) NETBOX_ROOT="${1#--netbox=}" ;;
        *) ARGS+=("$1") ;;
    esac
    shift
done
# Without a test label Django would discover every test under the current
# directory, NetBox's own included: default to the plugin's
HAS_LABEL=""
for arg in "${ARGS[@]+"${ARGS[@]}"}"; do
    case "$arg" in -*|[0-9]*) ;; *) HAS_LABEL=1 ;; esac
done
[ -n "$HAS_LABEL" ] || ARGS+=("$PLUGIN_MODULE")
if [ -n "$OWN" ]; then
    [ -n "$OWN_TEST_PATTERNS" ] || die "--own needs OWN_TEST_PATTERNS in dev/plugin.conf"
    # test ids contain the module and the class: select the hand-written ones
    for pattern in $OWN_TEST_PATTERNS; do
        ARGS+=(-k "$pattern")
    done
fi

TEST_DB="test_netbox"
TEMPLATE_DB="test_netbox_base"

dev_setup
psql_() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 -q "$@" 2>&1 | grep -v 'level=warning' || true; }
psql_q() { podman exec -i "$POSTGRES" psql -U netbox -d postgres -v ON_ERROR_STOP=1 -Atq "$@" 2>/dev/null; }
exists() { [ "$(psql_q -c "SELECT count(*) FROM pg_database WHERE datname = '$1'")" = 1 ]; }
drop_db() {
    psql_q -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$1' AND pid <> pg_backend_pid()" >/dev/null
    psql_q -c "DROP DATABASE IF EXISTS \"$1\"" >/dev/null
}
drop_test_databases() {
    # the test database and the clones of an earlier parallel run
    for db in $(psql_q -c "SELECT datname FROM pg_database WHERE datname ~ '^${TEST_DB}(_[0-9]+)?\$'"); do
        drop_db "$db"
    done
}

run_tests() { # $1: source directory of the plugin, rest: manage.py test arguments
    local source="$1"; shift
    (cd "$NETBOX_ROOT/netbox" && \
        PYTHONPATH="$source:$DEV_DIR" NETBOX_CONFIGURATION=configuration_test PLUGIN_MODULE="$PLUGIN_MODULE" \
        "$PYTHON" manage.py test "$@")
}

build_template() {
    echo "==> Building the template database from $TEMPLATE_REF (once, about 5 minutes)"
    local source="$MAIN_DIR" tmp=""
    if git -C "$MAIN_DIR" fetch -q "${TEMPLATE_REF%%/*}" "${TEMPLATE_REF#*/}" 2>/dev/null; then
        tmp="$(mktemp -d)"
        if git -C "$MAIN_DIR" worktree add -q --detach "$tmp/main" "$TEMPLATE_REF" 2>/dev/null; then
            source="$tmp/main"
        fi
    fi
    drop_test_databases
    drop_db "$TEMPLATE_DB"
    # creates and migrates the test database, then keeps it
    run_tests "$source" "$TEMPLATE_TEST" --noinput --keepdb
    drop_db "$TEMPLATE_DB"
    psql_q -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TEST_DB' AND pid <> pg_backend_pid()" >/dev/null
    psql_q -c "CREATE DATABASE \"$TEMPLATE_DB\" TEMPLATE \"$TEST_DB\"" >/dev/null
    if [ -n "$tmp" ]; then
        git -C "$MAIN_DIR" worktree remove --force "$tmp/main" 2>/dev/null || true
        rm -rf "$tmp"
    fi
}

if [ -n "$REBUILD" ] || ! exists "$TEMPLATE_DB"; then
    build_template
else
    # The template must not hold migrations this checkout does not have
    missing=""
    for name in $(podman exec -i "$POSTGRES" psql -U netbox -d "$TEMPLATE_DB" -Atq -c "SELECT name FROM django_migrations WHERE app = '$PLUGIN_MODULE'" 2>/dev/null); do
        [ -e "$REPO_DIR/$PLUGIN_MODULE/migrations/$name.py" ] || missing="$missing $name"
    done
    if [ -n "$missing" ]; then
        echo "warning: the template has migrations this checkout lacks:$missing" >&2
        echo "         merge main into the branch, or run dev/test.sh --rebuild" >&2
    fi
fi

echo "==> Cloning $TEMPLATE_DB into $TEST_DB"
drop_test_databases
psql_q -c "CREATE DATABASE \"$TEST_DB\" TEMPLATE \"$TEMPLATE_DB\"" >/dev/null

run_tests "$REPO_DIR" "${ARGS[@]}" --noinput --keepdb
