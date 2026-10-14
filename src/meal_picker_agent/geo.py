"""地理计算：Haversine 距离与球面偏移。"""

from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """两点间的球面直线距离（公里）。"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def offset_km(lat: float, lon: float, km: float, bearing_deg: float) -> tuple[float, float]:
    """从 (lat, lon) 沿方位角 bearing_deg（0=北，90=东）偏移 km 公里，返回新经纬度。"""
    d_r = km / EARTH_RADIUS_KM
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lam1 = math.radians(lon)

    phi2 = math.asin(
        math.sin(phi1) * math.cos(d_r) + math.cos(phi1) * math.sin(d_r) * math.cos(theta)
    )
    lam2 = lam1 + math.atan2(
        math.sin(theta) * math.sin(d_r) * math.cos(phi1),
        math.cos(d_r) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), math.degrees(lam2)
