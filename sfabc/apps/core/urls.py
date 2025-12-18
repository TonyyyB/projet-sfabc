from django.urls import path, include
from apps.core.views import *

app_name = "core"

urlpatterns = [
    path("", Home.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("a_propos/", AProposView.as_view(), name="a_propos"),
    path("services/", ServiceView.as_view(), name="services"),
    path("admin/", admin_dashboard, name="admin_dashboard"),
    path("admin/site/", edit_site, name="admin_site_edit"),
    path("admin/site/apropos/", apropos_list, name="admin_apropos_list"),
    path("admin/site/apropos/add/", apropos_edit, name="admin_apropos_add"),
    path("admin/site/apropos/<int:pk>/", apropos_edit, name="admin_apropos_edit"),
    path("admin/site/apropos/<int:pk>/delete/", apropos_delete, name="admin_apropos_delete"),
    path(
        "admin/apropos/<int:pk>/move/<str:direction>/",
        apropos_move,
        name="admin_apropos_move",
    ),
]