
from django.utils.html import format_html


class HTMLPresentation:

    def get_description_display(self):
        return format_html(self.description)