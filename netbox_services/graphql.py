import strawberry
import strawberry_django

from netbox.graphql.types import NetBoxObjectType

from . import models


@strawberry_django.type(
    models.Service,
    fields='__all__',
)
class ServiceType(NetBoxObjectType):
    pass


@strawberry.type(name="Query")
class ServicesQuery:
    service: ServiceType = strawberry_django.field()
    service_list: list[ServiceType] = strawberry_django.field()


schema = [
    ServicesQuery,
]
