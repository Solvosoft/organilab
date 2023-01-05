'''
Created on 29 jun. 2018

@author: luis
'''

from captcha.fields import ReCaptchaField


from django import forms
from msds.models import MSDSObject
import os
import hashlib
from django.conf import settings


class FormMSDSobject(forms.ModelForm):

    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']


class FormMSDSobjectUpdate(forms.ModelForm):

    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']
