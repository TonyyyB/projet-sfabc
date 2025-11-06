from django.db import models
from colorfield.fields import ColorField
from django.utils.html import mark_safe

# Create your models here.
class A_Propos(models.Model):
    id_ap = models.AutoField(primary_key=True)
    ordre_ap = models.IntegerField()
    titre_ap = models.CharField(max_length=1000)
    description_ap = models.TextField()
    images = models.ManyToManyField("Image_Site", through="Image_AP")

    def __str__(self):
        return self.titre_ap

class Service(models.Model):
    id_service = models.AutoField(primary_key=True)
    titre_service = models.CharField(max_length=200)
    description_service = models.TextField()
    ordre_service = models.IntegerField()
    image = models.ManyToManyField("Image_Site",through="Image_Service")

    def __str__(self):
        return self.titre_service


class Image_Site(models.Model):
    id_image = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images/site")
    
    def image_tag(self):
        return mark_safe('<img src="/directory/%s" width="150" height="150" />' % (self.image))

    image_tag.short_description = "Image du site"
    
    def __str__(self):
        return self.image.name


EMPLACEMENT = [
    ("right", "Droite"),
    ("center", "Centre"),
    ("left", "Gauche")
]




class Image_AP(models.Model):
    image = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="images")
    page_ap = models.ForeignKey(A_Propos, on_delete=models.CASCADE, related_name="page_ap")
    titre_image = models.CharField(max_length=100)
    position = models.CharField(choices=EMPLACEMENT)

    class Meta:
        unique_together = ('image', 'page_ap')

    def __str__(self):
        return f"page a propos {self.page_ap} avec des {self.image}"

class Image_Service(models.Model):
    image = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="images_Service")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="service", null=True, blank=True)
    titre_image = models.CharField(max_length=100)
    position = models.CharField(choices=EMPLACEMENT)

    class Meta:
        unique_together = ('image', 'service')

    def __str__(self):
        return f"service {self.service} avec des {self.image}"

class Site(models.Model):
    id = models.AutoField(primary_key=True)
    background = ColorField(default="#F6F2E8")
    foreground = ColorField(default="#B8A67E")
    police = models.CharField(max_length=200, default="Alata")
    bandeau_hauteur = models.IntegerField(default=140)
    logo = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="logo_site")
    bandeau = models.ForeignKey(Image_Site, on_delete=models.CASCADE, related_name="bandeau_site")

    def __str__(self):
        return f"<Site background: {self.background}, foreground: {self.foreground}, police: {self.police}>"
