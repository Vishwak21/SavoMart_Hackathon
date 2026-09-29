from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.area_analysis import LOCALITIES, build_area_report, search_localities
from app.database import get_db
from app.models import AreaReport

router = APIRouter(prefix="/api/areas", tags=["area intelligence"])


class AreaAnalysisRequest(BaseModel):
    locality_id: str


class AreaReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locality_id: str
    area_name: str
    latitude: float
    longitude: float
    radius_m: int
    fitness_score: int
    metrics: dict[str, Any]
    highlights: list[str]
    risks: list[str]
    data_source: str
    created_at: datetime


@router.get("/search")
def search_areas(q: str = Query(default="", max_length=80)) -> list[dict[str, Any]]:
    return search_localities(q)


@router.post("/analyze", response_model=AreaReportResponse)
def analyze_area(
    request: AreaAnalysisRequest,
    db: Session = Depends(get_db),
) -> AreaReport:
    if request.locality_id not in LOCALITIES:
        raise HTTPException(status_code=404, detail="Chennai locality was not found")

    report_data = build_area_report(request.locality_id)
    report = AreaReport(
        locality_id=report_data["locality_id"],
        area_name=report_data["name"],
        latitude=report_data["latitude"],
        longitude=report_data["longitude"],
        radius_m=report_data["radius_m"],
        fitness_score=report_data["fitness_score"],
        metrics=report_data["metrics"],
        highlights=report_data["highlights"],
        risks=report_data["risks"],
        data_source=report_data["data_source"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=list[AreaReportResponse])
def list_area_reports(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[AreaReport]:
    statement = select(AreaReport).order_by(AreaReport.created_at.desc()).limit(limit)
    return list(db.scalars(statement))


@router.get("/reports/{report_id}", response_model=AreaReportResponse)
def get_area_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> AreaReport:
    report = db.get(AreaReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Area report was not found")
    return report