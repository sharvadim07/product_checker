import minio
import os
from datetime import timedelta
import json
import urllib3
from io import BytesIO
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
    def fput_new_photo(self, file_path : str, user : str) -> minio.api.ObjectWriteResult:
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
            print(
                f"""\
                created {result.object_name} object;\
                etag: {result.etag}, version-id: {result.version_id}\
                """
            )
            return result
        except minio.S3Error as exc:
            print("error occurred.", exc)
    def put_new_photo(
            self, 
            image : BytesIO, 
            length : int,
            user : str, 
            object_name : str
        ) -> minio.api.ObjectWriteResult:
        try:
            tags = Tags(for_object=True)
            tags["User"] = user
            result = self._client.put_object(
                bucket_name = self._bucket_name,
                object_name = object_name,
                data = image,
                length = length,
                content_type = "application/photos",
                tags = tags
            )
            print(
                f"""
                created {result.object_name} object;
                etag: {result.etag}, version-id: {result.version_id}
                """
            )
            return result
        except minio.S3Error as exc:
            raise ValueError("minio.S3Error occurred.", exc)
    def put_new_bytearray_photo(
        self,
        bytearray_photo : bytearray, 
        user : str,
        object_name : str
    ) -> minio.api.ObjectWriteResult:
        # Upload photo to Minio
        try:
            # Convert the bytearray to a bytes object
            data_bytes = bytes(bytearray_photo)
            # Create a BytesIO object to read the bytes
            data_stream = BytesIO(data_bytes)
            minio_res = self.put_new_photo(
                data_stream,
                len(data_bytes),
                user,
                object_name
            )
            return minio_res
        except (AttributeError, TypeError, ValueError):
            raise ValueError("Something goes wrong while uploading byterrary photo to minio!")
    def get_object(self, object_name : str):
        try:
            # Get presigned URL string to download 'my-object' in
            # 'my-bucket' with two hours expiry.
            response = self._client.get_object(
                self._bucket_name,
                object_name,
            )
            return response
        except minio.S3Error as exc:
            print("error occurred.", exc)
            return
    def get_object_url(self, object_name : str) -> str:
        try:
            # Get presigned URL string to download 'my-object' in
            # 'my-bucket' with two hours expiry.
            url = self._client.get_presigned_url(
                "GET",
                self._bucket_name,
                object_name,
                expires = timedelta(hours=2),
            )
            print(url)
            return url
        except minio.S3Error as exc:
            print("error occurred.", exc)
            return ""
