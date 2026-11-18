"""Generate a fictional application inventory (``data/app_inventory.json`` was produced with seed 3)."""
from __future__ import annotations

import json
import random
from pathlib import Path

NAMES = ["Expense Tracker", "Legacy CRM", "Vendor Portal", "HR Onboarding", "Audit Workpapers", "Time Entry",
         "Contract Vault", "Sales Dashboard", "Asset Register", "Survey Tool", "Payroll Bridge", "Policy Library",
         "Travel Booking", "Risk Register", "Legacy Reporting", "Customer Portal", "Ticketing (old)", "Doc Scanner",
         "Benefits Portal", "Field Service App", "Pricing Engine", "Intranet v2", "Training LMS", "Data Mart",
         "Supplier Scorecard"]
OWNERS = ["Finance", "Sales Ops", "HR", "Audit", "IT", "Legal", "Procurement", "Risk"]
DATA = [["PII"], ["financial"], ["PII", "financial"], ["public"], ["PCI", "PII"], []]


def generate(n: int = 25, seed: int = 3) -> list[dict]:
    rng = random.Random(seed)
    apps = []
    for i, name in enumerate((NAMES * 4)[:n]):
        legacy = rng.random() < 0.4
        users = rng.choice([8, 25, 60, 150, 400, 1200, 3500])
        apps.append({
            "app_id": f"APP-{i + 1:03d}",
            "name": name if i < len(NAMES) else f"{name} {i // len(NAMES) + 1}",
            "owner": rng.choice(OWNERS),
            "business_criticality": rng.randint(1, 3) if legacy else rng.randint(2, 5),
            "active_users": users,
            "annual_cost": round(rng.uniform(15_000, 400_000 if legacy else 250_000), -2),
            "critical_cves": rng.randint(1, 6) if legacy else rng.choice([0, 0, 0, 1]),
            "high_cves": rng.randint(2, 12) if legacy else rng.randint(0, 3),
            "days_since_patch": rng.randint(120, 900) if legacy else rng.randint(5, 60),
            "vendor_supported": not legacy or rng.random() < 0.3,
            "replacement_available": rng.random() < (0.6 if legacy else 0.2),
            "data_classes": rng.choice(DATA),
            "integrations": rng.sample(["SSO", "ERP", "Data warehouse", "Email gateway", "Payroll"], rng.randint(0, 3)),
            "controls": {
                "mfa": rng.random() < (0.3 if legacy else 0.9),
                "audit_logging": rng.random() < (0.4 if legacy else 0.9),
                "encryption_at_rest": rng.random() < (0.4 if legacy else 0.95),
                "encryption_in_transit": rng.random() < (0.6 if legacy else 1.0),
                "access_review_days": rng.choice([30, 90, 180, 365] if legacy else [30, 60, 90]),
                "backup_tested": rng.random() < (0.3 if legacy else 0.8),
            },
        })
    return apps


def write(path: str | Path, n: int = 25, seed: int = 3) -> None:
    Path(path).write_text(json.dumps(generate(n, seed), separators=(",", ":")), encoding="utf-8")
