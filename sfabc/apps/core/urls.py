from django.urls import path, include
from .views import *

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("a_propos/", AProposView.as_view(), name="a_propos")
]