from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Text, DateTime, Index
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    language = Column(String, nullable=False, default="ja")
    agree_threshold = Column(Float, nullable=False, default=0.95)
    review_threshold = Column(Float, nullable=False, default=0.80)
    concurrency = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    audio_files = relationship("AudioFile", back_populates="project", cascade="all, delete-orphan")
    records = relationship("Record", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")


class AudioFile(Base):
    __tablename__ = "audio_files"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    original_name = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    duration_sec = Column(Float)
    size_bytes = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    error_message = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=now)

    project = relationship("Project", back_populates="audio_files")
    records = relationship("Record", back_populates="audio_file", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_audio_project", "project_id", "status"),
    )


class Record(Base):
    __tablename__ = "records"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    audio_file_id = Column(String, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    start_sec = Column(Float, nullable=False)
    end_sec = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    original_text = Column(Text, nullable=False)
    whisper_text = Column(Text, nullable=False)
    gemini_text = Column(Text, nullable=False)
    strategy = Column(String, nullable=False)
    similarity = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    cer = Column(Float, nullable=False)
    bucket = Column(String, nullable=False, default="train")
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=now, onupdate=now)

    project = relationship("Project", back_populates="records")
    audio_file = relationship("AudioFile", back_populates="records")
    edits = relationship("RecordEdit", back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_records_project_bucket", "project_id", "bucket"),
    )


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, default="queued")
    total_files = Column(Integer, nullable=False, default=0)
    processed = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    written = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)

    project = relationship("Project", back_populates="jobs")


class RecordEdit(Base):
    __tablename__ = "record_edits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String, ForeignKey("records.id", ondelete="CASCADE"), nullable=False)
    before_text = Column(Text, nullable=False)
    after_text = Column(Text, nullable=False)
    action = Column(String, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=False, default=now)

    record = relationship("Record", back_populates="edits")
