'''
Created on 1/8/2016

@author: nashyra
'''

from django.shortcuts import render
from django.http.response import HttpResponse
from django import forms
from django.core.exceptions import ValidationError

# Create your views here.

class FormNums(forms.Form):
    num4 = forms.IntegerField(widget=forms.NumberInput, help_text = "A number")
    
    def clean(self):
        data = super(FormNums, self).clean()
        try:
            num=int(data['num4'])
        except:
            raise ValidationError("Int is required")
        return data

def convert_int(number):
    result = 0
    try:
        result = int(number)
    except:
        pass
    return result