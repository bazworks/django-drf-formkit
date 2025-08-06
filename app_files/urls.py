from django.urls import path

from .views import SecureFileViewSet

urlpatterns = [
    # List and create files
    path(
        "files/",
        SecureFileViewSet.as_view({"get": "list", "post": "create"}),
        name="file-list",
    ),
    # Retrieve, update and delete specific file
    path(
        "files/<str:slug>/",
        SecureFileViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="file-detail",
    ),
    # Generate download URL - presigned
    path(
        "files/<str:slug>/download/",
        SecureFileViewSet.as_view({"get": "download"}),
        name="file-download",
    ),
]
