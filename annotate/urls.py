from django.contrib import admin
from django.urls import path

import annotate.views as views


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.index, name="index"),
    path("annotate", views.annotate, name="annotate"),
]
