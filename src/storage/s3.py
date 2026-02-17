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
        self.region = settings.s3.region
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3.endpoint_url,
            aws_access_key_id=settings.s3.access_key.get_secret_value(),
            aws_secret_access_key=settings.s3.secret_key.get_secret_value(),
            region_name=self.region,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                logger.info("Creating S3 bucket: %s", self.bucket)
                create_kwargs: dict[str, object] = {"Bucket": self.bucket}
                if self.region != "us-east-1":
                    create_kwargs["CreateBucketConfiguration"] = {
                        "LocationConstraint": self.region,
                    }
                self.client.create_bucket(**create_kwargs)
            else:
                raise

    def upload_bytes(self, key: str, data: bytes, content_type: str = "image/png") -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            ContentDisposition=f'inline; filename="{key.rsplit("/", 1)[-1]}"',
        )
        logger.debug("Uploaded %s (%d bytes)", key, len(data))
        return key

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(  # type: ignore[no-any-return]
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_object(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def list_objects(self, prefix: str) -> list[str]:
        """List all objects under prefix using paginator."""
        paginator = self.client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys
