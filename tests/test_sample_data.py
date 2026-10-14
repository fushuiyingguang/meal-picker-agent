"""校验团队实地采集的北苑 1 楼 77 条真实菜品数据样例。"""

import csv
from pathlib import Path

from meal_picker_agent.config import DEFAULT_CENTER
from meal_picker_agent.geo import haversine_km

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "beiyuan_1f_menu.csv"


def _rows():
    with SAMPLE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_beiyuan_sample_shape():
    rows = _rows()
    assert len(rows) == 77
    assert set(rows[0]) == {"name", "category", "price", "taste", "meat_type", "latitude", "longitude"}


def test_beiyuan_sample_coords_within_1km():
    for r in _rows():
        lat, lon = float(r["latitude"]), float(r["longitude"])
        dist = haversine_km(DEFAULT_CENTER[0], DEFAULT_CENTER[1], lat, lon)
        assert dist <= 1.0, f"{r['name']} 距离 {dist:.2f} 公里超出 1 公里"
