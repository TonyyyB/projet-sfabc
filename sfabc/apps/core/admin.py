from django.contrib import admin
from django.utils.html import mark_safe
from apps.core.models import A_Propos, Image_A_Propos, Image_Service, Image_Site, Service, Site


# Register your models here.
admin.site.register(A_Propos)
admin.site.register(Site)
admin.site.register(Service)

@admin.register(Image_Site)
class ImageSiteAdmin(admin.ModelAdmin):
    """Configuration d'affichage admin pour Image_Site (prévisualisation + miniature)."""
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]

    def image_preview(self, obj):
        """Génère un HTML de prévisualisation (img) pour l'admin Django."""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="{obj.image.width}" height="{obj.image.height}" />'
            )
        return "Pas d'image"
    image_preview.short_description = 'Preview'

    def image_list(self, obj):
        """Affiche une ligne admin incluant le nom + une miniature de l'image."""
        if obj.image:
            return mark_safe(
                f'{obj}<img src="{obj.image.url}" style="max-width:200px; max-height:200px;" />'
            )
        return "Pas d'image"

@admin.register(Image_A_Propos)
class ImageAProposAdmin(admin.ModelAdmin):
    """Configuration d'affichage admin pour Image_A_Propos (prévisualisation + miniature)."""
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]

    def image_preview(self, obj):
        """Génère un HTML de prévisualisation (img) pour l'image associée à une section "À propos"."""
        if obj.image and obj.image.image:
            return mark_safe(
                f'<img src="{obj.image.image.url}" width="{obj.image.image.width}" height="{obj.image.image.height}" />'
            )
        return "Pas d'image"
    image_preview.short_description = 'Preview'

    def image_list(self, obj):
        """Affiche une ligne admin (texte + miniature) pour l'image liée à la section "À propos"."""
        if obj.image and obj.image.image:
            return mark_safe(
                f'{obj}<img src="{obj.image.image.url}" style="max-width:200px; max-height:200px;" />'
            )
        return "Pas d'image"

@admin.register(Image_Service)
class ImageServiceAdmin(admin.ModelAdmin):
    """Configuration d'affichage admin pour Image_Service (prévisualisation + miniature)."""
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]

    def image_preview(self, obj):
        """Génère un HTML de prévisualisation (img) pour l'image associée à un service."""
        if obj.image and obj.image.image:
            return mark_safe(
                f'<img src="{obj.image.image.url}" width="{obj.image.image.width}" height="{obj.image.image.height}" />'
            )
        return "Pas d'image"
    image_preview.short_description = 'Preview'

    def image_list(self, obj):
        """Affiche une miniature pour l'image de service dans la liste admin."""
        if obj.image and obj.image.image:
            return mark_safe(
                f'<img src="{obj.image.image.url}" style="max-width:200px; max-height:200px;" />'
            )
        return "Pas d'image"
