"""
Drift-детектор вхідних даних.

Два рівні перевірки:
  1. Миттєвий (per-request) z-score: чи лежить вектор у межах reference-розподілу.
  2. Популяційний KS-тест по ковзному вікну останніх N запитів проти
     reference-вибірки (двосторонній Колмогорова–Смирнова).

Reference-статистика готується у model/train.py і зберігається у reference.json.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import stats


@dataclass
class DriftResult:
    """Результат однієї перевірки на дрейф."""

    drift: bool
    kind: str  # "none" | "zscore" | "ks"
    max_z: float
    p_values: dict[str, float] = field(default_factory=dict)
    offending_features: list[str] = field(default_factory=list)
    window_filled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "drift": self.drift,
            "kind": self.kind,
            "max_z": round(self.max_z, 4),
            "p_values": {k: round(v, 5) for k, v in self.p_values.items()},
            "offending_features": self.offending_features,
            "window_filled": self.window_filled,
        }


class DriftDetector:
    """Статистичний детектор дрейфу для табличних ознак."""

    def __init__(
        self,
        mean: np.ndarray,
        std: np.ndarray,
        reference_sample: np.ndarray,
        feature_names: list[str],
        z_threshold: float = 3.0,
        window: int = 50,
        p_value: float = 0.05,
    ) -> None:
        self.mean = mean
        self.std = np.where(std <= 1e-9, 1e-9, std)
        self.reference_sample = reference_sample
        self.feature_names = feature_names
        self.z_threshold = z_threshold
        self.window = window
        self.p_value = p_value
        self._buffer: deque[np.ndarray] = deque(maxlen=window)

    @classmethod
    def from_reference_file(
        cls,
        path: str,
        feature_names: list[str],
        z_threshold: float = 3.0,
        window: int = 50,
        p_value: float = 0.05,
    ) -> "DriftDetector":
        """Будує детектор з reference.json."""
        with open(path, "r", encoding="utf-8") as fh:
            ref = json.load(fh)
        return cls(
            mean=np.asarray(ref["mean"], dtype=float),
            std=np.asarray(ref["std"], dtype=float),
            reference_sample=np.asarray(ref["sample"], dtype=float),
            feature_names=ref.get("feature_names", feature_names),
            z_threshold=z_threshold,
            window=window,
            p_value=p_value,
        )

    def detect(self, data: list[list[float]]) -> DriftResult:
        """
        Перевіряє батч вхідних векторів на дрейф.

        Спочатку миттєвий z-score, 
        потім — популяційний KS-тест по ковзному вікну.
        """
        X = np.asarray(data, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Миттєвий z-score
        z = np.abs((X - self.mean) / self.std)
        max_z = float(z.max()) if z.size else 0.0
        z_offenders = [
            self.feature_names[i]
            for i in range(X.shape[1])
            if i < len(self.feature_names) and z[:, i].max() > self.z_threshold
        ]

        # Накопичення у вікно
        for row in X:
            self._buffer.append(row)
        window_filled = len(self._buffer) >= self.window

        p_values: dict[str, float] = {}
        ks_offenders: list[str] = []
        if window_filled:
            recent = np.asarray(self._buffer, dtype=float)
            for i in range(min(self.reference_sample.shape[1], recent.shape[1])):
                name = (
                    self.feature_names[i]
                    if i < len(self.feature_names)
                    else f"f{i}"
                )
                stat = stats.ks_2samp(self.reference_sample[:, i], recent[:, i])
                p_values[name] = float(stat.pvalue)
                if stat.pvalue < self.p_value:
                    ks_offenders.append(name)

        if ks_offenders:
            return DriftResult(
                drift=True,
                kind="ks",
                max_z=max_z,
                p_values=p_values,
                offending_features=ks_offenders,
                window_filled=window_filled,
            )
        if z_offenders:
            return DriftResult(
                drift=True,
                kind="zscore",
                max_z=max_z,
                p_values=p_values,
                offending_features=z_offenders,
                window_filled=window_filled,
            )
        return DriftResult(
            drift=False,
            kind="none",
            max_z=max_z,
            p_values=p_values,
            offending_features=[],
            window_filled=window_filled,
        )
