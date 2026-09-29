from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AreaReport(Base):
    __tablename__ = "area_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    locality_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    area_name: Mapped[str] = mapped_column(String(160), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    fitness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    highlights: Mapped[list] = mapped_column(JSON, nullable=False)
    risks: Mapped[list] = mapped_column(JSON, nullable=False)
    data_source: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PropertyRecord(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    locality_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    area_name: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    property_area_sqft: Mapped[int] = mapped_column(Integer, nullable=False)
    frontage_m: Mapped[int] = mapped_column(Integer, nullable=False)
    road_width_m: Mapped[int] = mapped_column(Integer, nullable=False)
    parking_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    visibility: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[str] = mapped_column(String(40), nullable=False)
    notes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="SCOUTED")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strengths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    risks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recommendation: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CatchmentRequest(Base):
    __tablename__ = "catchment_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    locality_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    area_name: Mapped[str] = mapped_column(String(160), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SurveyAssignment(Base):
    __tablename__ = "survey_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    catchment_request_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    survey_executive: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="ASSIGNED")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
