from django.shortcuts import render
from django.views.generic import *
from apps.products.models import *
from django.db.models import Prefetch

# Create your views here.
class Home(ListView):
    model = Produit
    template_name = "pages/home.html"
    context_object_name = "produits_moment"
    
    def get_queryset(self):
        return Produit.objects.filter(is_produit_du_moment = True).prefetch_related(Prefetch("images_produit", queryset=Image_Produit.objects.filter(is_produit_du_moment = True).select_related("image"), to_attr='images_list'))
    
    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['title'] = "Découvrez mes produits"
        return context
