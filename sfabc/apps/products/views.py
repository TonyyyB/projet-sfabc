from django.shortcuts import render
from django.views.generic import *
from apps.products.models import Produit, Image_Produit
from django.db.models import Count, Prefetch

# Create your views here.
class DetailProduitView(DetailView):
    model = Produit
    template_name = "products/detail.html"
    context_object_name = "produit"
    
    def get_queryset(self):
        return Produit.objects.prefetch_related(Prefetch("images_produit", queryset=Image_Produit.objects.select_related("image"), to_attr="images_list"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for image in context["produit"].images_list:
            print(image.image.image.url)
        context["title"] = self.object.nom_produit
        return context
    