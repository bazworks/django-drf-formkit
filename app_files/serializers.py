from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import SecureFile


class SecureFileSerializer(serializers.ModelSerializer):
    file_download_url = serializers.SerializerMethodField()

    class Meta:
        model = SecureFile
        fields = [
            "id",
            "slug",
            "file",
            "original_filename",
            "content_type",
            "file_size",
            "description",
            "file_download_url",
        ]
        read_only_fields = ["id", "slug"]

    @extend_schema_field(OpenApiTypes.URI)
    def get_file_download_url(self, obj):
        """Generate a presigned download URL for the file."""
        # Get disposition type from context, default to inline
        disposition_type = self.context.get("disposition_type", "inline")
        return obj.generate_presigned_url(disposition_type=disposition_type)

    def create(self, validated_data):
        """Override create to set additional fields."""
        request = self.context.get("request")
        if request and request.user:
            validated_data["uploaded_by"] = request.user

        # Set file size and original filename
        file = validated_data.get("file")
        if file:
            validated_data["file_size"] = file.size
            validated_data["original_filename"] = file.name

        return super().create(validated_data)
