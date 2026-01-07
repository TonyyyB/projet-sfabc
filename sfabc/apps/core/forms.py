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


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["titre_service", "description_service"]
        widgets = {
            "titre_service": forms.TextInput(attrs={"class": "input"}),
            "description_service": forms.Textarea(attrs={"class": "textarea", "rows": 6}),
        }


class ImageServiceForm(forms.ModelForm):
    upload = forms.ImageField(required=False)

    class Meta:
        model = Image_Service
        fields = ["image", "titre_image"]
        widgets = {
            "titre_image": forms.TextInput(attrs={"class": "input"}),
            "image": forms.Select(attrs={"class": "select-image"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['titre_image'].required = False

    def clean(self):
        cleaned = super().clean()
        delete_field_name = 'DELETE'
        delete_value = cleaned.get(delete_field_name, False)
        if delete_value:
            return cleaned
        image = cleaned.get("image")
        upload = cleaned.get("upload")
        if image and upload:
            raise forms.ValidationError("Choisissez une image OU un upload.")
        return cleaned


ImageServiceFormSet = inlineformset_factory(
    Service,
    Image_Service,
    form=ImageServiceForm,
    extra=1,
    can_delete=True
)