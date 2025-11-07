from django.shortcuts import render
from django.views.generic import *
from django.db.models import Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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


class ProduitDetailView(DetailView):
    model=Produit