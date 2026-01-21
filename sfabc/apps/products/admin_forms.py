from django import forms
from django.forms import inlineformset_factory

from apps.products.models import Famille, Image_Produit, Produit


class FamilleForm(forms.ModelForm):
    """Formulaire admin pour créer/modifier une famille."""

    class Meta:
        model = Famille
        fields = ["nom_famille"]

class ProduitForm(forms.ModelForm):
    """Formulaire admin pour créer/modifier un produit."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Placeholder plus explicite que le "---------" par défaut
        if "famille" in self.fields:
            self.fields["famille"].empty_label = "— Choisir une famille —"
            self.fields["famille"].queryset = Famille.objects.all().order_by("nom_famille")

    class Meta:
        model = Produit
        fields = [
            "nom_produit",
            "description_produit",
            "prix_produit",
            "famille",
            "is_produit_du_moment",
        ]


class ImageProduitForm(forms.ModelForm):
    """Formulaire admin pour gérer une ligne d'image produit (sélection existante ou upload)."""

    class Meta:
        model = Image_Produit
        # IMPORTANT: on n'inclut PAS le champ modèle `image` (ImageField) dans le form.
        # Sinon Django attend un fichier dans request.FILES et lève
        # "No file was submitted. Check the encoding type on the form.".
        # On pilote `instance.image` via `image_existing` / `upload`.
        fields = ["is_produit_du_moment"]

    # Sélection d'une image existante (bibliothèque) + upload optionnel
    image_existing = forms.ModelChoiceField(
        queryset=Image_Produit.objects.all().order_by("image"),
        required=False,
        label="Image",
        widget=forms.Select(attrs={"class": "select-image"}),
    )
    upload = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialise le formulaire et rend les champs de sélection/upload optionnels."""
        super().__init__(*args, **kwargs)
        self.fields["image_existing"].required = False
        self.fields["upload"].required = False
        # Placeholder plus explicite pour la sélection existante
        self.fields["image_existing"].empty_label = "— Sélectionner une image —"

    def clean(self):
        """Valide le choix exclusif (image existante vs upload) et remplit instance.image en conséquence."""
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned

        selected = cleaned.get("image_existing")
        upload = cleaned.get("upload")

        if selected and upload:
            raise forms.ValidationError("Choisissez une image OU un upload.")

        # Appliquer le choix / upload sur l'instance (le modèle attend un ImageField).
        if selected is not None:
            self.instance.image = selected.image

        if upload is not None:
            self.instance.image = upload

        # Si le form a été modifié (ex: image du moment) mais qu'il n'y a pas d'image
        # et que c'est une nouvelle ligne, on bloque.
        if (
            self.instance.pk is None
            and not self.instance.image
            and (selected is not None or upload is not None or cleaned.get("is_produit_du_moment"))
        ):
            raise forms.ValidationError("Sélectionnez une image (ou uploadez-en une).")

        # Autoriser les formulaires vides (extra=1)
        return cleaned

    def save(self, commit=True):
        """Sauvegarde l'image produit; l'image est préparée par clean() (instance.image)."""
        # `clean()` a déjà rempli instance.image si besoin
        return super().save(commit=commit)


ImageProduitFormSet = inlineformset_factory(
    Produit,
    Image_Produit,
    form=ImageProduitForm,
    extra=1,
    can_delete=True,
)
