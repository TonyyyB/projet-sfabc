from django.shortcuts import render
from django.views.generic import *

# Create your views here.
def home(request):
    return render(request, 'base.html', {'menus': {'Chaise': {'Chaise en bois': 'chair'}, 'Tables': {'Table en bois': 'table'}, 'Canapés': {'Canapé en cuir': 'sofa'}}})