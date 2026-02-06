from django.urls import path
from . import admin_views

app_name = "admin_reviews"

urlpatterns = [
    path("", admin_views.avis_list, name="admin_avis_list"),
    path("<int:pk>/repondre/", admin_views.avis_repondre, name="admin_avis_repondre"),
    path("<int:pk>/supprimer/", admin_views.avis_delete, name="admin_avis_delete"),
    path("reponse/<int:pk>/supprimer/", admin_views.reponse_delete, name="admin_reponse_delete"),
]
