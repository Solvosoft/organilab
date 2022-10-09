'''
Created on 29 jun. 2018

@author: luis
'''

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from django.utils.translation import gettext_lazy as _

from django import forms
from msds.models import MSDSObject
import os
import hashlib
from django.conf import settings


class FormMSDSobject(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']


class FormMSDSobjectUpdate(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']
