from django.urls import path, include
from apps.core.views import *

app_name = "core"

urlpatterns = [
    path("", Home.as_view(), name="home"),
    path("a_propos/", AProposView.as_view(), name="a_propos"),
    path("contact/", ContactView.as_view(), name="contact"),
]