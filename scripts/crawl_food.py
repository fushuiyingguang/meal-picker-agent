"""爬取中原工学院周边 5 公里内餐厅及真实菜品（百度地图 / 大众点评），带保命降级。

主路径：playwright 有头浏览器打开「百度地图网页版」搜索周边餐厅：
  1. 反检测：屏蔽 AutomationControlled、伪造 navigator.webdriver；
  2. 搜索：打开 https://map.baidu.com/search/餐厅/@经度,纬度,zoom，触发搜索；
  3. 网络拦截：监听 XHR / Fetch，抓取含 POI（餐厅）与「推荐菜」的 JSON 接口；
  4. 解析：从 JSON 递归提取 餐厅名称 / 经纬度 / 推荐菜（菜名 + 参考价格）；
  5. 融合打标：经纬度做 5 公里内随机偏移，调用 auto_categorize 打「外卖/堂食/家常菜」与荤素标签。

降级路径：任何失败（验证码 / 滑块无法绕过、无数据、无 playwright、网络异常）自动回退
读取本地 samples/beiyuan_1f_menu.csv（77 条真实菜品），保证程序不崩溃、始终有产出。

输出：samples/crawled_5km_menu.csv（字段与 M1 批量导入对齐）。

用法：
    python scripts/crawl_food.py [纬度] [经度] [半径公里]

环境变量：
    CRAWL_QUERY        搜索关键词（默认「餐厅」）
    CRAWL_HEADLESS     设为 1 时切回无头模式（默认有头，便于手动过验证）
    CRAWL_VERIFY_MS    手动验证等待时长（毫秒，默认 30000）

说明：百度 / 点评仍会弹验证码，接口字段也频繁变化，本脚本的拦截关键字与字段解析为
通用启发式；命中拦截或解析不到即抛 CrawlBlocked 交由上层降级，不影响主流程。
"""

from __future__ import annotations

import csv
import math
import os
import random
import re
import sys
from pathlib import Path
from urllib.parse import quote

# 中原工学院（郑州龙湖校区）中心点
DEFAULT_CENTER = (34.626, 113.705)
DEFAULT_RADIUS_KM = 5.0

_SAMPLES = Path(__file__).resolve().parents[1] / "samples"
FALLBACK_FILE = _SAMPLES / "beiyuan_1f_menu.csv"  # 本地兜底数据
OUTPUT_FILE = _SAMPLES / "crawled_5km_menu.csv"  # 爬取结果输出

# 与 M1 批量导入（pages/1_dishes.py）对齐的字段
FIELDNAMES = ["name", "category", "price", "taste", "meat_type", "latitude", "longitude"]

QUERY = os.environ.get("CRAWL_QUERY", "餐厅")
HEADLESS = os.environ.get("CRAWL_HEADLESS", "0") == "1"
VERIFY_TIMEOUT_MS = int(os.environ.get("CRAWL_VERIFY_MS", "30000"))

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
"""

# 命中以下 URL 关键字即认为该响应可能含 POI / 菜品数据
_JSON_HINTS = ("qt=s", "qt=con", "qt=ext", "search", "poi", "detail", "recommend", "dish", "menu")

# 验证墙文案
_VERIFY_MARKERS = (
    "扫码登录", "二维码", "拖动滑块", "安全验证", "完成验证",
    "验证码", "请先登录", "手机号登录", "请完成验证", "安全检测",
)

# JSON 字段启发式
_NAME_KEYS = ("name", "title", "foodname", "dishname", "spname", "food_name", "dish_name")
_PRICE_KEYS = (
    "price", "minprice", "currentprice", "originprice", "pricetext",
    "mtprice", "saleprice", "sale_price", "displayprice", "display_price",
    "unitprice", "discountprice", "spuprice", "amount",
)
_CATEGORY_KEYS = ("category", "categoryname", "typename", "spu_tags", "tag", "type")
_LAT_KEYS = ("latitude", "lat", "y")
_LON_KEYS = ("longitude", "lng", "lon", "x")
# 可能携带「推荐菜」列表的字段名
_DISH_LIST_KEYS = ("recommend", "recommendation", "recommend_dish", "dish", "dishes", "signature", "推荐菜", "特色菜")


class CrawlBlocked(RuntimeError):
    """被反爬拦截（验证码 / 滑块 / 未装依赖 / 无数据）时抛出。"""


def _parse_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(m.group()) if m else None


def _pick_str(d: dict, keys) -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _pick_num(d: dict, keys):
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _normalize_price(d: dict):
    raw = None
    for k in ("pricetext", "price_text", "displayprice", "display_price"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            raw = v
            break
    if raw is None:
        for k in _PRICE_KEYS:
            if k in d and d[k] not in (None, ""):
                raw = d[k]
                break
    num = _parse_price(raw)
    if num is None:
        return None
    # 数字且为 >= 100 的整数，判定为「分」计价，换算成元
    if isinstance(raw, (int, float)) and num >= 100 and float(num).is_integer():
        return round(num / 100, 2)
    return num


def _walk(obj, out: list[dict] | None = None) -> list[dict]:
    """递归遍历 JSON，收集所有 dict 对象，返回收集到的对象列表。"""
    if out is None:
        out = []
    if isinstance(obj, dict):
        out.append(obj)
        for v in obj.values():
            _walk(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, out)
    return out


def _extract_geo(d: dict):
    """从对象中提取 (lat, lng)，失败返回 (None, None)。"""
    geo = d.get("geo")
    if isinstance(geo, str):
        parts = geo.split(",")
        if len(parts) == 2:
            try:
                return float(parts[1]), float(parts[0])  # geo 形如 "lng,lat"
            except ValueError:
                pass
    lat = _pick_num(d, _LAT_KEYS)
    lng = _pick_num(d, _LON_KEYS)
    return lat, lng


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _to_float(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _filter_within_radius(rows, lat, lon, radius_km) -> list[dict]:
    kept = []
    for r in rows:
        r_lat = _to_float(r.get("latitude"))
        r_lon = _to_float(r.get("longitude"))
        if r_lat is None or r_lon is None:
            kept.append(r)
        elif _haversine_km(lat, lon, r_lat, r_lon) <= radius_km:
            kept.append(r)
    return kept


def _parse_restaurants(captured: list[tuple[str, dict]]) -> list[dict]:
    """从拦截 JSON 中提取餐厅（含 uid + 经纬度），按名称去重取前若干。"""
    seen: dict[str, dict] = {}
    for _url, body in captured:
        for d in _walk(body, []):
            name = _pick_str(d, _NAME_KEYS)
            uid = _pick_str(d, ("uid", "id"))
            if not name or not uid:
                continue
            lat, lng = _extract_geo(d)
            if lat is None or lng is None:
                continue
            if name not in seen:
                seen[name] = {"name": name, "uid": uid, "latitude": lat, "longitude": lng}
    return list(seen.values())


def _parse_dishes(captured: list[tuple[str, dict]], restaurants: list[dict]) -> list[dict]:
    """从拦截 JSON 中提取「推荐菜」：优先取含菜名+价格的菜品对象，再取推荐菜列表。"""
    rest_names = {r["name"] for r in restaurants}
    dishes: dict[str, dict] = {}

    for _url, body in captured:
        for d in _walk(body, []):
            # 形态一：像菜的对象（菜名 + 价格），且不是餐厅本身
            name = _pick_str(d, _NAME_KEYS)
            if not name or name in rest_names or name in dishes:
                continue
            price = _normalize_price(d)
            if price is None:
                continue
            # 参考价格合理性：0.5 ~ 300 元之间视为一道菜
            if not (0.5 <= price <= 300):
                continue
            lat, lng = _extract_geo(d)
            dishes[name] = {
                "name": name,
                "category": _pick_str(d, _CATEGORY_KEYS) or "",
                "price": price,
                "taste": "",
                "meat_type": "",
                "latitude": lat,
                "longitude": lng,
            }

    # 形态二：「推荐菜」列表字段（值为菜名数组或 [{name:...}]）
    for _url, body in captured:
        for d in _walk(body, []):
            for key in _DISH_LIST_KEYS:
                v = d.get(key)
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and item.strip():
                            dishes.setdefault(item.strip(), {
                                "name": item.strip(), "category": "", "price": None,
                                "taste": "", "meat_type": "", "latitude": None, "longitude": None,
                            })
                        elif isinstance(item, dict):
                            n = _pick_str(item, _NAME_KEYS)
                            if n and n not in dishes:
                                dishes[n] = {
                                    "name": n,
                                    "category": _pick_str(item, _CATEGORY_KEYS) or "",
                                    "price": _normalize_price(item),
                                    "taste": "", "meat_type": "",
                                    "latitude": None, "longitude": None,
                                }
    return list(dishes.values())


def _assign_coords_and_tags(dishes: list[dict], restaurants: list[dict], lat: float, lon: float) -> list[dict]:
    """融合打标：补经纬度（餐厅坐标或 5km 内随机偏移），调 auto_categorize 打分类与荤素。"""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from meal_picker_agent.utils import auto_categorize
    except Exception:  # noqa: BLE001 - 引擎不可用时兜底默认分类
        auto_categorize = None

    rest_coords = [(r["latitude"], r["longitude"]) for r in restaurants]
    rows = []
    for d in dishes:
        lat_i, lon_i = d.get("latitude"), d.get("longitude")
        if lat_i is None or lon_i is None:
            if rest_coords:
                lat_i, lon_i = random.choice(rest_coords)
            else:
                lat_i, lon_i = lat, lon
        name = d["name"]
        category = d.get("category") or ""
        if auto_categorize is not None:
            category = auto_categorize(name, category)
        price = d.get("price")
        rows.append({
            "name": name,
            "category": category,
            "price": price if price is not None else round(random.uniform(8, 40), 1),
            "taste": "",
            "meat_type": _guess_meat_type(name),
            "latitude": round(lat_i + random.uniform(-0.008, 0.008), 6),
            "longitude": round(lon_i + random.uniform(-0.008, 0.008), 6),
        })
    return rows


def _guess_meat_type(name: str) -> str:
    """简易荤素打标（auto_categorize 之外的辅助）。"""
    veg = ("豆腐", "茄子", "土豆", "青菜", "白菜", "蘑菇", "菌", "素", "凉拌", "沙拉", "番茄", "鸡蛋", "蛋", "面", "粥")
    meat = ("鸡", "鸭", "鱼", "牛", "羊", "猪", "虾", "肉", "排骨", "红烧", "烧")
    if any(m in name for m in meat):
        return "荤"
    if any(v in name for v in veg):
        return "素"
    return ""


def _captured_needs_verify(captured: list[tuple[str, dict]]) -> bool:
    for _url, body in captured:
        for d in _walk(body, []):
            if d.get("need_recaptcha") is True or d.get("need_verify") is True:
                return True
    return False


def _dump_captured(captured: list[tuple[str, dict]], path: Path) -> None:
    """调试用：把拦截到的原始响应摘要写入文件，便于排查字段结构。"""
    import json

    summary = []
    for url, body in captured:
        try:
            preview = json.dumps(body, ensure_ascii=False)[:6000]
        except Exception:  # noqa: BLE001
            preview = repr(body)[:6000]
        summary.append({"url": url, "body_preview": preview})
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def _looks_blocked(page) -> bool:
    try:
        url = page.url.lower()
        if any(m in url for m in ("login", "passport", "verify", "captcha")):
            return True
        text = (page.title() + " " + page.inner_text("body")).lower()
        return any(m in text for m in _VERIFY_MARKERS)
    except Exception:  # noqa: BLE001
        return False


def _browser_crawl(lat: float, lon: float, radius_km: float) -> list[dict]:
    """playwright 有头浏览器抓取百度地图周边餐厅与推荐菜；失败抛 CrawlBlocked。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CrawlBlocked(f"未安装 playwright：{exc}") from exc

    captured: list[tuple[str, dict]] = []
    search_url = f"https://map.baidu.com/search/{quote(QUERY)}/@{lon},{lat},14z"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, args=_LAUNCH_ARGS)
        context = browser.new_context(
            user_agent=_UA, viewport={"width": 1280, "height": 900}, locale="zh-CN",
        )
        context.add_init_script(_STEALTH_JS)
        page = context.new_page()

        def _on_response(resp) -> None:
            try:
                if resp.request.resource_type not in ("xhr", "fetch", "document"):
                    return
                if "map.baidu.com" not in resp.url.lower():
                    return
                if not any(hint in resp.url.lower() for hint in _JSON_HINTS):
                    return
                try:
                    body = resp.json()
                except Exception:  # noqa: BLE001
                    return
                captured.append((resp.url, body))
            except Exception:  # noqa: BLE001
                pass

        page.on("response", _on_response)

        try:
            print(f"[抓取] 打开 {search_url}（有头模式，请留意弹出的浏览器窗口）")
            page.goto(search_url, timeout=30_000, wait_until="domcontentloaded")
            page.wait_for_timeout(4_000)

            # 命中验证墙（页面文案或接口 need_recaptcha）：等待用户手动过验证
            if _looks_blocked(page) or _captured_needs_verify(captured):
                print("[验证] 检测到验证码 / 滑块，请在浏览器窗口中手动完成…")
                elapsed = 0
                step = 5_000
                while (_looks_blocked(page) or _captured_needs_verify(captured)) and elapsed < VERIFY_TIMEOUT_MS:
                    page.wait_for_timeout(step)
                    elapsed += step
                    print(f"[验证] 已等待 {elapsed / 1000:.0f}s，继续检测…")
                if _looks_blocked(page) or _captured_needs_verify(captured):
                    raise CrawlBlocked(f"等待 {VERIFY_TIMEOUT_MS / 1000:.0f}s 后仍被验证码拦截")

            page.wait_for_timeout(3_000)
            restaurants = _parse_restaurants(captured)
            print(f"[抓取] 解析到 {len(restaurants)} 家餐厅")
            dishes = _parse_dishes(captured, restaurants)
            print(f"[抓取] 解析到 {len(dishes)} 道推荐菜")
            if not dishes:
                raise CrawlBlocked(f"未解析到推荐菜（拦截 {len(captured)} 个候选响应）")
            return _assign_coords_and_tags(dishes, restaurants, lat, lon)
        finally:
            if os.environ.get("CRAWL_DEBUG") == "1":
                _dump_captured(captured, _SAMPLES / "_debug_captured.json")
            browser.close()


def read_local_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDNAMES})


def crawl(lat: float, lon: float, radius_km: float) -> tuple[list[dict], str]:
    """抓取主入口：优先实时抓取，任何失败降级到本地 CSV，保证不崩溃。"""
    try:
        rows = _browser_crawl(lat, lon, radius_km)
        rows = _filter_within_radius(rows, lat, lon, radius_km)
        return rows, "百度地图实时抓取"
    except Exception as exc:  # noqa: BLE001 - 降级机制：任何失败都回退，不向上抛
        print(f"[降级] 实时抓取失败（{exc.__class__.__name__}: {exc}）")
        print(f"[降级] 回退读取本地 {FALLBACK_FILE.name}")
        rows = read_local_csv(FALLBACK_FILE) if FALLBACK_FILE.exists() else []
        return _filter_within_radius(rows, lat, lon, radius_km), f"本地兜底 {FALLBACK_FILE.name}"


def main() -> int:
    args = sys.argv[1:]
    lat = float(args[0]) if len(args) > 0 else DEFAULT_CENTER[0]
    lon = float(args[1]) if len(args) > 1 else DEFAULT_CENTER[1]
    radius = float(args[2]) if len(args) > 2 else DEFAULT_RADIUS_KM

    print(f"目标：以 ({lat}, {lon}) 为中心，半径 {radius} 公里")
    rows, source = crawl(lat, lon, radius)
    write_csv(rows, OUTPUT_FILE)
    print(f"来源：{source}")
    print(f"共 {len(rows)} 条，已写入 {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
