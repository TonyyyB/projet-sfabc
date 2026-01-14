from django.urls import path, include
from .views import *

app_name = "products"

urlpatterns = [
    path("", ProduitListView.as_view(), name="liste_produits"),
    path("<int:pk>/", DetailProduitView.as_view(), name="detail_produit"),
    path("<int:pk>/avis/", include("apps.reviews.urls", namespace="reviews")),
]