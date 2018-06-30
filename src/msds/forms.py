'''
Created on 29 jun. 2018

@author: luis
'''

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from django.utils.translation import ugettext_lazy as _

from django import forms
from msds.models import MSDSObject
import os
import hashlib
from django.conf import settings


class FormMSDSobject(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())
    file = forms.FileField()
    ext_whitelist = ['.pdf', '.odt', '.docx', '.doc']

    def clean_file(self):
        name = self.cleaned_data['file'].name
        ext = os.path.splitext(name)[1]
        ext = ext.lower()
        if ext not in self.ext_whitelist:
            raise forms.ValidationError(_("Not allowed filetype!"))
        data = self.cleaned_data['file'].read()
        m = hashlib.md5()
        m.update(data)
        new_name = "%s%s" % (m.hexdigest(), ext)
        new_path = os.path.join(settings.STATIC_CRAWL, "%s%s" % (
            m.hexdigest(), ext))

        with open(new_path, 'wb') as arch:
            arch.write(data)

        return new_name

    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']


class FormMSDSobjectUpdate(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())
    file = forms.FileField(required=False)
    ext_whitelist = ['.pdf', '.odt', '.docx', '.doc']

    def clean_file(self):
        dev = None
        if type(self.cleaned_data['file']) == str:
            return self.cleaned_data['file']

        if self.cleaned_data['file']:
            name = self.cleaned_data['file'].name
            ext = os.path.splitext(name)[1]
            ext = ext.lower()
            if ext not in self.ext_whitelist:
                raise forms.ValidationError(_("Not allowed filetype!"))
            data = self.cleaned_data['file'].read()
            m = hashlib.md5()
            m.update(data)
            new_name = "%s%s" % (m.hexdigest(), ext)
            new_path = os.path.join(settings.STATIC_CRAWL, "%s%s" % (
                m.hexdigest(), ext))

            with open(new_path, 'wb') as arch:
                arch.write(data)

            dev = new_name
        elif self.instance.file:
            dev = self.instance.file
        return dev

    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']
