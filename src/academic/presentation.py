from django.utils.html import format_html


class HTMLPresentation:
    #This code is deprecated only if no arguments are sent to it.
    def get_description_display(self):
        return format_html(self.description)
