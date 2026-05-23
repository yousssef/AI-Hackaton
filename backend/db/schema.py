from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class PostingORM(Base):
    __tablename__ = "postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(64), nullable=False)
    source_url = Column(String(512), nullable=False)
    external_id = Column(String(256), nullable=False)
    company = Column(String(256))
    company_domain = Column(String(256))
    title = Column(String(512))
    description = Column(Text)
    location_raw = Column(String(256))
    remote_type = Column(String(64))
    role_family = Column(String(64))
    posted_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    verification = relationship("VerificationORM", back_populates="posting", uselist=False)
    feedback = relationship("FeedbackORM", back_populates="posting")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
    )


class VerificationORM(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    posting_id = Column(Integer, ForeignKey("postings.id"), nullable=False, unique=True)
    trust_score = Column(Integer)
    genuinely_remote = Column(Boolean)
    remote_confidence = Column(Float)
    scam_likelihood = Column(Float)
    scam_reasons = Column(Text)           # JSON array stored as text
    role_clarity = Column(Float)
    employer_legitimacy_signals = Column(Text)   # JSON array
    newcomer_friendly_signals = Column(Text)     # JSON array
    rationale = Column(Text)
    llm_response_json = Column(Text)
    classifier_version = Column(String(32), default="1.0")
    verified_at = Column(DateTime, default=datetime.utcnow)

    posting = relationship("PostingORM", back_populates="verification")


class FeedbackORM(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    posting_id = Column(Integer, ForeignKey("postings.id"), nullable=False)
    user_id = Column(String(256), default="anonymous")
    signal = Column(String(16))   # "up" | "down"
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    posting = relationship("PostingORM", back_populates="feedback")


def create_tables(engine):
    Base.metadata.create_all(bind=engine)
