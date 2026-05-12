import os
from django.db import models, transaction
from django.db.models import Q

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
    image = models.ImageField(upload_to="images/produits", max_length=255)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="images", null=True, blank=True)
    ordre = models.PositiveIntegerField(default=0)
    is_image_du_moment = models.BooleanField(default=False)

    class Meta:
        ordering = ["ordre", "id_image"]
        constraints = [
            models.UniqueConstraint(
                fields=["produit"],
                condition=Q(is_image_du_moment=True) & Q(produit__isnull=False),
                name="unique_image_du_moment_par_produit",
            ),
        ]

    def save(self, *args, **kwargs):
        """Garantit qu'il n'y a qu'une seule image du moment par produit."""
        with transaction.atomic():
            if self.is_image_du_moment and self.produit_id:
                (
                    Image_Produit.objects.filter(produit_id=self.produit_id, is_image_du_moment=True)
                    .exclude(pk=self.pk)
                    .update(is_image_du_moment=False)
                )
            super().save(*args, **kwargs)

    def __str__(self):
        """Représentation lisible d'une image produit (nom de fichier)."""
        return os.path.basename(self.image.name)
