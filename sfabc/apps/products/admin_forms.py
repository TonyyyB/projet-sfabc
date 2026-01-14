from django import forms
from apps.products.models import *
from django.forms import inlineformset_factory
class FamilleForm(forms.ModelForm):
    class Meta:
        model = Famille
        fields = ["nom_famille"]

class ProduitForm(forms.ModelForm):
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
    class Meta:
        model = Image_Produit
        fields = ["image", "is_produit_du_moment"]


ImageProduitFormSet = inlineformset_factory(
    Produit,
    Image_Produit,
    form=ImageProduitForm,
    extra=1,
    can_delete=True,
)