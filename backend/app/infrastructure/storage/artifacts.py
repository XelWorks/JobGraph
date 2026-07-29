import io
import logging
import os
import uuid

from app.infrastructure.storage.minio import storage

logger = logging.getLogger("app.infrastructure.storage.artifacts")

def clean_filename(filename: str) -> str:
    """Strip path components and return a safe base filename."""
    base = os.path.basename(filename)
    # Remove any unwanted characters to prevent path traversal
    return "".join(c for c in base if c.isalnum() or c in "._-")

def save_tailored_resume(application_id: uuid.UUID, file_data: bytes, filename: str = "tailored_resume.pdf") -> str:
    """
    Saves a tailored resume to MinIO in a dedicated directory.
    Uses uuid nonces to prevent overwrite and directory traversal leaks.
    Returns the storage key/object name.
    """
    safe_name = clean_filename(filename)
    # Generate unique nonced object name
    object_name = f"resumes/{application_id}_{uuid.uuid4().hex[:8]}_{safe_name}"

    try:
        data_len = len(file_data)
        storage.put_object(
            object_name=object_name,
            data=io.BytesIO(file_data),
            length=data_len,
            content_type="application/pdf"
        )
        logger.info(
            "tailored_resume_stored",
            extra={
                "application_id": str(application_id),
                "object_name": object_name,
                "length": data_len
            }
        )
        return object_name
    except Exception as e:
        logger.error(f"failed_to_store_tailored_resume: {e}", extra={"application_id": str(application_id)})
        raise RuntimeError("Failed to store tailored resume in object storage.") from e

def save_cover_letter(application_id: uuid.UUID, file_data: bytes, filename: str = "cover_letter.pdf") -> str:
    """
    Saves a tailored cover letter to MinIO in a dedicated directory.
    Uses uuid nonces to prevent overwrite and directory traversal leaks.
    Returns the storage key/object name.
    """
    safe_name = clean_filename(filename)
    # Generate unique nonced object name
    object_name = f"cover_letters/{application_id}_{uuid.uuid4().hex[:8]}_{safe_name}"

    try:
        data_len = len(file_data)
        storage.put_object(
            object_name=object_name,
            data=io.BytesIO(file_data),
            length=data_len,
            content_type="application/pdf"
        )
        logger.info(
            "cover_letter_stored",
            extra={
                "application_id": str(application_id),
                "object_name": object_name,
                "length": data_len
            }
        )
        return object_name
    except Exception as e:
        logger.error(f"failed_to_store_cover_letter: {e}", extra={"application_id": str(application_id)})
        raise RuntimeError("Failed to store cover letter in object storage.") from e
