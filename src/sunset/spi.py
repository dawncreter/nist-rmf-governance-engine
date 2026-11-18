"""Sunset Priority Index (SPI) and disposition.

Four 0-1 component scores:
    security   = min(1, (5*critical + 2*high) / 25) * 0.5 + (unsupported) * 0.2 + (gap severity / max) * 0.3
    cost       = min(1, cost_per_user / 2,000)
    debt       = min(1, days_since_patch / 365) * 0.6 + (unsupported) * 0.4
    regulatory = (personal data) * share of high-severity gaps that GDPR Art. 32 also cares about

    risk  = 0.45*security + 0.15*debt + 0.15*regulatory + 0.25*cost      (how much the app costs us to keep)
    value = (criticality - 1) / 4 * 0.8 + min(1, users / 2,000) * 0.2   (how much the business needs it)

    SPI = 100 * risk * (1 - 0.6*value) + 15 * replacement_available, capped at 100

Disposition (risk vs. value quadrant):
    risk >= 0.5 and value <  0.5  -> Retire
    risk >= 0.5 and value >= 0.5  -> Remediate (or Modernize if a replacement exists)
    risk <  0.5 and value <  0.25 -> Retire (cost only)
    otherwise                     -> Retain
"""
from __future__ import annotations

from dataclasses import dataclass

from .controls import CHECKS, PERSONAL_DATA, Gap, assess
from .inventory import Application

MAX_GAP = sum(c.severity for c in CHECKS)


@dataclass
class Assessment:
    app: Application
    gaps: list[Gap]
    security: float
    cost: float
    debt: float
    regulatory: float
    risk: float
    value: float
    spi: float
    disposition: str


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def score(app: Application) -> Assessment:
    gaps = assess(app)
    unsupported = 0.0 if app.vendor_supported else 1.0
    security = _clip(min(1, (5 * app.critical_cves + 2 * app.high_cves) / 25) * 0.5 + unsupported * 0.2
                     + sum(g.severity for g in gaps) / MAX_GAP * 0.3)
    cost = _clip(app.annual_cost / max(app.active_users, 1) / 2_000)
    debt = _clip(min(1, app.days_since_patch / 365) * 0.6 + unsupported * 0.4)
    personal = bool(PERSONAL_DATA & set(app.data_classes))
    high_gdpr = [g for g in gaps if g.gdpr and g.severity == 3]
    regulatory = _clip(len(high_gdpr) / 3) if personal else 0.0
    risk = round(0.45 * security + 0.15 * debt + 0.15 * regulatory + 0.25 * cost, 3)
    value = round((app.business_criticality - 1) / 4 * 0.8 + min(1, app.active_users / 2_000) * 0.2, 3)
    spi = round(min(100.0, 100 * risk * (1 - 0.6 * value) + (15 if app.replacement_available else 0)), 1)
    if risk >= 0.5:
        disposition = "Retire" if value < 0.5 else ("Modernize" if app.replacement_available else "Remediate")
    else:
        disposition = "Retire" if value < 0.25 else "Retain"
    return Assessment(app, gaps, round(security, 3), round(cost, 3), round(debt, 3), round(regulatory, 3),
                      risk, value, spi, disposition)


def rank(apps: list[Application]) -> list[Assessment]:
    return sorted((score(a) for a in apps), key=lambda s: s.spi, reverse=True)
