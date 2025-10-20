from django.db import models

# Create your models here.
class A_Propos(models.Model):
    id_ap = models.AutoField(primary_key=True)
    titre_ap = models.CharField(max_length=1000)
    description_ap = models.CharField()

    def __str__(self):
        return self.titre_ap


class Image(models.Model):
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images")


    def __str__(self):
        return self.image


class Site(models.Model):
    id = models.AutoField(primary_key=True)
    couleur = models.CharField(max_length=7) # exemple #000000
    police = models.CharField(max_length=200)
    logo = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="image_site")

    def __str__(self):
        return f"<Site {self.couleur}, {self.police}>"
