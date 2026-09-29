from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.area_analysis import LOCALITIES
from app.database import get_db
from app.models import CatchmentRequest, SurveyAssignment

router = APIRouter(prefix="/api", tags=["catchment workflow"])


class CatchmentRequestCreate(BaseModel):
    locality_id: str
    area_name: str
    target_type: str = "area"
    target_id: int | None = None
    reason: str = ""


class CatchmentRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locality_id: str
    area_name: str
    target_type: str
    target_id: int | None
    reason: str
    status: str
    created_at: datetime


class SurveyAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catchment_request_id: int
    survey_executive: str
    status: str
    progress: int
    created_at: datetime


@router.get("/catchment-requests", response_model=list[CatchmentRequestResponse])
def list_catchment_requests(db: Session = Depends(get_db)) -> list[CatchmentRequest]:
    statement = select(CatchmentRequest).order_by(CatchmentRequest.created_at.desc())
    return list(db.scalars(statement))


@router.post("/catchment-requests", response_model=CatchmentRequestResponse)
def create_catchment_request(
    payload: CatchmentRequestCreate,
    db: Session = Depends(get_db),
) -> CatchmentRequest:
    if payload.locality_id not in LOCALITIES:
        raise HTTPException(status_code=404, detail="Chennai locality was not found")

    request_record = CatchmentRequest(
        locality_id=payload.locality_id,
        area_name=payload.area_name or LOCALITIES[payload.locality_id]["name"],
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        status="PENDING",
    )
    db.add(request_record)
    db.commit()
    db.refresh(request_record)

    assignment = SurveyAssignment(
        catchment_request_id=request_record.id,
        survey_executive="Kavin Raj",
        status="ASSIGNED",
        progress=12,
    )
    db.add(assignment)
    db.commit()
    return request_record


@router.get("/survey-assignments", response_model=list[SurveyAssignmentResponse])
def list_survey_assignments(db: Session = Depends(get_db)) -> list[SurveyAssignment]:
    statement = select(SurveyAssignment).order_by(SurveyAssignment.created_at.desc())
    return list(db.scalars(statement))
