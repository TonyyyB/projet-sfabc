from django.shortcuts import render
from django.views.generic import *
from apps.core.models import A_Propos, Image_AP

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
