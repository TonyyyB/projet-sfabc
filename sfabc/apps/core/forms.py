from django import forms
from .models import *

class ContactForm(forms.Form):
    Nom = forms.CharField(required=True)
    Email = forms.EmailField(required=True)
    Sujet = forms.CharField(max_length=200,required=True)
    Message = forms.CharField(max_length=1000)