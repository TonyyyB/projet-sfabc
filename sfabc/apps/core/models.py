import os

from django.db import models
from django.utils.html import mark_safe

from colorfield.fields import ColorField

# Create your models here.
class A_Propos(models.Model):
    """Modèle représentant une section de la page "À propos"."""
    id_ap = models.AutoField(primary_key=True)
    ordre_ap = models.PositiveIntegerField(unique=True)
    titre_ap = models.CharField(max_length=1000)
    description_ap = models.TextField()


    def __str__(self):
        """Représentation lisible d'une section "À propos" (titre)."""
        return self.titre_ap

    class Meta:
        verbose_name_plural = "A propos"

class Service(models.Model):
    """Modèle représentant un service affiché sur le site."""
    id_service = models.AutoField(primary_key=True)
    titre_service = models.CharField(max_length=200)
    description_service = models.TextField()
    ordre_service = models.IntegerField()
    image = models.ManyToManyField("Image_Site",through="Image_Service")

    def __str__(self):
        """Représentation lisible d'un service (titre)."""
        return self.titre_service


class Image_Site(models.Model):
    """Modèle d'image générique utilisée sur le site (logo, bandeau, pages, etc.)."""
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images/site")

    def image_tag(self):
        """Retourne un snippet HTML (img) pour l'admin afin de prévisualiser l'image."""
        return mark_safe(f'<img src="/directory/{self.image}" width="150" height="150" />')

    image_tag.short_description = "Image du site"

    def __str__(self):
        """Retourne le nom de fichier de l'image (basename)."""
        return os.path.basename(self.image.name)

    class Meta:
        verbose_name_plural = "Images du site"


EMPLACEMENT = [
    ("right", "Droite"),
    ("center", "Centre"),
    ("left", "Gauche"),
]

class Image_A_Propos(models.Model):
    """Association entre une section "À propos" et une image, positionnée (gauche/centre/droite)."""
    image = models.ForeignKey(
        Image_Site,
        on_delete=models.CASCADE,
        related_name="images_A_Propos",
    )
    page_ap = models.ForeignKey(A_Propos, on_delete=models.CASCADE, related_name="images")
    titre_image = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(choices=EMPLACEMENT)

    class Meta:
        unique_together = ('position', 'page_ap')
        verbose_name_plural = "Images à propos"

    def __str__(self):
        """Représentation lisible du lien image ↔ section "À propos" (avec titre si présent)."""
        titre = self.titre_image if self.titre_image else self.image.image.name
        return f"{self.page_ap} - {titre}"

class Image_Service(models.Model):
    """Association entre un service et une image du site (avec titre optionnel)."""
    image = models.ForeignKey(
        Image_Site,
        on_delete=models.CASCADE,
        related_name="images_Service",
        null=True,
        blank=True,
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="service")
    titre_image = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = ('image', 'service')

    def __str__(self):
        """Représentation lisible du lien image ↔ service."""
        return f"service {self.service} avec des {self.image}"

class Site(models.Model):
    """Configuration singleton du site (couleurs, police, logo, bandeau)."""
    id = models.AutoField(primary_key=True)
    background = ColorField(default="#F6F2E8")
    foreground = ColorField(default="#B8A67E")
    police = models.CharField(max_length=200, default="Alata")
    bandeau_hauteur = models.IntegerField(default=140)
    logo = models.ForeignKey(
        Image_Site,
        on_delete=models.CASCADE,
        related_name="logo_site",
        null=True,
        blank=True,
    )
    bandeau = models.ForeignKey(
        Image_Site,
        on_delete=models.CASCADE,
        related_name="bandeau_site",
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        """Force l'unicité (pk=1) afin de conserver un singleton de configuration du site."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Charge la configuration unique du site (crée l'objet pk=1 si absent)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name_plural = "Site"

    def __str__(self):
        """Représentation lisible de la configuration du site (couleurs/police)."""
        return f"<Site background: {self.background}, foreground: {self.foreground}, police: {self.police}>"
