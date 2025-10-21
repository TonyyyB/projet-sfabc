from django.urls import path, include
from .views import *

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
]