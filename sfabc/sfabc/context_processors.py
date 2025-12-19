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


    if site is not None:
        body_bg = site.background
        body_fg = site.foreground
        police = site.police
        logo = site.logo.image.url if site.logo.image is not None else logo
        bandeau = site.bandeau.image.url if site.bandeau.image is not None else bandeau
        hauteur_bandeau = site.bandeau_hauteur
        
    body_fg_rgb = str(tuple(int(body_fg.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)))[1:-1]
    style = f"""
    :root {{
        --bs-body-bg: {body_bg} !important;
        --bs-dark-rgb: {body_fg_rgb} !important;
        --bs-body-font-family: {police};
    }}

    .background-img {{
        height: {hauteur_bandeau}px;
    }}

    .title {{
        bottom: calc(160px + {hauteur_bandeau/2}px + 0.5em);
    }}

    .produit {{
        border: 2px solid {body_fg};
    }}

    .prix-prod {{
        color: {body_fg};
    }}

    .btn-outline-primary.btn-pagination {{
        color: {body_fg};
        border-color: {body_fg};
    }}

    .btn-outline-primary.btn-pagination:hover {{
        color: {body_bg};
        background-color: {body_fg};
        border-color: {body_fg};
    }}

    .btn-outline-primary.btn-pagination.active {{
        color: {body_bg};
        background-color: {body_fg};
        border-color: {body_fg};
    }}

    .btn-outline-primary.btn-pagination:disabled {{
        color: {body_fg};
    }}

    .titre-service {{
        color: {body_fg};
    }}
    
    .product-image-container {{
        border: 2.5px solid {body_fg};
    }}

    .color-text-contact {{
        color: {body_fg} !important;
    }}

    .btn-contact {{
        color: #ffffff !important;
        background-color: {body_fg} !important;
    }}

    .color-placeholder-contact::placeholder{{
        opacity: 1 !important;
        color: {body_fg} !important;
    }}

    .color-border-contact {{
        border-color: {body_fg} !important;
    }}
    """
    # style = ":root{\n"
    # style += f"\t--bs-body-bg: {body_bg} !important;\n"
    # style += f"\t--bs-dark-rgb: {body_fg_rgb} !important;\n"
    # style += f'\t--bs-body-font-family: {police};\n'
    # style += "}\n"
    # style += ".background-img {\n"
    # style += f"\theight: {hauteur_bandeau}px;\n"
    # style += "}\n"
    # style += ".title {\n"
    # style += f"\tbottom: calc(160px + {hauteur_bandeau/2}px + 0.5em);\n"
    # style += "}\n"
    
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