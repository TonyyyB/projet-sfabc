from django.contrib import admin
from apps.core.models import A_Propos, Image, Image_AP, Site

# Register your models here.
admin.site.register(A_Propos)
admin.site.register(Image)
admin.site.register(Site)
admin.site.register(Image_AP)
