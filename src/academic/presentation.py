from django.utils.safestring import mark_safe


class HTMLPresentation:

    def get_description_display(self):
        return mark_safe(self.description)
