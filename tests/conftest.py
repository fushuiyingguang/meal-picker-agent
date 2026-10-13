import pytest

from meal_picker_agent.storage import Storage


@pytest.fixture
def storage(tmp_path):
    s = Storage(tmp_path / "test.db")
    s.init_db()
    return s
