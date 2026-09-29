from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.area_analysis import LOCALITIES
from app.database import get_db
from app.models import PropertyRecord

router = APIRouter(prefix="/api", tags=["property pipeline"])


class PropertyCreateRequest(BaseModel):
    locality_id: str
    address: str
    latitude: float
    longitude: float
    monthly_rent: int
    property_area_sqft: int
    frontage_m: int
    road_width_m: int
    parking_slots: int = 0
    visibility: int = 5
    condition: str = "average"
    notes: str = ""


class PropertyStatusUpdate(BaseModel):
    status: str
    note: str | None = None


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locality_id: str
    area_name: str
    address: str
    latitude: float
    longitude: float
    monthly_rent: int
    property_area_sqft: int
    frontage_m: int
    road_width_m: int
    parking_slots: int
    visibility: int
    condition: str
    notes: str
    status: str
    score: int
    strengths: list[str]
    risks: list[str]
    recommendation: str
    created_at: datetime


def _evaluate_property(payload: dict[str, Any]) -> tuple[int, list[str], list[str], str]:
    score = 0
    strengths: list[str] = []
    risks: list[str] = []

    area = payload["property_area_sqft"]
    if area >= 1400:
        score += 22
        strengths.append("Large operating footprint")
    elif area >= 900:
        score += 15
        strengths.append("Moderate unit size")
    else:
        risks.append("Small unit may limit merchandise mix")

    rent = payload["monthly_rent"]
    if rent <= 450000:
        score += 18
        strengths.append("Rent is within a healthy range")
    elif rent <= 700000:
        score += 10
        strengths.append("Rent is manageable for volume-led trade")
    else:
        risks.append("High rent may compress operating margin")

    frontage = payload["frontage_m"]
    if frontage >= 14:
        score += 18
        strengths.append("Strong frontage supports visibility")
    elif frontage >= 8:
        score += 10
    else:
        risks.append("Limited frontage can reduce street visibility")

    road = payload["road_width_m"]
    if road >= 10:
        score += 12
        strengths.append("Good road width supports easy access")
    elif road >= 6:
        score += 6
    else:
        risks.append("Narrow access may slow customer movement")

    parking = payload["parking_slots"]
    if parking >= 2:
        score += 12
        strengths.append("Parking access improves convenience")
    elif parking >= 1:
        score += 8
    else:
        risks.append("Limited parking can reduce conversion")

    visibility = payload["visibility"]
    if visibility >= 8:
        score += 10
        strengths.append("Visibility is strong for brand impact")
    elif visibility >= 5:
        score += 6
    else:
        risks.append("Low visibility may reduce walk-in traffic")

    condition = str(payload["condition"]).casefold()
    if condition in {"good", "excellent"}:
        score += 8
        strengths.append("Condition supports faster market readiness")
    else:
        risks.append("Condition needs review before launch")

    score = max(0, min(100, score))

    if score >= 80:
        recommendation = "Strong candidate for next-stage review"
    elif score >= 60:
        recommendation = "Promising but validate with field and catchment data"
    else:
        recommendation = "Low fit unless pricing or access improves"

    return score, strengths, risks, recommendation


@router.get("/properties", response_model=list[PropertyResponse])
def list_properties(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[PropertyRecord]:
    statement = select(PropertyRecord).order_by(PropertyRecord.created_at.desc()).limit(limit)
    return list(db.scalars(statement))


@router.post("/properties", response_model=PropertyResponse)
def create_property(
    payload: PropertyCreateRequest,
    db: Session = Depends(get_db),
) -> PropertyRecord:
    if payload.locality_id not in LOCALITIES:
        raise HTTPException(status_code=404, detail="Chennai locality was not found")

    area_name = LOCALITIES[payload.locality_id]["name"]
    score, strengths, risks, recommendation = _evaluate_property(payload.model_dump())

    property_record = PropertyRecord(
        locality_id=payload.locality_id,
        area_name=area_name,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        monthly_rent=payload.monthly_rent,
        property_area_sqft=payload.property_area_sqft,
        frontage_m=payload.frontage_m,
        road_width_m=payload.road_width_m,
        parking_slots=payload.parking_slots,
        visibility=payload.visibility,
        condition=payload.condition,
        notes=payload.notes,
        status="SCOUTED",
        score=score,
        strengths=strengths,
        risks=risks,
        recommendation=recommendation,
    )
    db.add(property_record)
    db.commit()
    db.refresh(property_record)
    return property_record


@router.patch("/properties/{property_id}/status", response_model=PropertyResponse)
def update_property_status(
    property_id: int,
    payload: PropertyStatusUpdate,
    db: Session = Depends(get_db),
) -> PropertyRecord:
    property_record = db.get(PropertyRecord, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property was not found")

    property_record.status = payload.status
    if payload.note:
        property_record.notes = f"{property_record.notes} | {payload.note}".strip(" |")
    db.commit()
    db.refresh(property_record)
    return property_record
