from apps.core.models import Site
def style_processor(request):
    site = Site.objects.all().first()
    print(site.logo.image.url)
    style = ":root{"
    style += "--bs-body-bg: #f6f2e8 !important;"
    style += "}"
    return {
        "site_style": style
    }