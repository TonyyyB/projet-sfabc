from django.db import models
from apps.core.models import Image

# Create your models here.
class Famille(models.Model):

    id_famille = models.AutoField(primary_key=True)
    nom_famille = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nomFamille
    

class Produit(models.Model):
    
    id_produit = models.AutoField(primary_key=True)
    nom_produit = models.CharField(max_length=200)
    prix_produit = models.DecimalField(max_digits=10, decimal_places=2)
    description_produit = models.TextField()
    is_produit_du_moment = models.BooleanField(default=False)
    # Relation CIF : chaque produit appartient à 1 famille (0,N côté famille 1,1 côté produit)→

class Image_Produit(models.Model):
    
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="image_produit")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="images_produit")
    is_produit_du_moment = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('image', 'produit')
    def __str__(self):
        return f"Image of {self.produit.nom_produit}"  