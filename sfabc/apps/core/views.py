from django.shortcuts import render
from django.views.generic import *
from apps.core.models import A_Propos, Image_AP

# Create your views here.
class HomeView(TemplateView):
    template_name = "base.html"

    def post(self, request, **kwargs):
        return render(request, self.template_name)


class AProposView(ListView):
    model = A_Propos
    context_object_name = "infos"
    template_name = "pages/about.html"


    def get_queryset(self):
        return A_Propos.objects.order_by("ordre_ap").prefetch_related("page_ap__image")


    def get_context_data(self, **kwargs):
        context = super(AProposView, self).get_context_data(**kwargs)
        return context