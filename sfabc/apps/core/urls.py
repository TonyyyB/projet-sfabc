from django.urls import path, include
from .views import *

app_name = "core"

urlpatterns = [
    path("", Home.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("a_propos/", AProposView.as_view(), name="a_propos")
]