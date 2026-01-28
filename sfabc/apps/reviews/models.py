from django.db import models
from apps.products.models import Produit

# Create your models here.


class Reponse(models.Model):
    """Modèle représentant une réponse à un avis. Il est lié à un avis, a une date et un message"""
    id_reponse = models.AutoField(primary_key=True)
    date = models.DateField(auto_now_add=True)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        """Représentation lisible d'une réponse."""
        return f"Réponse : {self.message}"


NOTES = {
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
}

class Avis(models.Model):
    """Modèle représentant un avis/notation associé à un produit."""
    id_note = models.AutoField(primary_key=True)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="avis")
    pseudonyme = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    valeur = models.IntegerField(choices=NOTES)
    message = models.TextField(null=True, blank=True)
    reponse = models.ForeignKey(Reponse, on_delete=models.CASCADE, related_name="avis", blank=True, null=True)

    def __str__(self):
        """Représentation lisible d'un avis (pseudonyme, produit, note)."""
        return f"{self.pseudonyme} sur {self.produit} : {self.valeur}/5"

    def stars(self):
        """Retourne une représentation en étoiles (★/☆) de la note sur 5."""
        rate = ""
        for _ in range(self.valeur):
            rate += "★"
        for _ in range(5 - self.valeur):
            rate += "☆"
        return rate

    def get_nom_produit(self):
        """Renvoie le nom du produit associé à l'avis (raccourci template/admin)."""
        return self.produit.nom_produit

