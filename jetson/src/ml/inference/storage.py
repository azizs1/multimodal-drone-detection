"""RustFS/S3 storage helpers for inference snapshots."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from urllib.parse import quote

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class UploadURLs:
    rgb: str | None = None
    thermal: str | None = None


class RustFSStorage:
    """Handles bucket bootstrap and annotated frame uploads to RustFS."""

    def __init__(
        self,
        endpoint: str,
        public_base_url: str,
        bucket: str,
        access_key: str | None,
        secret_key: str | None,
        region: str,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.public_base_url = public_base_url.rstrip("/")
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self._client = self._build_client(signed=bool(self.access_key and self.secret_key))
        self._fallback_client = self._build_client(signed=False)

    @classmethod
    def from_env(cls) -> RustFSStorage:
        return cls(
            endpoint=os.getenv("RUSTFS_ENDPOINT", "http://rustfs:9000"),
            public_base_url=os.getenv("RUSTFS_PUBLIC_BASE_URL", "http://localhost:9000"),
            bucket=os.getenv("RUSTFS_BUCKET", "drone-detection"),
            access_key=os.getenv("RUSTFS_ACCESS_KEY"),
            secret_key=os.getenv("RUSTFS_SECRET_KEY"),
            region=os.getenv("RUSTFS_REGION", "us-east-1"),
        )

    def _build_client(self, signed: bool):
        try:
            import boto3
            from botocore import UNSIGNED
            from botocore.client import Config as BotoConfig
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError("boto3 is required for RustFS uploads.") from exc

        s3_config: dict[str, object] = {"s3": {"addressing_style": "path"}}
        if signed and self.access_key and self.secret_key:
            logger.info(
                "RustFS client init endpoint=%s bucket=%s auth=signed region=%s",
                self.endpoint,
                self.bucket,
                self.region,
            )
            return boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=BotoConfig(**s3_config),
            )

        # Anonymous/unsigned mode for local RustFS variants.
        logger.info(
            "RustFS client init endpoint=%s bucket=%s auth=unsigned region=%s",
            self.endpoint,
            self.bucket,
            self.region,
        )
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            region_name=self.region,
            config=BotoConfig(signature_version=UNSIGNED, **s3_config),
        )

    def _call_s3(self, method_name: str, **kwargs):
        method = getattr(self._client, method_name)
        try:
            return method(**kwargs)
        except Exception as exc:
            logger.warning(
                "RustFS primary call failed method=%s err=%r; trying unsigned fallback",
                method_name,
                exc,
            )
            fallback_method = getattr(self._fallback_client, method_name)
            return fallback_method(**kwargs)

    def ensure_bucket_public(self) -> None:
        if os.getenv("RUSTFS_SKIP_BOOTSTRAP", "false").lower() == "true":
            logger.info("RustFS bootstrap skipped by config for bucket=%s", self.bucket)
            return

        logger.info("RustFS ensure bucket start bucket=%s", self.bucket)
        try:
            self._call_s3("head_bucket", Bucket=self.bucket)
            logger.info("RustFS bucket already exists bucket=%s", self.bucket)
        except Exception as exc:
            logger.warning(
                "RustFS head_bucket failed; attempting create bucket=%s err=%r", self.bucket, exc
            )
            self._call_s3("create_bucket", Bucket=self.bucket)
            logger.info("RustFS bucket created bucket=%s", self.bucket)

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
                }
            ],
        }
        self._call_s3("put_bucket_policy", Bucket=self.bucket, Policy=json.dumps(policy))
        logger.info("RustFS bucket policy applied bucket=%s", self.bucket)

        probe_enabled = os.getenv("RUSTFS_STARTUP_PROBE", "true").lower() == "true"
        if probe_enabled:
            probe_key = "_healthcheck/startup-probe.txt"
            self._call_s3(
                "put_object",
                Bucket=self.bucket,
                Key=probe_key,
                Body=b"ok",
                ContentType="text/plain",
            )
            logger.info("RustFS startup probe succeeded bucket=%s key=%s", self.bucket, probe_key)

    def upload_detection_images(
        self,
        timestamp: float,
        rgb_frame,
        thermal_frame,
    ) -> UploadURLs:
        ts_ms = int(timestamp * 1000)
        rgb_key = f"detections/{ts_ms}/rgb.jpg"
        thermal_key = f"detections/{ts_ms}/thermal.jpg"

        rgb_url = self._upload_jpeg(rgb_key, rgb_frame)
        thermal_url = self._upload_jpeg(thermal_key, thermal_frame)
        return UploadURLs(rgb=rgb_url, thermal=thermal_url)

    def upload_detection_image_bytes(
        self,
        timestamp: float,
        modality: str,
        jpeg_bytes: bytes,
    ) -> str | None:
        ts_ms = int(timestamp * 1000)
        key = f"detections/{ts_ms}/{modality}.jpg"
        return self._upload_jpeg_bytes(key=key, jpeg_bytes=jpeg_bytes)

    def _upload_jpeg(self, key: str, frame) -> str | None:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError("opencv-python is required for JPEG encoding.") from exc

        quality = int(os.getenv("RUSTFS_JPEG_QUALITY", "90"))
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            logger.warning("RustFS jpeg encode failed key=%s", key)
            return None

        return self._upload_jpeg_bytes(key=key, jpeg_bytes=encoded.tobytes())

    def _upload_jpeg_bytes(self, key: str, jpeg_bytes: bytes) -> str | None:
        self._call_s3(
            "put_object",
            Bucket=self.bucket,
            Key=key,
            Body=jpeg_bytes,
            ContentType="image/jpeg",
        )
        public_url = f"{self.public_base_url}/{self.bucket}/{quote(key)}"
        logger.info("RustFS upload succeeded key=%s url=%s", key, public_url)
        return public_url
