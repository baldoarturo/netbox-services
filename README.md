# NetBox Services Plugin

This plugin extends NetBox to manage and relate business services to network resources. It introduces a `Service` model that allows you to track various service types (such as L2VPN, L3VPN, DIA, Transit, CDN, Voice) and associate them with devices, interfaces, cables, VLANs, prefixes, VRFs, ASNs, route targets, L2VPNs, tunnels, and virtual machines.

## Features
- Add, edit, and delete business services.
- Relate services to network objects (devices, interfaces, cables, VLANs, prefixes, VRFs, ASNs, route targets, L2VPNs, tunnels, virtual machines).
- Filter and view services in a table with all relevant fields.
- Custom forms and views for relating specific network objects to a service.
- Integrated navigation and changelog support.

## Usage
- Access the plugin from the NetBox navigation menu under "Business Services".
- Create new services and relate them to network resources.
- Use the detail view to see all associations for a service.

![alt text](https://github.com/baldoarturo/netbox-services/raw/master/02-main.png)

## Why
Because you might be looking for such a thing. 

Tagging is great for simple categorization, but the NetBox Services plugin goes far beyond that by letting you model real business services and their relationships to network resources.

Instead of just tagging a device or prefix as "DIA," you can create a full DIA service—like "NW-123456" from Cogent—and link it to all relevant devices, interfaces, prefixes, VRFs, ASNs, and more.

For example, with a DIA service from Cogent (Service ID: NW-123456), you can:

- See all devices and interfaces delivering that service.
- Track the exact IP prefixes, VRFs, and ASNs involved.
- Relate cables, tunnels, and even virtual machines to the service.
- View and manage all these relationships in one place, with history and forms tailored to each resource.

This gives you a true service-centric view of your network, making troubleshooting, reporting, and change management much more powerful and organized than simple tagging ever could.

## Requirements
- NetBox 4.x or later
- Django 4.x or later

## Installation
1. Clone this repository into your NetBox `plugins` directory. You can also install it on your system / venv / coffee maker with
```bash
pip install netbox_services
```

2. Add `'netbox_services'` to the `PLUGINS` list in your NetBox configuration.

```python
    PLUGINS = [
        'netbox_services'
    ],
```

3. Run migrations: `python manage.py migrate netbox_services`
4. Restart NetBox.

## License
MIT
