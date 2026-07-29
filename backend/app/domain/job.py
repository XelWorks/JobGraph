import uuid
from datetime import datetime

from app.infrastructure.db.session import Base
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False  # e.g., "Greenhouse" or "Lever"
    )
    external_job_id: Mapped[str] = mapped_column(
        String(100), nullable=False  # Key used to uniquely map at the source ATS
    )
    board_token: Mapped[str] = mapped_column(
        String(100), nullable=False  # Identifies the corporate board searched
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    company: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    location: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    url: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )
    description_text: Mapped[str | None] = mapped_column(
        String(20000), nullable=True
    )
    raw_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationship
    match_score: Mapped["MatchScore | None"] = relationship(
        "MatchScore", back_populates="job_posting", cascade="all, delete-orphan", lazy="selectin"
    )


class MatchScore(Base):
    __tablename__ = "match_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_score: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_score: Mapped[int] = mapped_column(Integer, nullable=False)
    location_score: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_score: Mapped[int] = mapped_column(Integer, nullable=False)
    is_archived: Mapped[bool] = mapped_column(default=False, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    job_posting: Mapped["JobPosting"] = relationship("JobPosting", back_populates="match_score")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="Backlog", nullable=False  # "Backlog", "Scheduled", "Auto-Filled", "Submitted", "Failed"
    )
    mode: Mapped[str] = mapped_column(
        String(50), default="Manual", nullable=False  # "Manual", "Assisted", "Autonomous"
    )
    tailored_resume_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    cover_letter_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    tailored_resume_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )
    tailored_cover_letter_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )
    date_applied: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    notes: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    job_posting: Mapped["JobPosting"] = relationship("JobPosting", lazy="selectin")


