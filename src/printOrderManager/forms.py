'''
Created on 14 sep. 2018

@author: luisfelipe7
'''
from django import forms
from .models import PrintObject
from cruds_adminlte.widgets import CKEditorWidget
from cruds_adminlte.widgets import DatePickerWidget
from cruds_adminlte import TimePickerWidget
from django.conf import settings
from mapwidgets.widgets import GooglePointFieldWidget, GoogleStaticOverlayMapWidget, GooglePointFieldInlineWidget
from location_field.models.plain import PlainLocationField

# Create Print Login Form
from django.contrib.gis.db import models


class PrintRegisterForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Name'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    logo = forms.ImageField(widget=forms.FileInput())

    class Meta:
        model = PrintObject
        fields = ['name', 'email', 'logo', 'location']
        widgets = {
            'location': GooglePointFieldWidget,
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
