from django.contrib import admin
from django.utils.html import mark_safe
from apps.core.models import A_Propos, Image_Site, Image_AP, Site,Service, Image_Service

# Register your models here.
admin.site.register(A_Propos)
admin.site.register(Site)
admin.site.register(Service)

@admin.register(Image_Site)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]
    
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

@admin.register(Image_AP)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]
    
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
    
@admin.register(Image_Service)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ["image_preview"]
    list_display = ["image_list"]
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url = obj.image.image.url,
                width=obj.image.image.width,
                height=obj.image.image.height,
            ))
        return "Pas d'image"
    image_preview.short_description = 'Preview'
    
    def image_list(self, obj):
        if obj.image:
            return mark_safe('<img src="{url}" style="max-width:200px; max-height:200px;" />'.format(
                url = obj.image.image.url,
            ))
        return "Pas d'image"