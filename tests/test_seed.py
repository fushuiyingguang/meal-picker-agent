from meal_picker_agent.config import DEFAULT_CENTER
from meal_picker_agent.geo import haversine_km
from meal_picker_agent.seed import SEED_DISHES


def test_seed_count():
    assert len(SEED_DISHES) == 16


def test_seed_within_5km_of_center():
    for d in SEED_DISHES:
        assert d.latitude is not None and d.longitude is not None
        dist = haversine_km(DEFAULT_CENTER[0], DEFAULT_CENTER[1], d.latitude, d.longitude)
        assert dist <= 5.0, f"{d.name} 距离 {dist:.2f} 公里超出 5 公里"
        # distance 备注（米）与经纬度计算的直线距离一致
        assert d.distance is not None and abs(d.distance - dist * 1000) < 1.0
