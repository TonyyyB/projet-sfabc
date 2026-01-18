from django.db import models

# Create your models here.
class Famille(models.Model):

    """Modèle représentant une famille/catégorie de produits."""

    id_famille = models.AutoField(primary_key=True)
    nom_famille = models.CharField(max_length=100)
    
    def __str__(self):
        """Représentation lisible d'une famille (nom)."""
        return self.nom_famille 

class Produit(models.Model):
    """Modèle représentant un produit (nom, description, prix, famille, flag du moment)."""
    id_produit = models.AutoField(primary_key=True)
    nom_produit = models.CharField(max_length=200)
    prix_produit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description_produit = models.TextField()
    is_produit_du_moment = models.BooleanField(default=False)
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE, related_name="famille")
    
    def __str__(self):
        """Représentation lisible d'un produit (nom, famille, prix)."""
        return f"{self.nom_produit}, famille {self.famille}: {self.prix_produit}€"
    
class Image_Produit(models.Model):
    """Modèle d'image associable à un produit (ou image "du moment")."""
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images/produits")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="images", null=True, blank=True)
    is_produit_du_moment = models.BooleanField(default=False)

    def __str__(self):
        """Représentation lisible d'une image produit (nom de fichier)."""
        return f"Image {self.image.name}"   
