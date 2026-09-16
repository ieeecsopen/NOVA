from prototypes.uncertainty import Calibrated, Prediction, Unknown, calibrate


def test_prediction_requires_explicit_calibration_gate():
    prediction = Prediction("green", 0.95)

    result = calibrate(prediction, lambda value: value.score * 0.8)

    assert result == Calibrated("green", 0.76)


def test_failed_calibration_does_not_create_calibrated_value():
    prediction = Prediction("green", 0.95)

    assert calibrate(prediction, lambda _: None) is None
    assert calibrate(prediction, lambda _: 1.1) is None


def test_unknown_preserves_reason():
    assert Unknown("distribution shift").reason == "distribution shift"
