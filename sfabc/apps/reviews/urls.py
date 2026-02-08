from django.urls import path

from .views import ReviewListView, add_review, add_reply

app_name = "reviews"

urlpatterns = [
    path("add/", add_review, name="add_review"),
    path("reply/<int:avis_id>/", add_reply, name="add_reply"),
    path("", ReviewListView.as_view(), name="liste_avis"),
]
