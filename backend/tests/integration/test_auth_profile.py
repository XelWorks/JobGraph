import io
import uuid

import pytest
from app.domain.auth import User
from app.domain.profile import UserProfile
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.storage.minio import storage
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import delete


@pytest.mark.asyncio
async def test_complete_auth_profile_integration():
    """
    Integration Test:
    1. Register a new candidate.
    2. Retrieve hashed password from DB to verify Argon2 hashing is active.
    3. Authenticate/login to obtain JWT token.
    4. Create/update profile details.
    5. Upload resume PDF to MinIO.
    6. Verify PDF exists in S3/MinIO bucket.
    7. Clean up all created database models and MinIO files.
    """
    # Unique test email to prevent duplication conflicts
    test_id = uuid.uuid4().hex[:8]
    email = f"integration_candidate_{test_id}@example.com"
    password = "SuperSecurePassword123!"

    with TestClient(app) as client:
        # Step 1: Register User
        register_payload = {
            "email": email,
            "password": password,
            "first_name": "Integration",
            "last_name": "Tester"
        }
        reg_resp = client.post("/api/v1/auth/register", json=register_payload)
        assert reg_resp.status_code == 201
        user_id = uuid.UUID(reg_resp.json()["id"])

        # Step 2: Database validation (Verify password is not plaintext and hashed with Argon2id)
        async with SessionLocal() as session:
            db_user = await session.get(User, user_id)
            assert db_user is not None
            assert db_user.email == email
            assert db_user.hashed_password != password
            assert db_user.hashed_password.startswith("$argon2id$")

        # Step 3: Login to obtain JWT
        login_payload = {
            "email": email,
            "password": password
        }
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 4: Create/Update Profile
        profile_payload = {
            "phone": "+1 (555) 987-6543",
            "preferred_roles": ["Full Stack Architect", "Principal Engineer"],
            "preferred_locations": ["Remote", "London", "Austin"],
            "target_salary": 185000,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "MinIO"]
        }
        profile_resp = client.post("/api/v1/profile", json=profile_payload, headers=headers)
        assert profile_resp.status_code == 200
        profile_data = profile_resp.json()
        assert profile_data["phone"] == "+1 (555) 987-6543"
        assert profile_data["target_salary"] == 185000
        assert "Python" in profile_data["skills"]

        # Step 5: Upload Resume PDF to MinIO
        resume_name = f"resume_{test_id}.pdf"
        dummy_pdf_content = b"%PDF-1.4 mock integration test pdf content"
        file_payload = {"file": (resume_name, io.BytesIO(dummy_pdf_content), "application/pdf")}

        upload_resp = client.post("/api/v1/profile/resume", files=file_payload, headers=headers)
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert upload_data["master_resume_url"] is not None
        assert resume_name in upload_data["master_resume_url"]

        # Step 6: Verify file exists in MinIO
        async with SessionLocal() as session:
            from sqlalchemy import select
            # Query by user_id
            profile_query = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            db_profile = profile_query.scalar_one_or_none()
            assert db_profile is not None
            assert db_profile.master_resume_key is not None

            # Assert file exists inside local MinIO storage
            exists = storage.client.bucket_exists(storage.bucket_name)
            assert exists is True

            # Stat the object directly to verify it was written
            stat = storage.client.stat_object(storage.bucket_name, db_profile.master_resume_key)
            assert stat.size == len(dummy_pdf_content)
            assert stat.content_type == "application/pdf"

            # Retrieve master key for deletion cleanup
            resume_key = db_profile.master_resume_key
            profile_record_id = db_profile.id

        # Step 7: Clean up all created database models and MinIO files (Teardown)
        # Delete resume object from MinIO
        storage.client.remove_object(storage.bucket_name, resume_key)

        # Delete models from Postgres database
        async with SessionLocal() as session:
            # Cascades delete skills and experiences automatically due to ondelete="CASCADE"
            await session.execute(delete(UserProfile).where(UserProfile.id == profile_record_id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()

            # Verify records are deleted completely
            deleted_user = await session.get(User, user_id)
            profile_query_deleted = await session.execute(
                select(UserProfile).where(UserProfile.id == profile_record_id)
            )
            deleted_profile = profile_query_deleted.scalar_one_or_none()
            assert deleted_user is None
            assert deleted_profile is None
