from django.urls import path

from . import views

app_name = "export"

urlpatterns = [
    path("", views.export_view, name="export"),
]
