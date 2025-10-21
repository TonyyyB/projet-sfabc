from django.shortcuts import render
from django.views.generic import *
from apps.products.models import *
from django.db.models import Prefetch

# Create your views here.
def home(request):
    return render(request, 'pages/home.html')

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
