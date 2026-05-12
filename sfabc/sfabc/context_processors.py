from apps.core.models import Site
from apps.products.models import Produit
from django.templatetags.static import static
from django.db import OperationalError
import logging

logger = logging.getLogger(__name__)

def style_processor(request):
    try:
        site = Site.objects.first()
    except OperationalError as e:
        logger.error(f"Database error in context processor: {e}")
        print("Database error in context processor:", e)
        site = None
    
    if site is None:
        Site.objects.create()  # Crée une instance par défaut si la base de données est accessible mais vide
        site = Site.objects.first()
    if site.logo is None:
        logo = static("images/logo.png")
    if site.bandeau is None:
        bandeau = static("images/bois.jpg")
    page_foreground = site.page_foreground
    page_background = site.page_background
    card_background = site.card_background
    carousel_background = site.carousel_background
    border_primary = site.border_primary
    border_secondary = site.border_secondary
    text_title = site.text_title
    text_subtitle = site.text_subtitle
    text_normal = site.text_normal
    text_important = site.text_important
    text_discreet = site.text_discreet
    text_link = site.text_link
    text_header = site.text_header
    shadow = site.shadow
    button_color = site.button_color
    button_hover_color = site.button_hover_color
    police = site.police
    logo = site.logo.image.url if site.logo is not None else logo
    bandeau = site.bandeau.image.url if site.bandeau is not None else bandeau
    hauteur_bandeau = site.bandeau_hauteur
        
    page_foreground_rgb = str(tuple(int(page_foreground.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)))[1:-1]
    shadow_rgb = str(tuple(int(shadow.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)))[1:-1]
    
    style = ":root{\n"
    style += f"\t--logo-size: 150px !important;\n"
    style += f"\t--logo-size-mobile: 100px !important;\n"
    style += f"\t--sfabc-page-foreground: {page_foreground};\n"
    style += f"\t--sfabc-page-background: {page_background};\n"
    style += f"\t--sfabc-card-bg: {card_background};\n"
    style += f"\t--sfabc-carousel-bg: {carousel_background};\n"
    style += f"\t--sfabc-border-primary: {border_primary};\n"
    style += f"\t--sfabc-border-secondary: {border_secondary};\n"
    style += f"\t--sfabc-text-title: {text_title};\n"
    style += f"\t--sfabc-text-subtitle: {text_subtitle};\n"
    style += f"\t--sfabc-text-normal: {text_normal};\n"
    style += f"\t--sfabc-text-important: {text_important};\n"
    style += f"\t--sfabc-text-discreet: {text_discreet};\n"
    style += f"\t--sfabc-text-link: {text_link};\n"
    style += f"\t--sfabc-text-header: {text_header};\n"
    style += f"\t--sfabc-shadow: {shadow};\n"
    style += f"\t--sfabc-shadow-rgb: {shadow_rgb};\n"
    style += f"\t--sfabc-button: {button_color};\n"
    style += f"\t--sfabc-button-hover: {button_hover_color};\n"
    style += f'\t--sfabc-font: {police};\n'
    style += f"\t--bs-body-bg: var(--sfabc-page-background);\n"
    style += f"\t--bs-body-color: var(--sfabc-text-normal);\n"
    style += f"\t--bs-dark: var(--sfabc-text-normal);\n"
    style += f"\t--bs-dark-rgb: {page_foreground_rgb};\n"
    style += f'\t--bs-body-font-family: var(--sfabc-font);\n'
    style += "}\n"
    style += ".background-img {\n"
    style += f"\theight: {hauteur_bandeau}px;\n"
    style += "}\n"
    style += ".title {\n"
    style += f"\tbottom: calc(160px + {hauteur_bandeau/2}px + 0.5em);\n"
    style += "}\n"
    style += ".reponse {\n"
    style += f"\tborder-left: 4px solid var(--sfabc-border-secondary)\n"
    style += "}\n"

    
    menus = dict()

    try:
        produits = Produit.objects.select_related('famille').all()
        for produit in produits:
            if produit.famille and not menus.get(produit.famille.nom_famille):
                menus[produit.famille.nom_famille] = dict()
            if produit.famille:
                menus[produit.famille.nom_famille][produit.nom_produit] = produit.id_produit
    except OperationalError as e:
        logger.error(f"Database error loading products in context processor: {e}")

    sorted_menus = [(menu, sorted(submenus.items())) for menu, submenus in sorted(menus.items())]

    return {
        "site_style": style,
        "site_logo": logo,
        "site_bandeau": bandeau,
        "menus": sorted_menus
    }