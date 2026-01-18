from django.views.generic import *
from apps.products.models import Produit
from apps.reviews.models import Avis
from django.db.models import Count, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *

class DetailProduitView(DetailView):
    """Vue détail d'un produit avec images et statistiques d'avis."""
    model = Produit
    template_name = "products/detail.html"
    context_object_name = "produit"
    
    def get_queryset(self):
        """Précharge les relations (images, avis) pour afficher un produit efficacement."""
        return Produit.objects.prefetch_related('images', 'avis')
    
    def get_context_data(self, **kwargs):
        """Construit le contexte du détail produit (images, stats des avis, liste des avis)."""
        context = super().get_context_data(**kwargs)
        
        context["images"] = context["produit"].images.all()
        context["title"] = self.object.nom_produit
        
        # Calculer la moyenne des avis
        avis_stats = Avis.objects.filter(produit=self.object).aggregate(
            moyenne=Avg('valeur'),
            nombre=Count('id_note')
        )
        
        if avis_stats['moyenne'] is not None :
            moyenne_avis = round(avis_stats['moyenne'], 2)
        else : moyenne_avis = None
        nombre_avis = avis_stats['nombre']
       
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
        
        # Récupérer les avis liés au produit

        liste_avis = Avis.objects.filter(produit=self.object).order_by('-date')
        context['avis'] = liste_avis

        return context

class ProduitListView(ListView):
    """Vue listant les produits avec recherche et pagination."""
    model = Produit
    template_name = "pages/liste_produits.html"
    context_object_name = "produits"

    def get_queryset(self):
        """Retourne la liste de produits filtrée par recherche (si fournie) et ordonnée par famille."""
        query = self.request.GET.get('search')
        if query:
            return Produit.objects.filter(nom_produit__icontains=query).select_related('famille').prefetch_related("images").order_by("famille")
        return Produit.objects.select_related('famille').prefetch_related("images").order_by("famille")


    def get_context_data(self, **kwargs):
        """Ajoute le titre, la recherche et la pagination au contexte de la liste de produits."""
        context = super(ProduitListView, self).get_context_data(**kwargs)
        context["title"] = "Les produits"
        context["search"] = self.request.GET.get('search')
        for p in context["produits"]:
            if p.images.all().exists():
                p.img_affichage = p.images.all()[0]
            else:
                p.img_affichage = None
        
        # La pagination
        default_page = 1
        page = self.request.GET.get('page', default_page)

        items_per_page = 24
        paginator = Paginator(context["produits"], items_per_page)

        try:
            items_page = paginator.page(page)
        except PageNotAnInteger:
            items_page = paginator.page(default_page)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)
        context["items_page"] = items_page

        return context
