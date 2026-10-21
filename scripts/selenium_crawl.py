"""半自动抓取美团外卖当前页面的餐厅 / 菜品 / 价格（Selenium 有头浏览器 + 手动登录）。

流程（严格按此执行）：
    1. 启动一个可见（有头）的 Chrome 窗口，自动打开美团外卖网页版；
    2. 程序暂停最多 60 秒（也可回到终端按回车提前继续），你在浏览器里手动扫码登录，
       并搜索到「中原工学院」附近、展示菜品列表的页面；
    3. 时间到后程序自动接管，通过 DOM（By.CSS_SELECTOR / XPath）解析当前页面的
       餐厅名称、菜品名称、价格；
    4. 结果保存到 samples/selenium_menu.csv，并在终端打印前若干条预览。

任何异常直接打印错误并退出，不会死循环。

用法：
    python scripts/selenium_crawl.py [目标URL]

环境变量：
    CHROMEDRIVER_PATH   chromedriver.exe 的路径（默认自动使用 drivers/chromedriver.exe）

说明：美团 / 饿了么 DOM 的 class 名带哈希后缀、频繁变化，本脚本用 contains 关键字做
启发式匹配，抓取效果取决于当前页面结构；抓不到时打印提示，不会崩溃。
"""

from __future__ import annotations

import csv
import os
import re
import sys
import threading
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

_PROJECT = Path(__file__).resolve().parents[1]
_OUTPUT_FILE = _PROJECT / "samples" / "selenium_menu.csv"
_DEFAULT_DRIVER = _PROJECT / "drivers" / "chromedriver.exe"

FIELDNAMES = ["restaurant", "name", "category", "price", "latitude", "longitude"]
DEFAULT_CENTER = (34.626, 113.705)  # 中原工学院
DEFAULT_URL = "https://waimai.meituan.com/"

# class 关键字（用 contains 模糊匹配，需按站点实际 DOM 持续维护）
_RESTAURANT_HINTS = ("shop-name", "restaurant-name", "store-name", "poi-name", "shopName")
_DISH_HINTS = ("food-name", "foodname", "dish-name", "dishname", "item-name", "spu-name", "product-name")
_PRICE_HINTS = ("food-price", "foodprice", "dish-price", "item-price", "sale-price", "price", "salePrice")

_PRICE_RE = re.compile(r"[¥￥]\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*元")
_NOISE_WORDS = {"月售", "已售", "份", "起", "评价", "人", "元", "¥", "￥"}


def _chrome_options() -> Options:
    opts = Options()
    # 有头模式：不设 headless，弹出一个可见的 Chrome 窗口
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1400,900")
    return opts


def _make_driver() -> webdriver.Chrome:
    opts = _chrome_options()
    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    if not driver_path and _DEFAULT_DRIVER.exists():
        driver_path = str(_DEFAULT_DRIVER)
    if driver_path and Path(driver_path).exists():
        return webdriver.Chrome(service=Service(driver_path), options=opts)
    # 回退：交给 Selenium Manager 自动下载驱动
    return webdriver.Chrome(options=opts)


def _pause_for_manual(seconds: int = 60) -> None:
    """暂停程序，等待用户手动扫码登录并搜索；超时或回车后自动继续。"""
    print("=" * 60)
    print("请在浏览器中：")
    print("  1) 扫码登录美团外卖；")
    print("  2) 搜索并打开「中原工学院」附近、能看到菜品列表的页面。")
    print(f"程序将在 {seconds} 秒后自动接管（也可回到终端按回车提前继续）...")
    print("=" * 60)

    done = threading.Event()

    def _read() -> None:
        try:
            input()
        except Exception:  # noqa: BLE001 - 非交互环境 input 会抛 EOF，直接视为继续
            pass
        done.set()

    threading.Thread(target=_read, daemon=True).start()
    done.wait(timeout=seconds)
    print("[接管] 开始解析当前页面 DOM ...")


def _parse_price(text) -> float | None:
    if not text:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(text))
    return float(m.group()) if m else None


def _extract_restaurant(driver) -> str:
    """解析当前页面的餐厅名称。"""
    for hint in _RESTAURANT_HINTS:
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, f"[class*='{hint}']"):
                t = (el.text or "").strip()
                if t:
                    return t
        except Exception:  # noqa: BLE001
            continue
    # 回退：取 h1 或标题元素
    for sel in ("h1", "[class*='title']", "[class*='name']"):
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                t = (el.text or "").strip()
                if t and 2 <= len(t) <= 30:
                    return t
        except Exception:  # noqa: BLE001
            continue
    return ""


def _name_near_price(price_el) -> str:
    """从一个价格元素出发，向上找父级，把去除价格后的文本当作菜名。"""
    node = price_el
    for _ in range(4):
        try:
            node = node.find_element(By.XPATH, "..")
        except Exception:  # noqa: BLE001
            return ""
        full = (node.text or "").strip()
        if not full:
            continue
        cleaned = _PRICE_RE.sub(" ", full)
        cleaned = re.sub(r"\d+(?:\.\d+)?", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ¥￥起/元·-")
        parts = [p for p in re.split(r"[\s\n]+", cleaned) if 1 <= len(p) <= 20 and p not in _NOISE_WORDS]
        if parts:
            return parts[0]
    return ""


def _extract_dishes(driver, restaurant: str) -> list[dict]:
    """解析当前页面菜品：价格元素锚定 + class 关键字两种策略，按菜名去重。"""
    dishes: dict[str, dict] = {}

    def _add(name: str, price) -> None:
        if not name or name == restaurant or name in dishes:
            return
        dishes[name] = {
            "restaurant": restaurant,
            "name": name,
            "category": "",
            "price": price,
            "latitude": DEFAULT_CENTER[0],
            "longitude": DEFAULT_CENTER[1],
        }

    # 策略一：所有含 ¥/￥ 的元素 + 价格 class 元素，锚定菜名
    price_els = []
    try:
        price_els += driver.find_elements(By.XPATH, "//*[contains(text(), '¥') or contains(text(), '￥')]")
    except Exception:  # noqa: BLE001
        pass
    for hint in _PRICE_HINTS:
        try:
            price_els += driver.find_elements(By.CSS_SELECTOR, f"[class*='{hint}']")
        except Exception:  # noqa: BLE001
            pass

    for pe in price_els:
        try:
            price = _parse_price(pe.text)
            if price is None:
                continue
            _add(_name_near_price(pe), price)
        except Exception:  # noqa: BLE001
            continue

    # 策略二：按菜名 class 找元素，再从父级文本里配价格
    for hint in _DISH_HINTS:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, f"[class*='{hint}']")
        except Exception:  # noqa: BLE001
            continue
        for el in els:
            try:
                name = (el.text or "").strip()
                if not name or len(name) > 25:
                    continue
                price = None
                try:
                    parent = el.find_element(By.XPATH, "..")
                    m = _PRICE_RE.search(parent.text or "")
                    price = _parse_price(m.group(0)) if m else None
                except Exception:  # noqa: BLE001
                    price = None
                _add(name, price)
            except Exception:  # noqa: BLE001
                continue

    return list(dishes.values())


def _save_csv(dishes: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for d in dishes:
            writer.writerow({k: d.get(k, "") for k in FIELDNAMES})


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    driver = None
    try:
        print(f"[启动] 打开 {url}")
        driver = _make_driver()
        driver.get(url)
        _pause_for_manual(60)

        restaurant = _extract_restaurant(driver)
        dishes = _extract_dishes(driver, restaurant)
        print(f"[结果] 餐厅：{restaurant or '（未识别）'}，解析到 {len(dishes)} 道菜品")

        if not dishes:
            print("[提示] 未解析到菜品，请确认当前页面已展示菜品列表，或调整 _DISH_HINTS/_PRICE_HINTS 关键字。")
        else:
            _save_csv(dishes, _OUTPUT_FILE)
            print(f"[保存] 已写入 {_OUTPUT_FILE}")
            print("-" * 60)
            for d in dishes[:10]:
                print(f"  {d['name']}  ¥{d['price'] if d['price'] is not None else '?'}")
            if len(dishes) > 10:
                print(f"  ... 共 {len(dishes)} 条")
        return 0
    except Exception as exc:  # noqa: BLE001 - 任何异常打印报错并退出，不死循环
        print(f"[报错] {exc.__class__.__name__}: {exc}")
        return 1
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    raise SystemExit(main())
