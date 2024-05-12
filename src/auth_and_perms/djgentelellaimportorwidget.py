from django.urls import reverse


class ImpostorWidget:
    def __init__(self, context):
        self.context = context

    def render(self):
        return ""

    def render_js(self):
        return ""

    def render_external_html(self):
        return ""

    def get_menu_item(self):
        if hasattr(self.context['context']['request'], 'impostor_info'):
            dev = {
                'id': "fsb_%s" % self.context['item'].id,
                'title': 'Switch user',
                'link':  reverse('auth_and_perms:remove_impostor'),
                'icon': self.context['item'].icon
            }
            return """
                <a id="%(id)s" title="%(title)s" aria-controls="divref"
                 aria-expanded="false" class="bg-red"
                href="%(link)s">
                <span class="%(icon)s" aria-hidden="true"></span></a>
            """ % dev
        return ""
