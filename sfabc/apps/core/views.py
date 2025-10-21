from django.shortcuts import render
from django.views.generic import *
from apps.products.models import *
from django.db.models import Prefetch

# Create your views here.
def home(request):
    return render(request, 'pages/home.html', {"title":"Coucou"})
