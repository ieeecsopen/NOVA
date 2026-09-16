"""Small, explicit epistemic value model used by the uncertainty prototype."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

ValueT = TypeVar("ValueT")
ReasonT = TypeVar("ReasonT")


@dataclass(frozen=True)
class Certain(Generic[ValueT]):
    value: ValueT


@dataclass(frozen=True)
class Prediction(Generic[ValueT]):
    value: ValueT
    score: float


@dataclass(frozen=True)
class Calibrated(Generic[ValueT]):
    value: ValueT
    probability: float


@dataclass(frozen=True)
class Unknown(Generic[ReasonT]):
    reason: ReasonT


def calibrate(
    prediction: Prediction[ValueT],
    gate: Callable[[Prediction[ValueT]], float | None],
) -> Calibrated[ValueT] | None:
    """Convert a prediction only through an explicit calibration gate.

    The gate returns a calibrated probability or ``None`` when calibration
    fails. The score is never treated as a probability automatically.
    """
    probability = gate(prediction)
    if probability is None or not 0.0 <= probability <= 1.0:
        return None
    return Calibrated(prediction.value, probability)
