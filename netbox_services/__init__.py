from importlib.metadata import metadata

from netbox.plugins import PluginConfig

plugin = metadata('netbox_services')


class Services(PluginConfig):
    name = plugin.get('Name').replace('-', '_')
    verbose_name = plugin.get('Name').replace('-', ' ').title()
    description = plugin.get('Summary')
    version = plugin.get('Version')
    author = 'Arturo Baldo'
    author_email = 'baldoarturo@gmail.com'
    base_url = 'services'
    min_version = '4.4.0'


config = Services
