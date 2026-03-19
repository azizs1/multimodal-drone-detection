import time

from .adapters import adapt_yolo_results


class DummyBoxes:
    def __init__(self, xyxy, conf, cls):
        self.xyxy = xyxy
        self.conf = conf
        self.cls = cls


class DummyResult:
    def __init__(self, names, boxes):
        self.names = names
        self.boxes = boxes


def test_adapt_yolo_results_dict_names():
    now = time.time()
    result = DummyResult(
        names={0: "drone"},
        boxes=DummyBoxes(
            xyxy=[[1, 2, 3, 4]],
            conf=[0.95],
            cls=[0],
        ),
    )

    preds = adapt_yolo_results(
        modality="rgb",
        timestamp=now,
        result=result,
        sensor_id="cam0",
    )

    assert len(preds) == 1
    pred = preds[0]
    assert pred.modality == "rgb"
    assert pred.class_id == "drone"
    assert pred.confidence == 0.95
    assert pred.bbox == (1.0, 2.0, 3.0, 4.0)
    assert pred.meta["sensor_id"] == "cam0"


def test_adapt_yolo_results_alias_mapping():
    now = time.time()
    result = DummyResult(
        names=["0"],
        boxes=DummyBoxes(
            xyxy=[[0, 0, 10, 10]],
            conf=[0.85],
            cls=[0],
        ),
    )

    preds = adapt_yolo_results(
        modality="thermal",
        timestamp=now,
        result=result,
        sensor_id="ir0",
        class_aliases={"0": "drone"},
    )

    assert len(preds) == 1
    assert preds[0].class_id == "drone"
