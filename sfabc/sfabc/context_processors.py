from apps.core.models import Site
from apps.products.models import Produit
from django.templatetags.static import static
def style_processor(request):
    site = Site.objects.first()
    body_bg = "#f6f2e8"
    body_fg = "#B8A67E"
    police = "Alata"
    logo = static("images/logo.png")
    bandeau = static("images/bois.jpg")
    hauteur_bandeau = 140
    btn_color = "#5A4328"
    product_image_container_bg_color = "#ffffff"
    title_font_color = "#ffffff"
    if site is not None:
        body_bg = site.background
        body_fg = site.foreground
        police = site.police
        logo = site.logo.image.url if site.logo is not None else logo
        bandeau = site.bandeau.image.url if site.bandeau is not None else bandeau
        btn_color = site.bouton_color
        product_image_container_bg_color = site.product_image_container_background_color
        title_font_color = site.title_font
        hauteur_bandeau = site.bandeau_hauteur
        
    body_fg_rgb = str(tuple(int(body_fg.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)))[1:-1]
    style = ":root{\n"
    style += f"\t--bs-body-bg: {body_bg} !important;\n"
    style += f"\t--bs-dark-rgb: {body_fg_rgb} !important;\n"
    style += f'\t--bs-body-font-family: {police};\n'
    style += f'\t--btn-color: {btn_color};\n'
    style += f'\t--product-image-container-bg-color: {product_image_container_bg_color};\n'
    style += f'\t--title-font-color: {title_font_color};\n'
    style += "}\n"
    style += ".background-img {\n"
    style += f"\theight: {hauteur_bandeau}px;\n"
    style += "}\n"
    style += ".title {\n"
    style += f"\tbottom: calc(160px + {hauteur_bandeau/2}px + 0.5em);\n"
    style += "}\n"
    
    menus = dict()

    produits = Produit.objects.all()
    for produit in produits:
        if not menus.get(produit.famille.nom_famille):
            menus[produit.famille.nom_famille] = dict()
        menus[produit.famille.nom_famille][produit.nom_produit] = produit.id_produit

    return {
        "site_style": style,
        "site_logo": logo,
        "site_bandeau": bandeau,
        "menus": menus
    }