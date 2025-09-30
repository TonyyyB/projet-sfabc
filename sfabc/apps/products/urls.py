from django.urls import path, include

app_name = "products"

urlpatterns = [
    #TODO
    path("<int:pk>/avis/", include("apps.reviews.urls", namespace="reviews")),
]