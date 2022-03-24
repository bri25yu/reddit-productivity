from django.contrib import admin
from django.urls import path

import annotate.views as views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("annotate", views.AnnotateView.as_view(), name="annotate"),
    path("aggregate", views.aggregate, name="aggregate"),
]
