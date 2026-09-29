import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.areas import router as areas_router
from app.catchments import router as catchments_router
from app.database import Base, engine
from app.demo_users import DEMO_USERS, DemoUser
from app.properties import router as properties_router

app = FastAPI(
    title="Savo SiteScout API",
    description="Store expansion intelligence and field survey workflows for Savomart.",
    version="0.1.0",
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(areas_router)
app.include_router(properties_router)
app.include_router(catchments_router)

Base.metadata.create_all(bind=engine)


@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "Savo SiteScout API"}


@app.get("/api/demo-users", response_model=list[DemoUser], tags=["demo"])
def list_demo_users() -> list[DemoUser]:
    return [DemoUser(**user) for user in DEMO_USERS]