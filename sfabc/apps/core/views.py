from django.shortcuts import render
from django.views.generic import *

# Create your views here.
def home(request):
    return render(request, 'pages/home.html', {'menus': {
        'Chaise': {'Chaise en bois': 'chair'}, 
        'Tables': {'Table en bois': 'table'}, 
        'Canapés': {'Canapé en cuir': 'sofa'}, 
        'Meubles de rangement': {'Armoire': 'wardrobe', 'Commode': 'dresser'}, 
        'Lits': {'Lit simple': 'single_bed', 'Lit double': 'double_bed'}, 
        'Bureaux': {'Bureau en bois': 'desk'}, 
        'Chaises de bureau': {'Chaise de bureau ergonomique': 'office_chair'}, 
        'Étagères': {'Étagère murale': 'wall_shelf', 'Bibliothèque': 'bookcase'}, 
        'Meubles de jardin': {'Table de jardin': 'garden_table', 'Chaise de jardin': 'garden_chair'}, 
        'Meubles pour enfants': {'Lit enfant': 'kids_bed', 'Chaise enfant': 'kids_chair'}, 
        'Meubles de salle à manger': {'Table à manger': 'dining_table', 'Chaise de salle à manger': 'dining_chair'}, 
        'Meubles de salon': {'Table basse': 'coffee_table', 'Meuble TV': 'tv_stand'}, 
        'Meubles de bureau': {'Bibliothèque de bureau': 'office_bookcase', 'Caisson de bureau': 'office_pedestal'}, 
        'Meubles de chambre': {'Table de chevet': 'nightstand', 'Coiffeuse': 'dressing_table'}, 
        'Meubles de salle de bain': {'Meuble sous lavabo': 'bathroom_vanity', 'Armoire de salle de bain': 'bathroom_cabinet'}, 
        'Meubles multifonctions': {'Canapé-lit': 'sofa_bed', 'Table extensible': 'extendable_table'}, 
        'Meubles sur mesure': {'Meuble TV sur mesure': 'custom_tv_stand', 'Bibliothèque sur mesure': 'custom_bookcase'}}})
