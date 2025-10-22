from django.urls import path, include
from .views import *

app_name = "core"

urlpatterns = [
    path("", Home.as_view(), name="home"),
]