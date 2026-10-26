from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from utilities.exceptions import AbortRequest

from .models import Service


def _has_path(start, target, visited=None):
    """Depth-first search: can `target` be reached by following depends_on from `start`?"""
    if visited is None:
        visited = set()
    if start.pk in visited:
        return False
    visited.add(start.pk)
    for dependency in start.depends_on.all():
        if dependency.pk == target.pk or _has_path(dependency, target, visited):
            return True
    return False


@receiver(m2m_changed, sender=Service.depends_on.through)
def validate_no_dependency_cycle(sender, instance, action, pk_set, **kwargs):
    """Reject self-dependencies and any depends_on addition that would create a dependency cycle."""
    if action != 'pre_add' or not pk_set:
        return
    for pk in pk_set:
        if pk == instance.pk:
            raise AbortRequest('A service cannot depend on itself.')
        dependency = Service.objects.get(pk=pk)
        if _has_path(dependency, instance):
            raise AbortRequest(
                f'Adding "{dependency}" as a dependency of "{instance}" would create a '
                f'circular dependency.'
            )
