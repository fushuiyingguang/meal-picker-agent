import pytest

from meal_picker_agent.models import Dish
from meal_picker_agent.storage import StorageError


def _dish(name="宫保鸡丁", category="中餐", taste=None, price=None, meat_type="荤", distance=300):
    return Dish(
        id=None, name=name, category=category, taste=taste or [],
        price=price, meat_type=meat_type, distance=distance,
    )


class TestDish:
    def test_add_and_get(self, storage):
        dish_id = storage.add_dish(_dish())
        d = storage.get_dish(dish_id)
        assert d.name == "宫保鸡丁"
        assert d.category == "中餐"
        assert d.meat_type == "荤"

    def test_add_duplicate_raises(self, storage):
        storage.add_dish(_dish())
        with pytest.raises(StorageError):
            storage.add_dish(_dish())

    def test_list_filters(self, storage):
        storage.add_dish(_dish("宫保鸡丁", "中餐", ["辣"], 30, "荤", 300))
        storage.add_dish(_dish("蔬菜沙拉", "西餐", ["清淡"], 20, "素", 700))
        storage.add_dish(_dish("牛肉面", "面食", ["辣"], 15, "荤", 1200))

        assert {d.name for d in storage.list_dishes(category="中餐")} == {"宫保鸡丁"}
        assert {d.name for d in storage.list_dishes(taste=["清淡"])} == {"蔬菜沙拉"}
        assert {d.name for d in storage.list_dishes(meat_type="素")} == {"蔬菜沙拉"}
        assert {d.name for d in storage.list_dishes(max_price=18)} == {"牛肉面"}
        assert {d.name for d in storage.list_dishes(max_distance=500)} == {"宫保鸡丁"}
        assert {d.name for d in storage.list_dishes(keyword="面")} == {"牛肉面"}

    def test_update(self, storage):
        dish_id = storage.add_dish(_dish())
        assert storage.update_dish(dish_id, price=35, taste=["下饭"])
        d = storage.get_dish(dish_id)
        assert d.price == 35
        assert d.taste == ["下饭"]

    def test_delete_keeps_history(self, storage):
        dish_id = storage.add_dish(_dish("回锅肉", "中餐"))
        storage.add_record(dish_id, source="draw")
        assert storage.delete_dish(dish_id) is True
        assert storage.get_dish(dish_id) is None
        recs = storage.list_records()
        assert len(recs) == 1
        assert recs[0].dish_id is None
        assert recs[0].dish_name == "回锅肉"


class TestRecord:
    def test_add_record_snapshot(self, storage):
        dish_id = storage.add_dish(_dish("水煮鱼", "中餐"))
        storage.add_record(dish_id, source="draw")
        recs = storage.list_records()
        assert recs[0].dish_name == "水煮鱼"
        assert recs[0].source == "draw"

    def test_add_record_unknown_dish_raises(self, storage):
        with pytest.raises(StorageError):
            storage.add_record(999)

    def test_set_rating(self, storage):
        dish_id = storage.add_dish(_dish())
        rec_id = storage.add_record(dish_id)
        assert storage.set_rating(rec_id, 5, "好吃")
        recs = storage.list_records()
        assert recs[0].score == 5
        assert recs[0].rating_note == "好吃"

    def test_set_rating_out_of_range(self, storage):
        dish_id = storage.add_dish(_dish())
        rec_id = storage.add_record(dish_id)
        with pytest.raises(StorageError):
            storage.set_rating(rec_id, 6)

    def test_recent_dish_ids(self, storage):
        d1 = storage.add_dish(_dish("A"))
        d2 = storage.add_dish(_dish("B"))
        storage.add_record(d1)
        storage.add_record(d2)
        assert storage.recent_dish_ids(days=7) == {d1, d2}


class TestExport:
    def test_export_dishes_csv(self, storage):
        storage.add_dish(_dish())
        out = storage.export_dishes("csv")
        assert "name" in out and "宫保鸡丁" in out

    def test_export_records_json(self, storage):
        dish_id = storage.add_dish(_dish())
        storage.add_record(dish_id)
        out = storage.export_records("json")
        assert "宫保鸡丁" in out
