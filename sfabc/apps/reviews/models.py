from django.db import models
from apps.products.models import Produit

# Create your models here.
NOTES = {
    1 : "1",
    2 : "2",
    3 : "3",
    4 : "4",
    5 : "5"
}

class Avis(models.Model):
    id_note = models.AutoField(primary_key=True)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="avis")
    pseudonyme = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    valeur = models.IntegerField(choices=NOTES)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.pseudonyme} sur {self.produit} : {self.valeur}/5"
    
    def stars(self) :
        rate = ""
        for _ in range(self.valeur):
            rate += "★"
        for _ in range(5-self.valeur):
            rate += "☆"
        return rate
    
    def get_nom_produit(self):
        return self.produit.nom_produit
