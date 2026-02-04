from django import forms
from django.forms import inlineformset_factory

from colorfield.widgets import ColorWidget

from .models import A_Propos, Groupe_A_Propos, Image_Service, Image_Site, Service, Site

class ImageSiteForm(forms.ModelForm):
    """Formulaire admin pour uploader une Image_Site."""

    class Meta:
        model = Image_Site
        fields = ["image"]

POLICES = [
    ("Alata", "Alata"),
    ("Roboto", "Roboto"),
    ("Montserrat", "Montserrat"),
    ("Playfair Display", "Playfair Display"),
    ("Poppins", "Poppins"),
]

class SiteForm(forms.ModelForm):
    """Formulaire admin de configuration du site (couleurs, police, bandeau, logo)."""

    class Meta:
        model = Site
        fields = [
            "page_foreground",
            "page_background",
            "card_background",
            "carousel_background",
            "border_primary",
            "border_secondary",
            "text_title",
            "text_subtitle",
            "text_normal",
            "text_important",
            "text_discreet",
            "text_link",
            "text_header",
            "shadow",
            "police",
            "bandeau_hauteur",
            "logo",
            "bandeau",
        ]
        widgets = {
            "page_foreground": ColorWidget,
            "page_background": ColorWidget,
            "card_background": ColorWidget,
            "carousel_background": ColorWidget,
            "border_primary": ColorWidget,
            "border_secondary": ColorWidget,
            "text_title": ColorWidget,
            "text_subtitle": ColorWidget,
            "text_normal": ColorWidget,
            "text_important": ColorWidget,
            "text_discreet": ColorWidget,
            "text_link": ColorWidget,
            "text_header": ColorWidget,
            "shadow": ColorWidget,
            "police": forms.Select(choices=POLICES),
            "bandeau_hauteur": forms.NumberInput(attrs={"min": 50, "max": 400}),
        }


class GroupeAProposForm(forms.ModelForm):
    """Formulaire admin pour créer/modifier un groupe "À propos"."""

    class Meta:
        model = Groupe_A_Propos
        fields = ["titre_groupe"]
        widgets = {
            "titre_groupe": forms.TextInput(attrs={"class": "input"}),
        }


class AProposForm(forms.ModelForm):
    """Formulaire admin pour créer/modifier une section "À propos"."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher les groupes dans l'ordre défini.
        self.fields["groupe"].queryset = Groupe_A_Propos.objects.order_by("ordre_groupe", "pk")

    class Meta:
        model = A_Propos
        fields = ["groupe", "titre_ap", "description_ap"]
        widgets = {
            "groupe": forms.Select(attrs={"class": "input"}),
            "titre_ap": forms.TextInput(attrs={"class": "input"}),
            "description_ap": forms.Textarea(attrs={"rows": 6}),
        }

class ImageSlotForm(forms.Form):
    """Formulaire gérant un slot d'image pour "À propos" (position + image existante ou upload)."""
    position = forms.ChoiceField(
        choices=[("Gauche", "Gauche"), ("Centre", "Centre"), ("Droite", "Droite")],
        widget=forms.HiddenInput()
    )

    image = forms.ModelChoiceField(
        queryset=Image_Site.objects.all(),
        required=False
    )

    upload = forms.ImageField(required=False)
    titre_image = forms.CharField(required=False)

class ServiceForm(forms.ModelForm):
    """Formulaire admin pour créer/modifier un service (titre + description)."""

    class Meta:
        model = Service
        fields = ["titre_service", "description_service"]
        widgets = {
            "titre_service": forms.TextInput(attrs={"class": "input"}),
            "description_service": forms.Textarea(attrs={"class": "textarea", "rows": 6}),
        }


class ImageServiceForm(forms.ModelForm):
    """Formulaire admin d'une image de service (image existante ou upload + titre)."""
    upload = forms.ImageField(required=False)

    class Meta:
        model = Image_Service
        fields = ["image", "titre_image"]
        widgets = {
            "titre_image": forms.TextInput(attrs={"class": "input"}),
            "image": forms.Select(attrs={"class": "select-image"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialise le formulaire et rend certains champs optionnels (image/titre)."""
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['titre_image'].required = False

    def clean(self):
        """Valide la cohérence image/upload (choix exclusif) et autorise les formulaires vides si non supprimés."""
        cleaned = super().clean()
        delete_field_name = 'DELETE'
        delete_value = cleaned.get(delete_field_name, False)
        if delete_value:
            return cleaned
        image = cleaned.get("image")
        upload = cleaned.get("upload")
        if image and upload:
            raise forms.ValidationError("Choisissez une image OU un upload.")
        if not image and not upload:
            # Permettre les formulaires vides (cartes sans image)
            pass
        return cleaned

    def save(self, commit=True):
        """Sauvegarde l'instance en créant une Image_Site lors d'un upload (si fourni)."""
        instance = super().save(commit=False)

        # Gérer l'upload d'image
        upload = self.cleaned_data.get('upload')
        if upload:
            instance.image = Image_Site.objects.create(image=upload)

        if commit:
            instance.save()
        return instance


ImageServiceFormSet = inlineformset_factory(
    Service,
    Image_Service,
    form=ImageServiceForm,
    extra=1,
    can_delete=True
)
