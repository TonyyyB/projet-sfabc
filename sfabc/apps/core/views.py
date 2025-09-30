from django.shortcuts import render
from django.views.generic import *

# Create your views here.
class HomeView(TemplateView):
    template_name = "base.html"

    def post(self, request, **kwargs):
        return render(request, self.template_name)