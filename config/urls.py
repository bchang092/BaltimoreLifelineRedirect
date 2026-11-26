from django.contrib import admin
from django.urls import path
from inquiries.views import luma_home, luma_about

urlpatterns = [path("", luma_home, name="luma_home"), path("about/", luma_about, name="luma_about"), path("admin/", admin.site.urls)]
