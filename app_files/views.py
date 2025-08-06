from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SecureFile
from .serializers import SecureFileSerializer


class SecureFileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing secure file uploads and downloads.
    """

    queryset = SecureFile.objects.all()
    serializer_class = SecureFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = "slug"

    def get_queryset(self):
        """Filter files based on user permissions."""
        return self.queryset.filter(uploaded_by=self.request.user)

    @extend_schema(
        description="Upload a new file to secure storage",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "description": {"type": "string"},
                },
                "required": ["file"],
            }
        },
    )
    def create(self, request, *args, **kwargs):
        """Handle file upload with validation."""
        if "file" not in request.FILES:
            raise ValidationError("No file provided")

        file_obj = request.FILES["file"]
        data = request.data.copy()
        # Add file metadata from the file object
        data["original_filename"] = file_obj.name
        data["content_type"] = file_obj.content_type
        data["file_size"] = file_obj.size

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["get"])
    def download(self, request, slug=None):
        """Generate a presigned download URL for the file."""
        instance = self.get_object()

        # Get disposition type from query params (default to attachment)
        disposition_type = request.query_params.get("disposition", "inline")
        # Validate disposition type
        if disposition_type not in ["attachment", "inline"]:
            disposition_type = "inline"

        url = instance.generate_presigned_url(
            expiration=300, disposition_type=disposition_type
        )
        if url:
            return Response(
                {
                    "download_url": url,
                    "filename": instance.original_filename,
                    "content_type": instance.content_type,
                }
            )

        raise APIException("Could not generate download URL")
