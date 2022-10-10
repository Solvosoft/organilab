from contextvars import ContextVar
from django.db import models



class OrganilabContextQueryset(models.QuerySet):
    organilabContext = ContextVar('organilabcontext', default=None)

    def _chain(self, **kwargs):
        obj = super()._chain(**kwargs)
        orgcontext = self.organilabContext.get(None)
        if orgcontext:
            obj._filter_or_exclude_inplace(False, [],
                                       {"organilab_context": orgcontext})
        return obj

    def exists(self, noref=False):
        orgcontext = self.organilabContext.get(None)
        if orgcontext:
            self._filter_or_exclude_inplace(False, [],
                                       {"organilab_context": orgcontext})
        return super().exists()

    def create(self, **kwargs):
        orgcontext = self.organilabContext.get(None)
        if orgcontext:
            if 'organilab_context' not in kwargs:
                kwargs['organilab_context'] = orgcontext
        return super(OrganilabContextQueryset, self).create(**kwargs)

    def all(self):
        response = super(OrganilabContextQueryset, self).all()
        orgcontext = self.organilabContext.get(None)
        if orgcontext:
            response = response.filter(organilab_context=orgcontext)
        return response


    def as_manager(cls):
        # Address the circular dependency between `Queryset` and `Manager`.
        from django.db.models.manager import Manager
        manager = Manager.from_queryset(cls)()
        manager._built_with_as_manager = True
        def newall():
            return manager.get_queryset().all()

        manager.all = newall
        return manager
    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)


"""  
    def get_or_create(self, defaults=None, **kwargs):
        return super().get_or_create(defaults, **kwargs)
    def update_or_create(self, defaults=None, **kwargs):
        return super().update_or_create(defaults, **kwargs)
    def update(self, **kwargs):
        return super().update(**kwargs)
    def filter(self, *args, **kwargs):
        return super(OrganilabContextQueryset, self).filter(*args, **kwargs)
    def all(self):
        response= super(OrganilabContextQueryset, self).all()
        orgcontext = self.organilabContext.get(None)
        if orgcontext:
            response = response.filter(organilab_context=orgcontext)
        return response
"""