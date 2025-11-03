from django.shortcuts import render
from django.views.generic import *
from django.db.models import Prefetch
from .models import *

# Create your views here.
class ProduitListView(ListView):
    model = Produit
    template_name = "pages/liste_produits.html"
    context_object_name = "produits"


    def get_queryset(self):
        query = self.request.GET.get('search')
        if query:
            return Produit.objects.filter(nom_produit__icontains=query).select_related('famille').prefetch_related("images").order_by("famille")
        return Produit.objects.select_related('famille').prefetch_related("images").order_by("famille")


    def get_context_data(self, **kwargs):
        context = super(ProduitListView, self).get_context_data(**kwargs)
        context["title"] = "Les produits"
        context["search"] = self.request.GET.get('search')
        for p in context["produits"]:
            if p.images.all().exists():
                p.img_affichage = p.images.all()[0]
            else:
                p.img_affichage = None
        return context


class ProduitDetailView(DetailView):
    model=Produit