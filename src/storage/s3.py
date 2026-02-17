from __future__ import annotations

import logging

import boto3
from botocore.exceptions import ClientError

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.s3.bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3.endpoint_url,
            aws_access_key_id=settings.s3.access_key.get_secret_value(),
            aws_secret_access_key=settings.s3.secret_key.get_secret_value(),
            region_name=settings.s3.region,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info("Creating S3 bucket: %s", self.bucket)
            self.client.create_bucket(Bucket=self.bucket)

    def upload_bytes(self, key: str, data: bytes, content_type: str = "image/png") -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.debug("Uploaded %s (%d bytes)", key, len(data))
        return key

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_object(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def list_objects(self, prefix: str) -> list[str]:
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
