from meal_picker_agent.geo import haversine_km, offset_km


def test_haversine_same_point():
    assert haversine_km(34.626, 113.705, 34.626, 113.705) == 0.0


def test_haversine_one_degree_lat():
    d = haversine_km(34.0, 113.0, 35.0, 113.0)
    assert 110 < d < 112


def test_offset_roundtrip():
    lat, lon = offset_km(34.626, 113.705, 2.0, 90)
    d = haversine_km(34.626, 113.705, lat, lon)
    assert 1.9 < d < 2.1
