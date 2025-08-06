from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import status
from rest_framework.response import Response

API_PREFIX = getattr(settings, "API_PREFIX", "api")
print(API_PREFIX)

urlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns += [
    path(f"{API_PREFIX}/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        f"{API_PREFIX}/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

urlpatterns += [
    path(f"{API_PREFIX}/auth/", include("app_auth.urls")),
    path(f"{API_PREFIX}/files/", include("app_files.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
