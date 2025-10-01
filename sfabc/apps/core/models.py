from django.db import models

# Create your models here.
class A_Propos(models.model):
    id_ap = models.AutoField(primary_key=True)
    titre_ap = models.CharField(max_length=1000)
    description_ap = models.CharField()

    def __str__(self):
        return self.titre_ap


class Image(models.Model):
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images")
    page_ap = models.ForeignKey(A_Propos, on_delete=models.CASCADE, related_name="images_ap", null=True, blank=True)

    def __str__(self):
        return self.image


class Site(models.Model):
    id = models.AutoField(primary_key=True)
    couleur = models.CharField(max_length=7) # exemple #000000
    police = models.CharField(max_length=200)
    logo = models.ForeignKey(Image, related_name="image_site")

    def __str__(self):
        return f"<Site {self.couleur}, {self.police}>"
