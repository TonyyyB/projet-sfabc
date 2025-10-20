from django.db import models
from colorfield.fields import ColorField


# Create your models here.
class A_Propos(models.Model):
    id_ap = models.AutoField(primary_key=True)
    ordre_ap = models.IntegerField()
    titre_ap = models.CharField(max_length=1000)
    description_ap = models.CharField()

    def __str__(self):
        return self.titre_ap


class Image(models.Model):
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images")

    def __str__(self):
        return self.image.name


class Image_AP(models.Model):
    images = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="images")
    page_ap = models.ForeignKey(A_Propos, on_delete=models.CASCADE, related_name="page_ap")

    class Meta:
        unique_together = ('images', 'page_ap')

    def __str__(self):
        return f"page a propos {self.page_ap} avec des {self.images}"


class Site(models.Model):
    id = models.AutoField(primary_key=True)
    background = ColorField(default="#F6F2E8")
    foreground = ColorField(default="#B8A67E")
    police = models.CharField(max_length=200)
    logo = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="image_site")

    def __str__(self):
        return f"<Site {self.couleur}, {self.police}>"
