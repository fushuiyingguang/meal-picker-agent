"""共享数据访问层：三个页面只通过本模块读写 SQLite，不直接写 SQL。

接口契约见 docs/data-interface.md。
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .models import Dish, Record


class StorageError(Exception):
    """数据访问层异常。"""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    price REAL,
    taste TEXT NOT NULL DEFAULT '',
    meat_type TEXT NOT NULL DEFAULT '',
    distance REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id INTEGER REFERENCES dishes(id) ON DELETE SET NULL,
    dish_name TEXT NOT NULL DEFAULT '',
    selected_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    score INTEGER CHECK (score BETWEEN 1 AND 5),
    rating_note TEXT,
    source TEXT NOT NULL DEFAULT 'draw'
);
"""


def _list_to_str(items: list[str] | None) -> str:
    return ",".join(items) if items else ""


def _str_to_list(s: str) -> list[str]:
    return [t for t in (s or "").split(",") if t]


def _row_to_dish(row: sqlite3.Row) -> Dish:
    return Dish(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        price=row["price"],
        taste=_str_to_list(row["taste"]),
        meat_type=row["meat_type"],
        distance=row["distance"],
    )


def _row_to_record(row: sqlite3.Row) -> Record:
    return Record(
        id=row["id"],
        dish_id=row["dish_id"],
        dish_name=row["dish_name"],
        selected_at=row["selected_at"],
        score=row["score"],
        rating_note=row["rating_note"],
        source=row["source"],
    )


class Storage:
    """SQLite 数据访问层。"""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        """建库建表（幂等）。"""
        conn = self._connect()
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    # ---- 菜品 ----
    def add_dish(self, dish: Dish) -> int:
        """新增菜品，返回 id；菜名重复时抛 StorageError。"""
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO dishes (name, category, price, taste, meat_type, distance) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (dish.name, dish.category, dish.price, _list_to_str(dish.taste), dish.meat_type, dish.distance),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise StorageError(f"菜品已存在或数据非法：{dish.name}") from exc
        finally:
            conn.close()

    def get_dish(self, dish_id: int) -> Dish | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM dishes WHERE id = ?", (dish_id,)).fetchone()
            return _row_to_dish(row) if row else None
        finally:
            conn.close()

    def list_dishes(
        self,
        category: str | None = None,
        taste: list[str] | None = None,
        meat_type: str | None = None,
        max_price: float | None = None,
        max_distance: float | None = None,
        keyword: str | None = None,
    ) -> list[Dish]:
        """多条件筛选。taste 为「含任一口味即命中」的精确匹配。"""
        clauses: list[str] = []
        params: list = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if taste:
            clauses.append("(" + " OR ".join("(',' || taste || ',') LIKE ?" for _ in taste) + ")")
            params.extend(f"%,{t},%" for t in taste)
        if meat_type:
            clauses.append("meat_type = ?")
            params.append(meat_type)
        if max_price is not None:
            clauses.append("price IS NOT NULL AND price <= ?")
            params.append(max_price)
        if max_distance is not None:
            clauses.append("distance IS NOT NULL AND distance <= ?")
            params.append(max_distance)
        if keyword:
            clauses.append("name LIKE ?")
            params.append(f"%{keyword}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        conn = self._connect()
        try:
            rows = conn.execute(f"SELECT * FROM dishes{where} ORDER BY id", params).fetchall()
            return [_row_to_dish(r) for r in rows]
        finally:
            conn.close()

    def update_dish(self, dish_id: int, **fields) -> bool:
        """按关键字参数更新字段（taste 传 list）；显式传 None 表示置空。"""
        allowed = {"name", "category", "price", "taste", "meat_type", "distance"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        if isinstance(updates.get("taste"), list):
            updates["taste"] = _list_to_str(updates["taste"])
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn = self._connect()
        try:
            cur = conn.execute(
                f"UPDATE dishes SET {set_clause} WHERE id = ?",
                [*updates.values(), dish_id],
            )
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.IntegrityError as exc:
            raise StorageError(f"更新失败：{exc}") from exc
        finally:
            conn.close()

    def delete_dish(self, dish_id: int) -> bool:
        """删除菜品并保留历史：records.dish_id 置空，dish_name 快照保留。"""
        conn = self._connect()
        try:
            conn.execute("UPDATE records SET dish_id = NULL WHERE dish_id = ?", (dish_id,))
            cur = conn.execute("DELETE FROM dishes WHERE id = ?", (dish_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def export_dishes(self, fmt: str = "csv") -> str:
        """导出菜品（返回 csv/json 字符串内容）。"""
        dishes = self.list_dishes()
        if fmt == "json":
            return json.dumps([asdict(d) for d in dishes], ensure_ascii=False, indent=2)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "name", "category", "price", "taste", "meat_type", "distance"])
        for d in dishes:
            writer.writerow([d.id, d.name, d.category, d.price, ",".join(d.taste), d.meat_type, d.distance])
        return buf.getvalue()

    # ---- 记录 ----
    def add_record(self, dish_id: int, source: str = "draw") -> int:
        """新增选餐记录，同时快照菜名到 dish_name。"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT name FROM dishes WHERE id = ?", (dish_id,)).fetchone()
            if row is None:
                raise StorageError(f"菜品不存在：{dish_id}")
            cur = conn.execute(
                "INSERT INTO records (dish_id, dish_name, source) VALUES (?, ?, ?)",
                (dish_id, row["name"], source),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def list_records(self) -> list[Record]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM records ORDER BY id").fetchall()
            return [_row_to_record(r) for r in rows]
        finally:
            conn.close()

    def set_rating(self, record_id: int, score: int, note: str = "") -> bool:
        """打分（1-5）与文字评价。"""
        if not 1 <= score <= 5:
            raise StorageError(f"评分须在 1-5 之间：{score}")
        conn = self._connect()
        try:
            cur = conn.execute(
                "UPDATE records SET score = ?, rating_note = ? WHERE id = ?",
                (score, note, record_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def export_records(self, fmt: str = "csv") -> str:
        """导出历史记录（返回 csv/json 字符串内容）。"""
        records = self.list_records()
        if fmt == "json":
            return json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "dish_id", "dish_name", "selected_at", "score", "rating_note", "source"])
        for r in records:
            writer.writerow([r.id, r.dish_id, r.dish_name, r.selected_at, r.score, r.rating_note, r.source])
        return buf.getvalue()

    def recent_dish_ids(self, days: int = 7) -> set[int]:
        """近 N 天已选菜品 id 集合（不重复推荐用）。"""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT DISTINCT dish_id FROM records "
                "WHERE dish_id IS NOT NULL AND selected_at >= datetime('now','localtime', ?)",
                (f"-{days} days",),
            ).fetchall()
            return {r["dish_id"] for r in rows}
        finally:
            conn.close()
