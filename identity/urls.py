from django.urls import path

from . import views

urlpatterns = [
    path("", views.identify, name="identify-post"),
]