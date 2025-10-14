from django.contrib import admin
from apps.core.models import A_Propos, Image, Site

# Register your models here.
admin.site.register(A_Propos)
admin.site.register(Image)
admin.site.register(Site)