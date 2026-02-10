'''
Created on 29 jun. 2018

@author: luis
'''

from django import forms

from msds.models import MSDSObject


class FormMSDSobject(forms.ModelForm):
    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']


class FormMSDSobjectUpdate(forms.ModelForm):
    class Meta:
        model = MSDSObject
        fields = ['provider', 'product', 'file']
