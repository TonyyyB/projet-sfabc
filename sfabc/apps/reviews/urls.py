from django.urls import path, include
from .views import *

app_name = "reviews"

urlpatterns = [
    path("", ReviewListView.as_view(), name="liste_avis")
]