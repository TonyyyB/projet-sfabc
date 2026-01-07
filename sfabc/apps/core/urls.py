from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.core.views import *

app_name = "core"

urlpatterns = [
    # Login / Logout for admin area
    path("admin/login/", auth_views.LoginView.as_view(template_name="admin/login.html"), name="admin_login"),
    path("admin/logout/", auth_views.LogoutView.as_view(next_page='core:admin_login'), name="admin_logout"),

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
    path("admin/apropos/<int:pk>/move/<str:direction>/", apropos_move, name="admin_apropos_move"),
    path("admin/site/services/", service_list, name="admin_service_list"),
    path("admin/site/services/<int:pk>/move/<str:direction>/", service_move, name="admin_service_move"),
    path("admin/site/services/<int:pk>/delete/", service_delete, name="admin_service_delete"),
    path("admin/site/services/add/", service_add, name="admin_service_add"),
    path("admin/site/services/<int:pk>/edit/", service_edit, name="admin_service_edit"),
    path("admin/images/", image_library, name="admin_image_library"),
    path("admin/images/api/", image_api, name="admin_image_api"),
    path("admin/images/<int:pk>/delete/", image_delete, name="admin_image_delete"),
    path("admin/images/<int:pk>/rename/", image_rename, name="admin_image_rename"),
]