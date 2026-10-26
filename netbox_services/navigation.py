from netbox.plugins import PluginMenu
from netbox.plugins import PluginMenuItem, PluginMenuButton

services = PluginMenuItem(
    auth_required=True,
    link='plugins:netbox_services:service_list',
    link_text='Business Services',
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_services:service_add',
            title='Add',
            icon_class='mdi mdi-plus',
        ),
    )
)

impact_search = PluginMenuItem(
    auth_required=True,
    link='plugins:netbox_services:impact_search',
    link_text='Impact Search',
)

contracts = PluginMenuItem(
    auth_required=True,
    link='plugins:netbox_services:contracts',
    link_text='Contracts',
)


menu = PluginMenu(
    label='Business Services',
    groups=(
        ('Services', (services, impact_search, contracts)),
    ),
    icon_class='mdi mdi-receipt-text-arrow-right'
)
