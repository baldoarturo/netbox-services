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


menu = PluginMenu(
    label='Business Services',
    groups=(
        ('Services', (services,)),
    ),
    icon_class='mdi mdi-receipt-text-arrow-right'
)
