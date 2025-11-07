from django.db import models
from colorfield.fields import ColorField
from django.utils.html import mark_safe
import os

# Create your models here.
class A_Propos(models.Model):
    id_ap = models.AutoField(primary_key=True)
    ordre_ap = models.IntegerField()
    titre_ap = models.CharField(max_length=1000)
    description_ap = models.TextField()

    def __str__(self):
        return self.titre_ap
    
    class Meta:
        verbose_name_plural = "A propos"


class Image_Site(models.Model):
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images/site")
    
    def image_tag(self):
        return mark_safe('<img src="/directory/%s" width="150" height="150" />' % (self.image))

    image_tag.short_description = "Image du site"
    
    def __str__(self):
        return os.path.basename(self.image.name)
    
    class Meta:
        verbose_name_plural = "Images du site"


EMPLACEMENT = [
    ("right", "Droite"),
    ("center", "Centre"),
    ("left", "Gauche")
]


class Image_AP(models.Model):
    image = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="images_ap")
    page_ap = models.ForeignKey(A_Propos, on_delete=models.CASCADE, related_name="images")
    titre_image = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(choices=EMPLACEMENT)

    class Meta:
        unique_together = ('image', 'page_ap')
        verbose_name_plural = "Images à propos"

    def __str__(self):
        return f"{self.page_ap} - {self.titre_image if self.titre_image else self.image.image.name}"


class Site(models.Model):
    id = models.AutoField(primary_key=True)
    background = ColorField(default="#F6F2E8")
    foreground = ColorField(default="#B8A67E")
    police = models.CharField(max_length=200, default="Alata")
    bandeau_hauteur = models.IntegerField(default=140)
    logo = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="logo_site")
    bandeau = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="bandeau_site")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name_plural = "Site"

    def __str__(self):
        return f"<Site background: {self.background}, foreground: {self.foreground}, police: {self.police}>"
