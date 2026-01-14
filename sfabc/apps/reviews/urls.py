from django.urls import path, include
from .views import *

app_name = "reviews"

urlpatterns = [
    path("add/", add_review, name="add_review"),
    path("", ReviewListView.as_view(), name="liste_avis")
]