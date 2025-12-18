from django import forms
from .models import *
from colorfield.widgets import ColorWidget
from django.forms import inlineformset_factory

class ContactForm(forms.Form):
    Nom = forms.CharField(required=True)
    Email = forms.EmailField(required=True)
    Sujet = forms.CharField(max_length=200,required=True)
    Message = forms.CharField(max_length=1000)

POLICES = [
    ("Alata", "Alata"),
    ("Roboto", "Roboto"),
    ("Montserrat", "Montserrat"),
    ("Playfair Display", "Playfair Display"),
    ("Poppins", "Poppins"),
]

class ImageSiteForm(forms.ModelForm):
    class Meta:
        model = Image_Site
        fields = ["image"]

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            "background",
            "foreground",
            "police",
            "bandeau_hauteur",
            "logo",
            "bandeau",
        ]
        widgets = {
            "background": ColorWidget,
            "foreground": ColorWidget,
            "police": forms.Select(choices=POLICES),
            "bandeau_hauteur": forms.NumberInput(attrs={"min": 50, "max": 400}),
        }


class AProposForm(forms.ModelForm):
    class Meta:
        model = A_Propos
        fields = ["titre_ap", "description_ap"]
        widgets = {
            "titre_ap": forms.TextInput(attrs={"class": "input"}),
            "description_ap": forms.Textarea(attrs={"rows": 6}),
        }

class ImageSlotForm(forms.Form):
    image = forms.ModelChoiceField(
        queryset=Image_Site.objects.all(),
        required=False
    )
    upload = forms.ImageField(required=False)
    titre_image = forms.CharField(required=False, max_length=100)