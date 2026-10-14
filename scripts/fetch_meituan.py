"""美团/饿了么附近菜单爬虫模板（仅代码留存，不参与演示主流程）。

- 默认离线模式（REMOTE_ENABLED = False）：不联网，直接读取本地 samples/nearby_menu.csv 兜底。
- 若需真正请求平台，请自行接入官方/带签名的接口，并把 REMOTE_ENABLED 置为 True。
- 演示要求「离线爬取 + 本地导入」，绝不在演示时实时请求外卖平台。

用法：
    python scripts/fetch_meituan.py [纬度] [经度] [半径公里]

默认以中原工学院（郑州龙湖校区）为中心抓取 5 公里内数据。
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# 默认关闭联网：离线/演示场景绝不实时请求外卖平台
REMOTE_ENABLED = False

# 以中原工学院（郑州龙湖校区）为中心抓取 5 公里内数据
DEFAULT_CENTER = (34.626, 113.705)
DEFAULT_RADIUS_KM = 5.0

# 示例接口占位：真实平台接口通常需要签名、token 与风控参数，请勿直接使用
REMOTE_API = "https://example.com/api/nearby-restaurants"

_SAMPLES = Path(__file__).resolve().parents[1] / "samples"
LOCAL_FALLBACK = _SAMPLES / "nearby_menu.csv"
OUTPUT_FILE = _SAMPLES / "nearby_menu.csv"

FIELDNAMES = ["name", "category", "price", "taste", "meat_type", "latitude", "longitude"]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MealPickerAgent/0.1; educational demo)"}


def fetch_nearby(lat: float, lon: float, radius_km: float = DEFAULT_RADIUS_KM) -> list[dict]:
    """按中心点 + 半径抓取附近菜单（示例模板，需自行接入真实接口）。"""
    import requests  # 离线模式下不会走到这里

    params = {"lat": lat, "lng": lon, "radius": radius_km * 1000, "page_size": 50}
    resp = requests.get(REMOTE_API, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    # 示例：假设返回 {"restaurants": [{"name": ..., "category": ..., ...}]}
    return [
        {
            "name": item.get("name", ""),
            "category": item.get("category", ""),
            "price": item.get("avg_price"),
            "taste": item.get("taste", ""),
            "meat_type": item.get("meat_type", ""),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }
        for item in payload.get("restaurants", [])
    ]


def read_local_csv(path: Path) -> list[dict]:
    """读取本地兜底 CSV，返回与 fetch_nearby 同构的行。"""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDNAMES})


def main() -> int:
    args = sys.argv[1:]
    lat = float(args[0]) if len(args) > 0 else DEFAULT_CENTER[0]
    lon = float(args[1]) if len(args) > 1 else DEFAULT_CENTER[1]
    radius = float(args[2]) if len(args) > 2 else DEFAULT_RADIUS_KM

    if not REMOTE_ENABLED:
        print(f"[离线模式] 以中原工学院为中心抓取 {radius} 公里内数据（不联网，读本地兜底）。")
        if LOCAL_FALLBACK.exists():
            rows = read_local_csv(LOCAL_FALLBACK)
        else:
            print(f"[提示] 本地兜底文件不存在：{LOCAL_FALLBACK}")
            rows = []
    else:
        try:
            rows = fetch_nearby(lat, lon, radius)
            write_csv(rows, OUTPUT_FILE)
        except Exception as exc:  # noqa: BLE001
            print(f"[降级] 爬取失败：{exc}，回退到本地 samples/nearby_menu.csv")
            rows = read_local_csv(LOCAL_FALLBACK) if LOCAL_FALLBACK.exists() else []

    print(f"共 {len(rows)} 条，可用 M1「批量导入」导入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
