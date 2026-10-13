from meal_picker_agent.models import Dish, Record


def test_dish_defaults():
    d = Dish(id=None, name="测试", category="中餐")
    assert d.taste == []
    assert d.price is None
    assert d.meat_type == ""
    assert d.distance is None


def test_record_defaults():
    r = Record(id=None, dish_id=None, dish_name="测试", selected_at="2026-10-13 12:00:00")
    assert r.score is None
    assert r.source == "draw"
