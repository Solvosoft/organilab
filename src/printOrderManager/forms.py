'''
Created on 14 sep. 2018

@author: luisfelipe7
'''
# Imports for the models and forms
from django.contrib.gis.db import models
from django import forms
from .models import PrintObject
# Imports for the widgets
from cruds_adminlte.widgets import CKEditorWidget
from cruds_adminlte.widgets import DatePickerWidget
from cruds_adminlte import TimePickerWidget
from django.conf import settings
from mapwidgets.widgets import GooglePointFieldWidget, GoogleStaticOverlayMapWidget, GooglePointFieldInlineWidget
from location_field.models.plain import PlainLocationField
# Import the logging library
import logging
# Import the validators
from .validators import validate_email
# Import for the captcha
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

# Forms for the severals models


class PrintRegisterForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Print Name (Ex: Print)'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Print Email or Principal Email to contact (Ex: print@gmail.com)'}))
    logo = forms.ImageField(widget=forms.FileInput(
        attrs={'class': '', 'accept': '.jpg, .jpeg, .png, .gif'}))
    phone = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Phone number of your print (Ex: +55577777777) '}))
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = PrintObject
        fields = ['name', 'email', 'phone', 'description', 'logo', 'location']
        widgets = {
            'location': GooglePointFieldWidget,
            'description': CKEditorWidget(attrs={'class': 'form-control', 'lang': settings.LANGUAGE_CODE, 'value': 'Hola', 'text': 'Bien y usted'}),
        }


class PrintLoginForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Name'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    logo = forms.ImageField(widget=forms.FileInput(
        attrs={'class': 'form-control'}))

    class Meta:
        model = PrintObject
        fields = ['name', 'email', 'logo', 'location', 'geolocation']
        widgets = {
            'location': GooglePointFieldWidget,
            'geolocation': GoogleStaticOverlayMapWidget,
        }


class FormPrintObject(forms.ModelForm):

    class Meta:
        model = PrintObject
        fields = ['name', 'email', 'logo',
                  'description', 'geolocation', 'location']
        widgets = {
            'location': GooglePointFieldWidget,
            'geolocation': GoogleStaticOverlayMapWidget,
        }
