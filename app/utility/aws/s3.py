import logging
import re
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.utility.config import get_settings

# Configure an S3 lifecycle rule on prefix "staging/" to expire uncommitted uploads.
AWS_REGION = "us-east-1"
AWS_BUCKET_NAME = "print-preowned"
AWS_EXPIRATION = 3000
STAGING_PREFIX = "staging/"
BOOKS_PREFIX = "books/"

FILE_TYPE_CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "jp2": "image/jp2",
}

ALLOWED_FILE_TYPES = frozenset(FILE_TYPE_CONTENT_TYPES.keys())

STAGING_KEY_PATTERN = re.compile(
    r"^staging/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/(?:jpg|jpeg|png|jp2)$"
)


def _s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    )


def validate_file_type(file_type: str) -> str:
    normalized = file_type.lower()
    if normalized not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: jpg, jpeg, png, jp2",
        )
    return normalized


def content_type_for_file_type(file_type: str) -> str:
    return FILE_TYPE_CONTENT_TYPES[validate_file_type(file_type)]


def _assets_cdn_base() -> str | None:
    return get_settings().assets_cdn_url


def create_object_url(object_name: str) -> str:
    cdn_base = _assets_cdn_base()
    if not cdn_base:
        raise HTTPException(
            status_code=500,
            detail="ASSETS_CDN_URL is not configured",
        )
    return f"{cdn_base}/{object_name}"


def staging_object_key(file_type: str) -> str:
    upload_id = str(uuid.uuid4())
    return f"{STAGING_PREFIX}{upload_id}/{validate_file_type(file_type)}"


def book_cover_object_key(book_id: str, file_type: str) -> str:
    ext = validate_file_type(file_type)
    if ext == "jpeg":
        ext = "jpg"
    return f"{BOOKS_PREFIX}{book_id}/cover.{ext}"


def validate_staging_key(image_key: str) -> None:
    if ".." in image_key or not STAGING_KEY_PATTERN.match(image_key):
        raise HTTPException(status_code=400, detail="Invalid staged image")


def staging_key_from_image(image: str) -> str | None:
    key = object_key_from_url(image)
    if key is None or not STAGING_KEY_PATTERN.match(key):
        return None
    return key


def resolve_persisted_book_image(
    image: str,
    book_id: str,
    *,
    old_image: str | None = None,
) -> str:
    staging_key = staging_key_from_image(image)
    if staging_key is None:
        return image

    final_image = promote_staging_to_book(staging_key, book_id)
    if old_image:
        delete_replaced_book_cover(old_image, final_image, book_id)
    return final_image


def file_type_from_staging_key(image_key: str) -> str:
    return image_key.rsplit("/", 1)[-1]


def create_presigned_upload_url(object_name: str, file_type: str):
    content_type = content_type_for_file_type(file_type)
    s3_client = _s3_client()
    try:
        return s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": AWS_BUCKET_NAME,
                "Key": object_name,
                "ContentType": content_type,
            },
            ExpiresIn=AWS_EXPIRATION,
        )
    except ClientError as e:
        logging.error(e)
        return None


def promote_staging_to_book(image_key: str, book_id: str) -> str:
    validate_staging_key(image_key)
    file_type = file_type_from_staging_key(image_key)
    dest_key = book_cover_object_key(book_id, file_type)
    s3_client = _s3_client()

    try:
        s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=image_key)
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=400, detail="Staged image not found") from e

    try:
        s3_client.copy_object(
            Bucket=AWS_BUCKET_NAME,
            CopySource={"Bucket": AWS_BUCKET_NAME, "Key": image_key},
            Key=dest_key,
            ContentType=content_type_for_file_type(file_type),
            MetadataDirective="REPLACE",
        )
        s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=image_key)
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Failed to promote image") from e

    return create_object_url(dest_key)


def delete_object_if_exists(object_key: str) -> None:
    s3_client = _s3_client()
    try:
        s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=object_key)
    except ClientError as e:
        logging.error(e)


def object_key_from_url(image_url: str) -> str | None:
    s3_prefix = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/"
    if image_url.startswith(s3_prefix):
        return image_url[len(s3_prefix) :]

    cdn_base = _assets_cdn_base()
    if cdn_base and image_url.startswith(f"{cdn_base}/"):
        return image_url[len(cdn_base) + 1 :]

    return None


def delete_replaced_book_cover(old_image_url: str, new_image_url: str, book_id: str) -> None:
    if old_image_url == new_image_url:
        return

    old_key = object_key_from_url(old_image_url)
    new_key = object_key_from_url(new_image_url)
    if old_key is None or new_key is None:
        return

    expected_prefix = f"{BOOKS_PREFIX}{book_id}/"
    if old_key.startswith(expected_prefix) and old_key != new_key:
        delete_object_if_exists(old_key)
