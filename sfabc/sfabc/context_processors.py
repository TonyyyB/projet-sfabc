from apps.core.models import Site
from django.templatetags.static import static
def style_processor(request):
    site = Site.objects.first()
    body_bg = "#f6f2e8"
    body_fg = "#B8A67E"
    police = "Liberation Sans"
    logo = static("images/logo.png")
    bandeau = static("image/bois.jpg")
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
    
    return {
        "site_style": style,
        "site_logo": logo,
        "site_bandeau": bandeau
    }