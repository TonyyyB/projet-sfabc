from apps.core.models import Site
from django.templatetags.static import static
def style_processor(request):
    site = Site.objects.first()
    body_bg = "#f6f2e8"
    body_fg = "#B8A67E"
    police = "Alata"
    logo = static("images/logo.png")
    bandeau = static("images/bois.jpg")
    hauteur_bandeau = 140
    if site is not None:
        body_bg = site.background
        body_fg = site.foreground
        police = site.police
        logo = site.logo.image.url if site.logo.image is not None else logo
        bandeau = site.bandeau.image.url if site.bandeau.image is not None else bandeau
        hauteur_bandeau = site.bandeau_hauteur
        
    body_fg_rgb = str(tuple(int(body_fg.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)))[1:-1]
    style = ":root{\n"
    style += f"\t--bs-body-bg: {body_bg} !important;\n"
    style += f"\t--bs-dark-rgb: {body_fg_rgb} !important;\n"
    style += f'\t--bs-body-font-family: {police};\n'
    style += "}\n"
    style += ".background-img {\n"
    style += f"\theight: {hauteur_bandeau}px;\n"
    style += "}\n"
    style += ".title {\n"
    style += f"\tbottom: calc(90px + {hauteur_bandeau/2}px + 0.5em);\n"
    style += "}\n"
    
    menus = {
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
        'Meubles sur mesure': {'Meuble TV sur mesure': 'custom_tv_stand', 'Bibliothèque sur mesure': 'custom_bookcase'}}
    
    menus = {
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
        'Meubles sur mesure': {'Meuble TV sur mesure': 'custom_tv_stand', 'Bibliothèque sur mesure': 'custom_bookcase'}}
    
    menus = {
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
        'Meubles sur mesure': {'Meuble TV sur mesure': 'custom_tv_stand', 'Bibliothèque sur mesure': 'custom_bookcase'}}
    
    return {
        "site_style": style,
        "site_logo": logo,
        "site_bandeau": bandeau,
        "menus": menus
    }