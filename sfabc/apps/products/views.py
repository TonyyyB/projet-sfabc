from django.shortcuts import render
from django.views.generic import *
from apps.products.models import Produit, Image_Produit
from django.db.models import Count, Prefetch, Avg
from django import template

from apps.reviews.models import Avis

# Create your views here.
class DetailProduitView(DetailView):
    model = Produit
    template_name = "products/detail.html"
    context_object_name = "produit"
    
    def get_queryset(self):
        return Produit.objects.prefetch_related('images', 'avis')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context["images"] = context["produit"].images.all()
        context["title"] = self.object.nom_produit
        
        # Calculer la moyenne des avis
        avis_stats = Avis.objects.filter(produit=self.object).aggregate(
            moyenne=Avg('valeur'),
            nombre=Count('id_note')
        )
        
        #moyenne_avis = avis_stats['moyenne']
        #nombre_avis = avis_stats['nombre']
        
        moyenne_avis = 4.5
        nombre_avis = 5
        
        # Créer une liste de dictionnaires pour les étoiles
        etoiles = []
        if moyenne_avis:
            for i in range(1, 6):
                if moyenne_avis >= i:
                    masque = 0  # Étoile pleine
                elif moyenne_avis > i - 1:
                    masque = 100 - int((moyenne_avis - (i - 1)) * 100)
                else:
                    masque = 100  # Étoile vide
                etoiles.append(masque)
        else:
            etoiles = [100, 100, 100, 100, 100]  # Toutes vides
        
        context['moyenne_avis'] = moyenne_avis
        context['nombre_avis'] = nombre_avis
        context['etoiles'] = etoiles
        
        return context
    

    