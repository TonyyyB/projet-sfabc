from django.db import models
from sfabc.apps.core.models import Image

# Create your models here.
class Famille(models.Model):

    id_famille = models.AutoField(primary_key=True)
    nom_famille = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nomFamille
    

class Produit(models.Model):
    
    id_produit = models.AutoField(primary_key=True)
    type_produit = models.CharField(max_length=200)
    prix_produit = models.DecimalField(max_digits=10, decimal_places=2)
    description_produit = models.TextField()
    # Relation CIF : chaque produit appartient à 1 famille (0,N côté famille 1,1 côté produit)→
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE, related_name="produits",null=True, blank=True)
    