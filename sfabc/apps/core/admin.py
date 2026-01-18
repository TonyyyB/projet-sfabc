from django.contrib import admin
from django.utils.html import mark_safe
from apps.core.models import A_Propos, Image_Site, Image_A_Propos, Site,Service, Image_Service


# Register your models here.
admin.site.register(A_Propos)
admin.site.register(Site)
admin.site.register(Service)

@admin.register(Image_Site)
class ImageAdmin(admin.ModelAdmin):
    """Configuration d'affichage admin pour Image_Site (prévisualisation + miniature)."""
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]
    
    def image_preview(self, obj):
        """Génère un HTML de prévisualisation (img) pour l'admin Django."""
        if obj.image:
            return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url = obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            ))
        return "Pas d'image"
    image_preview.short_description = 'Preview'
    
    def image_list(self, obj):
        """Affiche une ligne admin incluant le nom + une miniature de l'image."""
        if obj.image:
            return mark_safe('{string}<img src="{url}" style="max-width:200px; max-height:200px;" />'.format(
                string = str(obj),
                url = obj.image.url,
            ))
        return "Pas d'image"

@admin.register(Image_A_Propos)
class ImageAdmin(admin.ModelAdmin):
    """Configuration d'affichage admin pour Image_A_Propos (prévisualisation + miniature)."""
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]
    
    def image_preview(self, obj):
        """Génère un HTML de prévisualisation (img) pour l'image associée à une section "À propos"."""
        if obj.image:
            return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url = obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            ))
        return "Pas d'image"
    image_preview.short_description = 'Preview'
    
    def image_list(self, obj):
        """Affiche une ligne admin (texte + miniature) pour l'image liée à la section "À propos"."""
        if obj.image:
            return mark_safe('{string}<img src="{url}" style="max-width:200px; max-height:200px;" />'.format(
                string = str(obj),
                url = obj.image.image.url,
            ))
        return "Pas d'image"
    
@admin.register(Image_Service)
class ImageAdmin(admin.ModelAdmin):
    """Configuration d'affichage admin pour Image_Service (prévisualisation + miniature)."""
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]
    
    def image_preview(self, obj):
        """Génère un HTML de prévisualisation (img) pour l'image associée à un service."""
        if obj.image:
            return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url = obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            ))
        return "Pas d'image"
    image_preview.short_description = 'Preview'
    
    def image_list(self, obj):
        """Affiche une miniature pour l'image de service dans la liste admin."""
        if obj.image:
            return mark_safe('<img src="{url}" style="max-width:200px; max-height:200px;" />'.format(
                url = obj.image.image.url,
            ))
        return "Pas d'image"
