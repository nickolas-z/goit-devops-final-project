"""
Retrain-скрипт для AIOps Quality.

Навчає sklearn-класифікатор на датасеті Iris і зберігає:
  * model.joblib       — серіалізована модель (Pipeline: StandardScaler + SGDClassifier);
  * reference.json      — reference-статистика ознак для drift-детектора
                          (mean, std, та вибірка для KS-тесту).

Скрипт ідемпотентний і може запускатись:
  * локально          — `python model/train.py`;
  * у CI job `retrain-model` — за замовчуванням GitHub Actions
    (.github/workflows/retrain.yml), альтернативно GitLab CI (.gitlab-ci.yml).

Версія артефакту визначається env MODEL_VERSION (за замовчуванням — git-sha
або timestamp), щоб CI міг тегувати новий Docker-образ.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

OUTPUT_DIR = Path(os.getenv("MODEL_OUTPUT_DIR", Path(__file__).parent))
MODEL_PATH = OUTPUT_DIR / "model.joblib"
REFERENCE_PATH = OUTPUT_DIR / "reference.json"

LEARNING_RATE: float = float(os.getenv("LEARNING_RATE", "0.01"))
EPOCHS: int = int(os.getenv("EPOCHS", "500"))
REFERENCE_SAMPLE_SIZE: int = int(os.getenv("REFERENCE_SAMPLE_SIZE", "120"))

FEATURE_NAMES: list[str] = [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
]


def model_version() -> str:
    """Версія артефакту: пріоритет env MODEL_VERSION → git sha → timestamp."""
    explicit = os.getenv("MODEL_VERSION")
    if explicit:
        return explicit
    sha = os.getenv("CI_COMMIT_SHORT_SHA") or os.getenv("GIT_SHA")
    if sha:
        return sha
    return time.strftime("%Y%m%d-%H%M%S")


def train() -> Pipeline:
    """Навчає Pipeline(StandardScaler + SGDClassifier) на Iris."""
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                SGDClassifier(
                    loss="log_loss",
                    learning_rate="constant",
                    eta0=LEARNING_RATE,
                    max_iter=EPOCHS,
                    random_state=42,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, pipeline.predict(X_test))
    loss = log_loss(y_test, pipeline.predict_proba(X_test))
    print(
        f"trained: accuracy={accuracy:.4f} loss={loss:.4f} "
        f"lr={LEARNING_RATE} epochs={EPOCHS}"
    )
    return pipeline


def build_reference() -> dict[str, Any]:
    """
    Reference-статистика для drift-детектора рахується на повному (raw) Iris.

    Зберігаємо mean/std (для z-score) та вибірку (для KS-тесту).
    """
    X, _ = load_iris(return_X_y=True)
    rng = np.random.default_rng(42)
    n = min(REFERENCE_SAMPLE_SIZE, X.shape[0])
    idx = rng.choice(X.shape[0], size=n, replace=False)
    sample = X[idx]
    return {
        "feature_names": FEATURE_NAMES,
        "mean": X.mean(axis=0).round(6).tolist(),
        "std": X.std(axis=0).round(6).tolist(),
        "sample": sample.round(6).tolist(),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    version = model_version()

    pipeline = train()
    joblib.dump(pipeline, MODEL_PATH)
    print(f"saved model → {MODEL_PATH}")

    reference = build_reference()
    with open(REFERENCE_PATH, "w", encoding="utf-8") as fh:
        json.dump(reference, fh, indent=2)
    print(f"saved reference → {REFERENCE_PATH}")

    (OUTPUT_DIR / "MODEL_VERSION").write_text(version + "\n", encoding="utf-8")
    print(f"MODEL_VERSION={version}")


if __name__ == "__main__":
    main()
