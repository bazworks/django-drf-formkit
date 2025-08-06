from django.contrib.auth import get_user_model

from .models import SecureFile
from .serializers import SecureFileSerializer

User = get_user_model()


def create_secure_file(file_obj, description=None, user=None):
    """
    Create a SecureFile instance from a file object.

    Args:
        file_obj (File): The uploaded file object
        description (str, optional): File description
        user (User, optional): User who uploaded the file

    Returns:
        tuple: (SecureFile instance, error_dict)
            - If successful, returns (secure_file, None)
            - If failed, returns (None, error_dict)
    """
    # Prepare file data
    file_data = {
        "file": file_obj,
        "original_filename": file_obj.name,
        "content_type": file_obj.content_type,
        "file_size": file_obj.size,
        "description": description,
    }
    print("file_data:", file_data)

    # Create and validate using serializer
    serializer = SecureFileSerializer(data=file_data)

    print("serializer.valid():", serializer.is_valid())
    serializer.is_valid(raise_exception=True)

    # Save the file
    secure_file = serializer.save(uploaded_by=user)
    return secure_file, None
