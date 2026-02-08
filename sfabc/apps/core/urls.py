from django.urls import path

from apps.core.views import AProposView, ContactConfirmationView, ContactView, Home, ServiceView

app_name = "core"

urlpatterns = [
    path("", Home.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("contact/confirmation/", ContactConfirmationView.as_view(), name="contact_confirmation"),
    path("a_propos/", AProposView.as_view(), name="a_propos"),
    path("services/", ServiceView.as_view(), name="services"),
]
