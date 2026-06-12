"""
AIOps Quality — FastAPI inference service.

Обгортка для sklearn-моделі (Iris classifier) як HTTP inference-сервіс.
На кожен запит:
  * вхідні дані логуються (structured stdout → Promtail → Loki);
  * модель обчислює відповідь у функції predict();
  * виконується перевірка на дрейф вхідних даних (drift_detector);
  * у разі дрейфу інкрементується лічильник та (опціонально) тригериться
    пайплайн retrain-model через webhook — за замовчуванням GitHub Actions
    (repository_dispatch), альтернативно GitLab CI.

Метрики Prometheus експонуються на /metrics (requests, latency, drift, predictions).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import joblib
import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

from drift_detector import DriftDetector, DriftResult

# Configuration (12-factor: усе через environment)

MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/model/model.joblib")
REFERENCE_PATH: str = os.getenv("REFERENCE_PATH", "/app/model/reference.json")
MODEL_VERSION: str = os.getenv("MODEL_VERSION", "unknown")
DRIFT_Z_THRESHOLD: float = float(os.getenv("DRIFT_Z_THRESHOLD", "3.0"))
DRIFT_WINDOW: int = int(os.getenv("DRIFT_WINDOW", "50"))
DRIFT_P_VALUE: float = float(os.getenv("DRIFT_P_VALUE", "0.05"))
RETRAIN_WEBHOOK_KIND: str = os.getenv("RETRAIN_WEBHOOK_KIND", "github")
RETRAIN_WEBHOOK_URL: str = os.getenv("RETRAIN_WEBHOOK_URL", "")
RETRAIN_WEBHOOK_TOKEN: str = os.getenv("RETRAIN_WEBHOOK_TOKEN", "")
RETRAIN_WEBHOOK_REF: str = os.getenv("RETRAIN_WEBHOOK_REF", "main")
RETRAIN_WEBHOOK_EVENT: str = os.getenv("RETRAIN_WEBHOOK_EVENT", "drift-detected")

CLASS_NAMES: list[str] = ["setosa", "versicolor", "virginica"]
FEATURE_NAMES: list[str] = [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
]

# Logging — JSON-рядки у stdout, які підхоплює Promtail/Loki

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
logger = logging.getLogger("aiops")


def log_event(event: str, **fields: Any) -> None:
    """Лог одним JSON-рядком (зручно парсити в Loki)."""
    record = {"event": event, "ts": time.time(), **fields}
    logger.info(json.dumps(record, default=str))


# Prometheus metrics

REQUESTS = Counter(
    "inference_requests_total",
    "Загальна кількість inference-запитів",
    ["endpoint", "status"],
)
LATENCY = Histogram(
    "inference_request_latency_seconds",
    "Час обробки inference-запиту (сек)",
    ["endpoint"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
PREDICTIONS = Counter(
    "inference_predictions_total",
    "Кількість передбачень за класом",
    ["predicted_class"],
)
DRIFT_ALERTS = Counter(
    "inference_drift_alerts_total",
    "Кількість спрацювань детектора дрейфу",
    ["kind"],
)
DRIFT_SCORE = Gauge(
    "inference_drift_score",
    "Поточний максимальний z-score вхідного вектора відносно reference",
)
MODEL_INFO = Gauge(
    "inference_model_info",
    "Інформація про завантажену модель",
    ["version"],
)


# Pydantic-схеми

class PredictRequest(BaseModel):
    """Вхідні дані: одна або кілька проб з 4 ознаками Iris."""

    features: list[list[float]] = Field(
        ...,
        description="Список векторів ознак [[sepal_length, sepal_width, "
        "petal_length, petal_width], ...]",
        examples=[[[5.1, 3.5, 1.4, 0.2]]],
    )


class Prediction(BaseModel):
    predicted_class: int
    predicted_label: str
    probabilities: list[float]


class PredictResponse(BaseModel):
    model_version: str
    predictions: list[Prediction]
    drift_detected: bool
    drift_detail: dict[str, Any]


# Глобальний стан (модель + детектор), наповнюється у lifespan

class _State:
    model: Any = None
    detector: DriftDetector | None = None


state = _State()


def _load_model() -> Any:
    """Завантажує модель з диска."""
    log_event("model_loading", path=MODEL_PATH)
    model = joblib.load(MODEL_PATH)
    log_event("model_loaded", path=MODEL_PATH, version=MODEL_VERSION)
    return model


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Завантаження моделі та детектора при старті."""
    state.model = _load_model()
    state.detector = DriftDetector.from_reference_file(
        REFERENCE_PATH,
        z_threshold=DRIFT_Z_THRESHOLD,
        window=DRIFT_WINDOW,
        p_value=DRIFT_P_VALUE,
        feature_names=FEATURE_NAMES,
    )
    MODEL_INFO.labels(version=MODEL_VERSION).set(1)
    log_event("startup_complete", model_version=MODEL_VERSION)
    yield
    log_event("shutdown")


app = FastAPI(
    title="AIOps Quality — Inference Service",
    description="FastAPI inference + drift detection для Iris-класифікатора.",
    version=MODEL_VERSION,
    lifespan=lifespan,
)


# Основна логіка предикту — окрема функція згідно вимог TASK

def predict(data: list[list[float]]) -> list[Prediction]:
    """
    Повертає передбачення моделі для матриці ознак.

    Args:
        data: список векторів ознак (кожен — 4 числа для Iris).

    Returns:
        Список Prediction з класом, лейблом та ймовірностями.
    """
    X = np.asarray(data, dtype=float)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    labels = state.model.predict(X)
    try:
        proba = state.model.predict_proba(X)
    except (AttributeError, NotImplementedError):
        proba = np.eye(len(CLASS_NAMES))[labels]

    results: list[Prediction] = []
    for cls, probs in zip(labels, proba):
        cls_int = int(cls)
        label = CLASS_NAMES[cls_int] if cls_int < len(CLASS_NAMES) else str(cls_int)
        results.append(
            Prediction(
                predicted_class=cls_int,
                predicted_label=label,
                probabilities=[round(float(p), 6) for p in probs],
            )
        )
    return results


def _maybe_trigger_retrain(detail: dict[str, Any]) -> None:
    """Webhook для запуску retrain (GitHub Actions або GitLab CI)."""
    if not RETRAIN_WEBHOOK_URL or not RETRAIN_WEBHOOK_TOKEN:
        return
    try:
        import requests

        if RETRAIN_WEBHOOK_KIND == "github":
            # GitHub repository_dispatch → workflow retrain-model.
            resp = requests.post(
                RETRAIN_WEBHOOK_URL,  # https://api.github.com/repos/<owner>/<repo>/dispatches
                headers={
                    "Authorization": f"Bearer {RETRAIN_WEBHOOK_TOKEN}",
                    "Accept": "application/vnd.github+json",
                },
                json={"event_type": RETRAIN_WEBHOOK_EVENT, "client_payload": detail},
                timeout=5,
            )
        else:
            # GitLab pipeline trigger token.
            resp = requests.post(
                RETRAIN_WEBHOOK_URL,
                data={
                    "token": RETRAIN_WEBHOOK_TOKEN,
                    "ref": RETRAIN_WEBHOOK_REF,
                    "variables[TRIGGER_SOURCE]": "drift_detector",
                },
                timeout=5,
            )
        log_event(
            "retrain_webhook_sent",
            kind=RETRAIN_WEBHOOK_KIND,
            status_code=resp.status_code,
            detail=detail,
        )
    except Exception as exc:  # noqa: BLE001 — webhook не має валити інференс
        log_event("retrain_webhook_error", error=str(exc))


# Endpoints

@app.get("/", response_class=JSONResponse)
def root() -> dict[str, Any]:
    return {
        "service": "aiops-quality-inference",
        "model_version": MODEL_VERSION,
        "classes": CLASS_NAMES,
        "features": FEATURE_NAMES,
        "endpoints": ["/predict", "/health", "/metrics", "/docs"],
    }


@app.get("/health", response_class=JSONResponse)
@app.get("/healthz", response_class=JSONResponse)
def health() -> dict[str, str]:
    """Liveness/readiness probe."""
    ready = state.model is not None and state.detector is not None
    return {"status": "ok" if ready else "loading"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    """Prometheus scrape endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(payload: PredictRequest, request: Request) -> PredictResponse:
    """Inference + перевірка дрейфу на кожен запит."""
    start = time.perf_counter()
    endpoint = "/predict"

    # Логування
    log_event(
        "inference_request",
        client=request.client.host if request.client else None,
        n_samples=len(payload.features),
        features=payload.features,
    )

    try:
        # Передбачення
        predictions = predict(payload.features)
        for p in predictions:
            PREDICTIONS.labels(predicted_class=p.predicted_label).inc()

        # Перевірка дрейфу
        assert state.detector is not None
        drift: DriftResult = state.detector.detect(payload.features)
        DRIFT_SCORE.set(drift.max_z)
        if drift.drift:
            DRIFT_ALERTS.labels(kind=drift.kind).inc()
            log_event("drift_detected", **drift.as_dict())
            print("Drift detected", flush=True)  # явний маркер для kubectl logs
            _maybe_trigger_retrain(drift.as_dict())

        # Логування відповіді
        log_event(
            "inference_response",
            model_version=MODEL_VERSION,
            predictions=[p.predicted_label for p in predictions],
            drift_detected=drift.drift,
        )

        REQUESTS.labels(endpoint=endpoint, status="200").inc()
        return PredictResponse(
            model_version=MODEL_VERSION,
            predictions=predictions,
            drift_detected=drift.drift,
            drift_detail=drift.as_dict(),
        )
    except Exception as exc:  # noqa: BLE001
        REQUESTS.labels(endpoint=endpoint, status="500").inc()
        log_event("inference_error", error=str(exc))
        raise
    finally:
        LATENCY.labels(endpoint=endpoint).observe(time.perf_counter() - start)
