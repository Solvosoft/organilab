# encoding: utf-8
"""Conceder y quitar capacidades por el camino real de organilab.

En organilab los permisos efectivos **no salen de ``user.user_permissions``**:
los inyecta ``ProfileMiddleware`` (``authentication/middleware.py:95-159``)
uniendo tres fuentes — los ``Rol`` que el perfil tiene en ese ámbito, los
permisos directos del usuario y los de sus grupos — en ``user._perm_cache``.

Una prueba que sólo toque ``user_permissions`` miente en las dos direcciones:
concede donde el middleware no concedería y niega donde sí.  Este módulo es la
única forma en que la suite del labview manipula permisos.

Dos advertencias que condicionan el diseño y que cuestan caro descubrir tarde:

* **El middleware se salta a los superusuarios** (``middleware.py:50``), y
  ``has_perm`` cortocircuita antes de mirar backends.  Con un superusuario,
  cualquier prueba de permisos pasa sin probar nada.
* **El ámbito por perfil concede en todas las organizaciones**: el ``queryQ``
  del middleware incluye siempre la rama ``object_id=profile.pk``.  Por eso el
  ámbito por defecto aquí es el **laboratorio**, cuya rama es literal
  (``object_id == lab_pk``) y es la única que permite probar aislamiento entre
  inquilinos.
"""

import hashlib

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from auth_and_perms.models import ProfilePermission, Rol


def resolve_permissions(codenames):
    """``["laboratory.add_shelf", "view_furniture"]`` -> queryset de Permission.

    Acepta la forma con app y sin ella.  La forma con app importa: hay
    codenames repetidos entre aplicaciones (``add_recipientsize`` de sga y los
    de laboratory conviven), y filtrar sólo por codename concede de más.
    """
    permissions = []
    for codename in codenames:
        if "." in codename:
            app_label, name = codename.split(".", 1)
            found = Permission.objects.filter(
                content_type__app_label=app_label, codename=name
            )
        else:
            found = Permission.objects.filter(codename=codename)
        if not found:
            raise LookupError("No existe el permiso %r" % codename)
        permissions.extend(found)
    return permissions


class RolPermissionMixin:
    """Capacidades por ``Rol`` -> ``ProfilePermission`` -> ``ProfileMiddleware``."""

    def reload_user(self, user):
        """Re-lee el usuario y rehace el login.

        ``has_perm`` cachea en ``_perm_cache`` sobre la instancia: sin releer,
        una concesión posterior no se ve y la prueba pasa por la razón
        equivocada.
        """
        user = type(user).objects.get(pk=user.pk)
        client = getattr(self, "client", None)
        if client is not None:
            client.force_login(user)
        return user

    def strip_effective_permissions(self, user):
        """Deja al usuario sin ninguna capacidad efectiva.

        Desata los ``Rol`` **del perfil** en vez de vaciar ``Rol.permissions``,
        que es un catálogo compartido: vaciarlo dejaría también sin permisos al
        otro inquilino de la misma prueba.
        """
        user.user_permissions.clear()
        user.groups.clear()
        for profile_permission in ProfilePermission.objects.filter(
            profile=user.profile
        ):
            profile_permission.rol.clear()
        return self.reload_user(user)

    def grant(self, user, codenames, scope=None):
        """Concede esas capacidades en ese ámbito (por defecto, ``self.lab``)."""
        scope = scope if scope is not None else self.lab
        permissions = resolve_permissions(codenames)
        # ``Rol.name`` son 100 caracteres y un conjunto de 23 capacidades no
        # cabe: el nombre es un resumen estable del conjunto, de modo que el
        # mismo conjunto reutiliza su Rol en vez de crear una fila por vuelta.
        digest = hashlib.sha1(
            ",".join(sorted(codenames)).encode("utf-8")
        ).hexdigest()[:12]
        rol, _created = Rol.objects.get_or_create(name="test:%s" % digest)
        rol.permissions.set(permissions)

        content_type = ContentType.objects.get_for_model(scope)
        profile_permission, _created = ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=content_type,
            object_id=scope.pk,
        )
        profile_permission.rol.add(rol)
        return self.reload_user(user)

    def set_capabilities(self, user, codenames, scope=None):
        """El estado exacto: primero a cero, luego sólo esas capacidades."""
        user = self.strip_effective_permissions(user)
        if codenames:
            user = self.grant(user, codenames, scope=scope)
        return user
