from django.urls import path
from django.contrib.auth import views as auth_views

from .admin_views import (
    admin_dashboard,
    apropos_delete,
    apropos_edit,
    apropos_list,
    apropos_move,
    edit_site,
    image_api,
    image_delete,
    image_library,
    image_rename,
    logout_view,
    service_add,
    service_delete,
    service_edit,
    service_image_form,
    service_list,
    service_move,
    upload_image,
)

app_name = "admin_core"

urlpatterns = [
    # Login / Logout for admin area
    path("login/", auth_views.LoginView.as_view(template_name="admin/login.html"), name="admin_login"),
    path("logout/", logout_view, name="admin_logout"),

    path("", admin_dashboard, name="admin_dashboard"),
    path("site/", edit_site, name="admin_site_edit"),
    path("site/apropos/", apropos_list, name="admin_apropos_list"),
    path("site/apropos/add/", apropos_edit, name="admin_apropos_add"),
    path("site/apropos/<int:pk>/", apropos_edit, name="admin_apropos_edit"),
    path("site/apropos/<int:pk>/delete/", apropos_delete, name="admin_apropos_delete"),
    path("apropos/<int:pk>/move/<str:direction>/", apropos_move, name="admin_apropos_move"),
    path("site/services/", service_list, name="admin_service_list"),
    path("site/services/<int:pk>/move/<str:direction>/", service_move, name="admin_service_move"),
    path("site/services/<int:pk>/delete/", service_delete, name="admin_service_delete"),
    path("site/services/add/", service_add, name="admin_service_add"),
    path("site/services/<int:pk>/edit/", service_edit, name="admin_service_edit"),
    path("site/services/image-form/", service_image_form, name="admin_service_image_form"),
    path("images/", image_library, name="admin_image_library"),
    path("images/upload/", upload_image, name="admin_image_upload"),
    path("images/api/", image_api, name="admin_image_api"),
    path("images/<int:pk>/delete/", image_delete, name="admin_image_delete"),
    path("images/<int:pk>/rename/", image_rename, name="admin_image_rename"),
]
