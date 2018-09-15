'''
Created on 14 sep. 2018

@author: luisfelipe7
'''
from django import forms
from .models import Print
from cruds_adminlte.widgets import CKEditorWidget
from cruds_adminlte.widgets import DatePickerWidget
from cruds_adminlte import TimePickerWidget
from django.conf import settings

# Create print form


class FormPrint(forms.ModelForm):
    # captcha = ReCaptchaField(widget=ReCaptchaWidget())
    # file = forms.ImageField()
    # ext_whitelist = ['.pdf', '.odt', '.docx', '.doc']

    # def clean_file(self):
    # name = self.cleaned_data['file'].name
    # ext = os.path.splitext(name)[1]
    # ext = ext.lower()
    # if ext not in self.ext_whitelist:
    #    raise forms.ValidationError(_("Not allowed filetype!"))
    # data = self.cleaned_data['file'].read()
    # m = hashlib.md5()
    #  m.update(data)
    # new_name = "%s%s" % (m.hexdigest(), ext)
    # new_path = os.path.join(settings.STATIC_CRAWL, "%s%s" % (
    #    m.hexdigest(), ext))
    #
    # with open(new_path, 'wb') as arch:
    #    arch.write(data)

    #    return new_name

    class Meta:
        model = Print
        fields = ['id', 'email', 'location',
                  'logo', 'description', 'startTime']
        widgets = {
            'startTime': TimePickerWidget(attrs={'icon': 'fa-clock-o'}),
        }
