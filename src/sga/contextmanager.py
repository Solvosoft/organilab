from sga.managers import OrganilabContextQueryset


class OrganilabContextManager():
    def __init__(self, contextname):
        self.contextname = contextname
        self.context=OrganilabContextQueryset.organilabContext

    def __enter__(self, *args, **kwargs):
        self.token = self.context.set(self.contextname)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.reset(self.token)