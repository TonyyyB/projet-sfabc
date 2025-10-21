from django.shortcuts import render
from django.views.generic import *

# Create your views here.
def home(request):
    return render(request, 'pages/home.html', {"title":"Coucou"})
