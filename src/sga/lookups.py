from ajax_select import register, LookupChannel
from django.db.models import Q

from sga.models import WarningWord, DangerIndication, PrudenceAdvice


@register('warningwords')
class TagsLookup(LookupChannel):
    model = WarningWord

    def check_auth(self, request):
        if request.user.is_authenticated():
            return True
        return False

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q).order_by('weigth')

    def format_item_display(self, item):
        return u"<span class='tag' data-pk=\"%s\"> %s</span>" % (item.pk, item.name)

@register('dangerindication')
class TagsLookup(LookupChannel):
    model = DangerIndication

    def check_auth(self, request):
        if request.user.is_authenticated():
            return True
        return False

    def get_query(self, q, request):
        return self.model.objects.filter(Q(description__icontains=q)|Q(code__icontains=q)).order_by('code')[:8]

    def format_item_display(self, item):
        texto = """
        <a class="tagcode btn btn-xs" id="%(code)s" title="%(code)s" data-ftype="itext">%(code)s</a>
        <a class='tag' id="%(code)s"  title="%(description)s" data-ftype="textbox"> %(description)s</a>
        """ % {'code': item.code, 'description': item.description}

        return texto


@register('prudenceadvices')
class TagsLookup(LookupChannel):
    model = PrudenceAdvice

    def check_auth(self, request):
        if request.user.is_authenticated():
            return True
        return False

    def get_query(self, q, request):

        return self.model.objects.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(
            prudence_advice_help__icontains=q)).order_by('code')[:8]

    def format_item_display(self, item):
        texto = """<a class="tagcode btn btn-xs" id="%(code)s" title="%(code)s" data-ftype="itext" >%(code)s</a>
        <a class='tag' id="%(code)s"  title="%(description)s" data-ftype="textbox"> %(description)s</a> """ % {
            'code': item.code, 'description': item.name}

        return texto

