from django.urls import path
from . import admin_views

app_name = "admin_produits"

urlpatterns = [
    path("", admin_views.produit_list, name="admin_produit_list"),
    path("add/", admin_views.produit_add, name="admin_produit_add"),
    path("images/api/", admin_views.image_produit_api, name="admin_produit_image_api"),
    path("<int:pk>/", admin_views.produit_edit, name="admin_produit_edit"),
    path("<int:pk>/delete/", admin_views.produit_delete, name="admin_produit_delete"),
    path("familles/", admin_views.famille_list, name="admin_famille_list"),
    path("familles/add/", admin_views.famille_add, name="admin_famille_add"),
    path("familles/<int:pk>/", admin_views.famille_edit, name="admin_famille_edit"),
]