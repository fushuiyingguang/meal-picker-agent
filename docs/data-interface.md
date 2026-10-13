# 数据结构与接口定义

三模块共享同一 SQLite 库；模块之间不直接调用，只通过共享数据访问层 `Storage` 读写。

## 存储选型
- **SQLite**（Python 标准库 `sqlite3`），单文件 `data/meal.db`，git 忽略。
- 选择理由：支持关联、筛选、去重、导出，比 JSON 更适合 CRUD + 不重复推荐场景。

## 表结构

### `dishes`（菜品）
| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK AUTOINCREMENT | 菜品 ID |
| name | TEXT | NOT NULL UNIQUE | 菜名 |
| category | TEXT | NOT NULL | 分类 |
| price | REAL | 可空 | 价格（元） |
| taste | TEXT | DEFAULT '' | 口味，逗号分隔，如 `辣,咸` |
| meat_type | TEXT | DEFAULT '' | 荤素：荤/素/半荤素 |
| distance | REAL | 可空 | 距离（米） |
| created_at | TEXT | DEFAULT 当前时间 | 录入时间 |

### `records`（选餐记录）
| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK AUTOINCREMENT | 记录 ID |
| dish_id | INTEGER | FK → dishes.id，可空 | 关联菜品，删除菜品后置空 |
| dish_name | TEXT | DEFAULT '' | 菜名快照，删除菜品后仍可展示 |
| selected_at | TEXT | DEFAULT 当前时间 | 选餐时间 |
| score | INTEGER | CHECK 1-5，可空 | 打分 |
| rating_note | TEXT | 可空 | 评价文字 |
| source | TEXT | DEFAULT 'draw' | 来源：draw / manual |

> **删除策略（已定）**：允许删除菜品并保留历史——`records.dish_id` 置空，`dish_name` 快照保留菜名。

```sql
CREATE TABLE dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    price REAL,
    taste TEXT NOT NULL DEFAULT '',
    meat_type TEXT NOT NULL DEFAULT '',
    distance REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id INTEGER REFERENCES dishes(id) ON DELETE SET NULL,
    dish_name TEXT NOT NULL DEFAULT '',
    selected_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    score INTEGER CHECK (score BETWEEN 1 AND 5),
    rating_note TEXT,
    source TEXT NOT NULL DEFAULT 'draw'
);
```

## 数据模型（`src/meal_picker_agent/models.py`）
```python
@dataclass
class Dish:
    id: int | None
    name: str
    category: str
    price: float | None = None
    taste: list[str] = field(default_factory=list)  # 口味标签
    meat_type: str = ""                              # 荤/素/半荤素
    distance: float | None = None                    # 距离（米）

@dataclass
class Record:
    id: int | None
    dish_id: int | None
    dish_name: str          # 菜名快照
    selected_at: str
    score: int | None = None
    rating_note: str | None = None
    source: str = "draw"
```

## 共享数据访问层（`src/meal_picker_agent/storage.py`）
`Storage` 类的方法即三模块唯一数据入口，页面不直接写 SQL。

| 方法 | 说明 |
| --- | --- |
| `init_db()` | 建库建表（幂等） |
| `add_dish(dish) -> int` | 新增，重名抛 `StorageError` |
| `get_dish(dish_id) -> Dish \| None` | 按 id 查询 |
| `list_dishes(category=None, taste=None, meat_type=None, max_price=None, max_distance=None, keyword=None) -> list[Dish]` | 多条件筛选（taste 任一命中） |
| `update_dish(dish_id, **fields) -> bool` | 更新字段（taste 传 list，None 置空） |
| `delete_dish(dish_id) -> bool` | 删除并保留历史（dish_id 置空、快照保留） |
| `export_dishes(fmt="csv") -> str` | 导出内容字符串（csv/json） |
| `add_record(dish_id, source="draw") -> int` | 新增记录，快照 `dish_name` |
| `list_records() -> list[Record]` | 查询历史 |
| `set_rating(record_id, score, note) -> bool` | 打分评价（1-5） |
| `export_records(fmt="csv") -> str` | 导出内容字符串（csv/json） |
| `recent_dish_ids(days=7) -> set[int]` | 近 N 天已选 id 集合（不重复推荐） |

## 模块间数据流
```
M1 菜品库 ──写──▶ dishes ──读──▶ M2 筛选摇号 ──写──▶ records ──读──▶ M3 记录评价/统计
                                │
                                └─ recent_dish_ids(days) 排除近期已选（不重复推荐）
```

## 约定
- 数据库文件不入库；首次启动自动 `init_db`。
- 表结构/接口变更需同步更新本文档与三份模块报告。
