"""HTTP service for the price model.

Run from the ml/ folder:
    .venv/Scripts/python.exe -m uvicorn shotti_ml.api:app --port 8000

The artifact is loaded once, at startup: $SHOTTI_ARTIFACT if set, else the newest folder under
ml/artifacts. Endpoints:

    GET  /health    the service is up and which model it serves
    GET  /model     version, training data, interval settings and metrics
    POST /predict   one car -> expected asking price in taka and its 80% range
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import settings
from .artifact import load_artifact

LATEST_YEAR = date.today().year + 1  # next year's models go on sale this year

EXAMPLE = {
    "brand": "Toyota",
    "model": "Axio",
    "build_year": 2018,
    "mileage_km": 60000,
    "engine_cc": 1500,
    "fuel": "petrol",
    "transmission": "automatic",
}


class Car(BaseModel):
    """One car. Only brand, model, build year and fuel are required; the rest is filled in the way the
    training data was: engine size from the model's median, mileage from cars built the same year."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [EXAMPLE]})

    brand: str = Field(min_length=1, max_length=40, description="Make, such as Toyota")
    model: str = Field(min_length=1, max_length=60, description="Model, such as Axio or Corolla Cross")
    build_year: int = Field(ge=1985, le=LATEST_YEAR)
    mileage_km: int | None = Field(None, ge=0, le=1_000_000, description="Above 400,000 is treated as 400,000, as in training")
    engine_cc: int | None = Field(None, ge=600, le=8000)
    fuel: Literal["petrol", "octane", "hybrid", "diesel", "cng", "lpg", "other"] = Field(description="petrol (or octane), hybrid, diesel, cng, lpg or other")
    transmission: Literal["automatic", "manual"] = "automatic"
    registration_year: int | None = Field(None, ge=1985, le=LATEST_YEAR, description="Year first registered in Bangladesh")
    condition: Literal["Used", "Reconditioned", "Unknown"] = "Unknown"
    listing_site: Literal["garirbazar", "bikroy"] = "garirbazar"

    @field_validator("fuel", "transmission", "listing_site", mode="before")
    @classmethod
    def _lower(cls, value):
        if isinstance(value, str):
            value = value.strip().lower()
            if value == "electric":
                raise ValueError("electric cars are not priced: the training data has too few and drops them")
        return value

    @field_validator("condition", mode="before")
    @classmethod
    def _capitalise(cls, value):
        return value.strip().capitalize() if isinstance(value, str) else value

    @field_validator("brand", "model")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def _registered_after_built(self):
        if self.registration_year is not None and self.registration_year < self.build_year:
            raise ValueError("registration_year cannot be before build_year")
        return self


class Prediction(BaseModel):
    price_bdt: int = Field(description="Expected asking price, rounded to the nearest 1,000 taka")
    low_bdt: int
    high_bdt: int
    coverage: float = Field(description="Share of real asking prices the range is calibrated to hold")
    model_version: str
    matched_brand: str
    matched_model: str
    model_seen_in_training: bool = Field(description="False when the model had too few listings and was pooled as 'Other model'")
    imputed: list[str] = Field(description="Fields filled in from training medians")


def create_app(artifact: str | Path | None = None) -> FastAPI:
    """The app; `artifact` overrides $SHOTTI_ARTIFACT and the newest-artifact default."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.artifact = load_artifact(settings.artifact_dir(artifact))
        yield

    app = FastAPI(title="Shotti Dam used-car price model", version="1", lifespan=lifespan)

    @app.get("/health")
    def health(request: Request) -> dict:
        return {"status": "ok", "model_version": request.app.state.artifact.version}

    @app.get("/model")
    def model_info(request: Request) -> dict:
        a = request.app.state.artifact
        m = a.metadata
        return {
            "version": a.version,
            "created_at": m["created_at"],
            "git_commit": m["git_commit"],
            "data_fingerprint": m["data_fingerprint"],
            "reference_year": m["reference_year"],
            "data": m["data"],
            "interval": m["interval"],
            "metrics": a.metrics,
        }

    @app.post("/predict", response_model=Prediction)
    def predict(car: Car, request: Request) -> dict:
        return request.app.state.artifact.price_car(car.model_dump())

    return app


app = create_app()
