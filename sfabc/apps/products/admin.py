from django.contrib import admin
from apps.products.models import Famille, Produit, Image_Produit

# Register your models here.
admin.site.register(Famille)
admin.site.register(Produit)
admin.site.register(Image_Produit)
