from django import forms
from .models import *

class ContactForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200,required=True)
    message = forms.CharField(max_length=1000)