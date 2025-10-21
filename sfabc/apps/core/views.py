from django.shortcuts import render
from django.views.generic import *
from apps.core.models import A_Propos, Image_AP
from apps.products.models import *
from django.db.models import Prefetch

# Create your views here.
def home(request):
    return render(request, 'pages/home.html', {"title":"Coucou"})


class AProposView(ListView):
    model = A_Propos
    context_object_name = "infos"
    template_name = "pages/about.html"


    def get_queryset(self):
        return A_Propos.objects.order_by("ordre_ap").prefetch_related("page_ap__image")


    def get_context_data(self, **kwargs):
        context = super(AProposView, self).get_context_data(**kwargs)
        context["title"] = "À propos"
        return context

class Home(ListView):
    model = Produit
    template_name = "sfabc/templates/pages/home.html"
    context_object_name = "produits_moment"
    
    def get_queryset(self):
        return Produit.objects.filter(is_produit_du_moment = True).prefetch_related(Prefetch("image", queryset=Image_Produit.objects.select_related("produit").filter(is_produit_du_moment = True)))
    
    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['titre'] = "Découvrez mes produits"
        return context
