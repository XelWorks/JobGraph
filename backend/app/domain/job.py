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

