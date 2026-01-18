from django.urls import path
from . import admin_views

app_name = "admin_produits"

urlpatterns = [
    path("", admin_views.produit_list, name="admin_produit_list"),
    path("add/", admin_views.produit_add, name="admin_produit_add"),
    path("images/", admin_views.image_produit_library, name="admin_produit_image_library"),
    path("images/api/", admin_views.image_produit_api, name="admin_produit_image_api"),
    path("images/image-form/", admin_views.produit_image_form, name="admin_produit_image_form"),
    path("images/<int:pk>/delete/", admin_views.image_produit_delete, name="admin_produit_image_delete"),
    path("images/<int:pk>/rename/", admin_views.image_produit_rename, name="admin_produit_image_rename"),
    path("<int:pk>/", admin_views.produit_edit, name="admin_produit_edit"),
    path("<int:pk>/delete/", admin_views.produit_delete, name="admin_produit_delete"),
    path("familles/", admin_views.famille_list, name="admin_famille_list"),
    path("familles/add/", admin_views.famille_add, name="admin_famille_add"),
    path("familles/<int:pk>/", admin_views.famille_edit, name="admin_famille_edit"),
    path("familles/<int:pk>/delete/", admin_views.famille_delete, name="admin_famille_delete"),
]
