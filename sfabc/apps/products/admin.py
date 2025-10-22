from django.contrib import admin
from django.utils.html import mark_safe
from apps.products.models import * 

# Register your models here.
admin.site.register(Famille)
admin.site.register(Produit)

@admin.register(Image_Produit)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ["image_preview"]
    list_display = ["desc_produit","image_list"]
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url = obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            ))
        return "Pas d'image"
    image_preview.short_description = 'Preview'
    
    def image_list(self, obj):
        if obj.image:
            return mark_safe('<img src="{url}" style="max-width:200px; max-height:200px;" />'.format(
                url = obj.image.url,
            ))
        return "Pas d'image"
    
    def desc_produit(self, obj):
        return str(obj.produit)