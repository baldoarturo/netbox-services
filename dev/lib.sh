# shellcheck shell=bash
# Shared by dev/run.sh and dev/test.sh: finds NetBox and makes sure everything
# they need is there (system packages, NetBox, virtualenv, containers). Every
# step does nothing when it is already done, so the scripts can run as often as
# wanted, also on a fresh clone of the repository.
#
# Variables a script can set before calling dev_setup:
#   NETBOX_ROOT  where NetBox is (cloned there if missing). Default: .netbox/
#                in the main checkout of this repository.
# The plugin-specific values (module, database, NetBox tag...) come from
# dev/plugin.conf. Other overrides: DEMO_VERSION (demo data used for new
# databases; default: the one matching the NetBox in use).

DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# This checkout of the repository (a git worktree, maybe)
REPO_DIR="$(dirname "$DEV_DIR")"
# The main checkout of the repository: where the plugin is installed from and
# where .netbox/ lives, shared by all the worktrees
MAIN_DIR="$(cd "$(git -C "$DEV_DIR" rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"

source "$DEV_DIR/plugin.conf"
export PLUGIN_MODULE PLUGIN_DEV_DB
COMPOSE_PROJECT="$(echo "$PLUGIN_MODULE" | tr '_' '-')-dev"

say() { echo "==> $*"; }
die() { echo "error: $*" >&2; exit 1; }

# A usable NetBox directory path: --netbox DIR > $NETBOX_ROOT > .netbox/
dev_resolve_root() {
    NETBOX_ROOT="${NETBOX_ROOT:-$MAIN_DIR/.netbox}"
    case "$NETBOX_ROOT" in /*) ;; *) NETBOX_ROOT="$PWD/$NETBOX_ROOT" ;; esac
    VENV="$NETBOX_ROOT/venv"
    PYTHON="$VENV/bin/python"
}

# Newest Python NetBox supports (3.12+) found on the PATH
find_python() {
    local candidate
    for candidate in python3.14 python3.13 python3.12; do
        if command -v "$candidate" >/dev/null 2>&1; then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}

# Installs what is missing with the system package manager (sudo). The build
# packages are only needed to create the virtualenv.
ensure_system_deps() {
    local pybin="" py="" missing=() pkg
    if [ ! -x "$PYTHON" ]; then
        pybin="$(find_python)" || die "Python 3.12 or newer is required to create the virtualenv (python3.12, python3.13 or python3.14 not found in the PATH)"
        py="$(basename "$pybin")"
    fi
    if command -v apt-get >/dev/null 2>&1; then
        for pkg in git curl podman ${py:+build-essential "$py-dev" "$py-venv" libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev zlib1g-dev}; do
            dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
        done
        [ ${#missing[@]} -eq 0 ] && return 0
        say "Installing system packages with apt (needs sudo): ${missing[*]}"
        sudo apt-get update && sudo apt-get install -y "${missing[@]}"
    elif command -v dnf >/dev/null 2>&1; then
        for pkg in git curl podman ${py:+gcc "$py-devel" libxml2-devel libxslt-devel libffi-devel libpq-devel openssl-devel zlib-devel}; do
            rpm -q "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
        done
        [ ${#missing[@]} -eq 0 ] && return 0
        say "Installing system packages with dnf (needs sudo): ${missing[*]}"
        sudo dnf install -y "${missing[@]}"
    else
        for pkg in git curl podman; do
            command -v "$pkg" >/dev/null 2>&1 || die "$pkg is not installed and there is no apt or dnf to install it: install it by hand"
        done
    fi
}

ensure_netbox() {
    if [ -f "$NETBOX_ROOT/netbox/manage.py" ]; then
        local have
        have="$(git -C "$NETBOX_ROOT" describe --tags --always 2>/dev/null || echo unknown)"
        [ "$have" = "$NETBOX_REF" ] || echo "note: NetBox in $NETBOX_ROOT is at $have, the pinned version is $NETBOX_REF (left as is)" >&2
        return 0
    fi
    if [ -d "$NETBOX_ROOT" ] && [ -n "$(ls -A "$NETBOX_ROOT")" ]; then
        die "$NETBOX_ROOT exists but is not a NetBox checkout (no netbox/manage.py)"
    fi
    say "Cloning NetBox $NETBOX_REF into $NETBOX_ROOT"
    git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$NETBOX_REF" https://github.com/netbox-community/netbox.git "$NETBOX_ROOT"
}

# Virtualenv with NetBox's requirements, the plugin (editable, from the main
# checkout), podman-compose and tblib (so `--parallel` can report failures).
# Reinstalled only when those requirements change.
ensure_venv() {
    if [ ! -x "$PYTHON" ]; then
        say "Creating the virtualenv in $VENV"
        "$(find_python)" -m venv "$VENV"
    fi
    local extras="podman-compose tblib" stamp="$VENV/.dev-requirements" want
    want="$(cat "$NETBOX_ROOT/requirements.txt" "$MAIN_DIR/pyproject.toml" <(echo "$extras") | sha256sum | cut -d' ' -f1)"
    if [ "$(cat "$stamp" 2>/dev/null)" != "$want" ]; then
        say "Installing NetBox requirements and the plugin (a few minutes the first time)"
        "$PYTHON" -m pip install -q --disable-pip-version-check -r "$NETBOX_ROOT/requirements.txt"
        "$PYTHON" -m pip install -q --disable-pip-version-check -e "$MAIN_DIR" $extras
        echo "$want" > "$stamp"
    fi
}

# Starts postgres and redis unless they run already (from this repository or
# from any other compose project exposing the same services), then waits for
# postgres. Sets POSTGRES, the name of its container.
ensure_containers() {
    local service missing=""
    for service in postgres redis redis-cache; do
        [ -n "$(podman ps -q --filter "label=com.docker.compose.service=$service" 2>/dev/null)" ] || missing=1
    done
    if [ -n "$missing" ]; then
        say "Starting postgres and redis"
        local compose out
        compose="$(command -v podman-compose || echo "$VENV/bin/podman-compose")"
        out="$("$compose" -p "$COMPOSE_PROJECT" -f "$DEV_DIR/compose.yml" up -d 2>&1)" || die "podman-compose failed:
$out"
    fi
    POSTGRES="$(podman ps --filter "label=com.docker.compose.service=postgres" --format '{{.Names}}' 2>/dev/null | head -1)"
    [ -n "$POSTGRES" ] || die "the postgres container is not running"
    local _
    for _ in $(seq 1 60); do
        podman exec "$POSTGRES" pg_isready -q -U netbox >/dev/null 2>&1 && return 0
        sleep 1
    done
    die "postgres ($POSTGRES) does not accept connections"
}

dev_setup() {
    dev_resolve_root
    ensure_system_deps
    ensure_netbox
    ensure_venv
    ensure_containers
}

# NetBox demo data (SQL dump) matching the NetBox in use (4.7.3 -> v4.7),
# downloaded the first time a database needs it. Sets DEMO_VERSION and DEMO_SQL.
demo_sql() {
    local version="${DEMO_VERSION:-}"
    if [ -z "$version" ]; then
        version="$(sed -n 's/^version: *"\{0,1\}\([0-9]*\.[0-9]*\).*/v\1/p' "$NETBOX_ROOT/netbox/release.yaml" | head -1)"
        [ -n "$version" ] || die "could not tell the NetBox version from $NETBOX_ROOT/netbox/release.yaml: set DEMO_VERSION (e.g. v4.7)"
    fi
    DEMO_VERSION="$version"
    local sql="$NETBOX_ROOT/netbox-demo-$version.sql"
    if [ ! -f "$sql" ]; then
        say "Downloading the NetBox demo data $version"
        curl -fsSL -o "$sql.part" "https://github.com/netbox-community/netbox-demo-data/raw/refs/heads/master/sql/netbox-demo-$version.sql" \
            || { rm -f "$sql.part"; die "could not download the demo data $version: set DEMO_VERSION to one that exists in netbox-community/netbox-demo-data"; }
        mv "$sql.part" "$sql"
    fi
    DEMO_SQL="$sql"
}
