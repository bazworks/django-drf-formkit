from storages.backends.s3boto3 import S3Boto3Storage


class SecureFileStorage(S3Boto3Storage):
    """
    Custom storage class for secure files using S3
    """

    location = "secure_files"  # creates a folder in your bucket
    file_overwrite = False
    default_acl = "private"

    def get_accessed_time(self, name):
        return None

    def get_created_time(self, name):
        return None

    def path(self, name):
        raise NotImplementedError("S3 storage does not support path()")
