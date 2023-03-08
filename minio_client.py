import minio
import os
import datetime
import json
import urllib3
urllib3.disable_warnings()
from minio.commonconfig import Tags

class MyMinioClient():
    def __init__(self, credentials : str = "data/credentials.json") -> None:
        try:
            with open (credentials, 'r') as f:
                credentials = json.load(f)
            self._client = minio.Minio(
                **credentials
            )
            self._bucket_name = "productphotos"
            # Make 'product_photos' bucket if not exist.
            found = self._client.bucket_exists(bucket_name = self._bucket_name)
            if not found:
                self._client.make_bucket(self._bucket_name)
            else:
                print(f"Bucket '{self._bucket_name}' already exists")
        except minio.S3Error as exc:
            print("error occurred.", exc)
    def put_new_photo(self, file_path : str, user : str) -> minio.api.ObjectWriteResult:
        try:
            object_name = f"{os.path.basename(file_path)}"
            tags = Tags(for_object=True)
            tags["User"] = user
            result = self._client.fput_object(
                bucket_name = self._bucket_name,
                object_name = object_name,
                file_path = file_path,
                content_type = "application/photos",
                tags = tags
            )
            print(f"created {result.object_name} object; \
                etag: {result.etag}, version-id: {result.version_id}")
            return result
        except minio.S3Error as exc:
            print("error occurred.", exc)
    def get_object_url(self, object_name : str) -> str:
        try:
            # Get presigned URL string to download 'my-object' in
            # 'my-bucket' with two hours expiry.
            url = self._client.get_presigned_url(
                "GET",
                self._bucket_name,
                object_name,
                expires = datetime.timedelta(hours=2),
            )
            print(url)
            return url
        except minio.S3Error as exc:
            print("error occurred.", exc)
            return ""
