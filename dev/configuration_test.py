"""
NetBox configuration to run the plugin tests: NetBox's testing configuration
with the plugin enabled. Used through NETBOX_CONFIGURATION=configuration_test,
see dev/test.sh, which sets PLUGIN_MODULE from dev/plugin.conf.
"""

import os

from netbox.configuration_testing import *  # noqa: F401,F403
from netbox.configuration_testing import PLUGINS

PLUGINS = [*PLUGINS, os.environ['PLUGIN_MODULE']]
DEVELOPER = True
