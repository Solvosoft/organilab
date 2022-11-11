from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups
from laboratory.models import Object
from auth_and_perms.models import Rol
from django.contrib.auth.models import User

@register_lookups(prefix="rol", basename="rolsearch")
class RolGModelLookup(BaseSelect2View):
    model = Rol
    fields = ['name']

@register_lookups(prefix="object", basename="objectsearch")
class ObjectGModelLookup(BaseSelect2View):
    model = Object
    fields = ['code', 'name']


@register_lookups(prefix="userbase", basename="userbase")
class User(BaseSelect2View):
    model = User
    fields = ['username']



