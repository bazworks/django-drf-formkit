import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from app_core.models import CoreModel
from app_files.storage import SecureFileStorage

User = get_user_model()


def get_file_path(instance, filename):
    """
    Generate file path using the slug and original file extension.
    The slug is guaranteed to be unique by CoreModel.
    """
    # Get the file extension from the original filename
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return f"{timezone.now():%Y/%m}/{instance.slug}.{ext}"


class SecureFile(CoreModel):
    """Model for storing secure file information and managing S3 uploads."""

    file = models.FileField(upload_to=get_file_path, storage=SecureFileStorage)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_files",
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Secure File"
        verbose_name_plural = "Secure Files"
        ordering = ["-dtm_created"]

    def __str__(self):
        return str(self.original_filename)

    def generate_presigned_url(self, expiration=300, disposition_type="attachment"):
        """
        Generate a presigned URL for secure file download or viewing.

        Args:
            expiration (int): URL expiration time in seconds (default: 1 hour)
            disposition_type (str): Either 'attachment' for download or 'inline' for viewing
        """
        try:
            s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_S3_REGION_NAME,
                aws_access_key_id=(
                    settings.AWS_ACCESS_KEY_ID
                    if hasattr(settings, "AWS_ACCESS_KEY_ID")
                    else None
                ),
                aws_secret_access_key=(
                    settings.AWS_SECRET_ACCESS_KEY
                    if hasattr(settings, "AWS_SECRET_ACCESS_KEY")
                    else None
                ),
            )

            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            storage = self.file.storage
            key = self.file.name
            if hasattr(storage, "location") and storage.location:
                key = f"{storage.location}/{key}"

            url = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": key,
                    "ResponseContentDisposition": f'{disposition_type}; filename="{self.original_filename}"',
                    "ResponseContentType": self.content_type,
                },
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def delete(self, *args, **kwargs):
        """Override delete to ensure file is deleted from S3."""
        if self.file:
            self.file.storage.delete(self.file.name)
        super().delete(*args, **kwargs)

    def clean(self):
        """Validate file size and type."""
        if self.file:
            # 100MB file size limit
            if self.file_size > 100 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 100MB.")

            # Add more validation as needed
            allowed_extensions = [
                ".pdf",
                ".doc",
                ".docx",
                ".txt",
                ".jpg",
                ".jpeg",
                ".png",
            ]
            ext = self.file.name.lower().split(".")[-1]
            if f".{ext}" not in allowed_extensions:
                raise ValidationError("File type not supported.")
