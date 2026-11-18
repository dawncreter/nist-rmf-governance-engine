"""Application inventory model and loader."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class Controls(BaseModel):
    mfa: bool = False
    audit_logging: bool = False
    encryption_at_rest: bool = False
    encryption_in_transit: bool = False
    access_review_days: int = Field(default=365, ge=0)
    backup_tested: bool = False


class Application(BaseModel):
    app_id: str
    name: str
    owner: str
    business_criticality: int = Field(ge=1, le=5, description="1 = nice to have, 5 = business critical")
    active_users: int = Field(ge=0)
    annual_cost: float = Field(ge=0)
    critical_cves: int = Field(default=0, ge=0)
    high_cves: int = Field(default=0, ge=0)
    days_since_patch: int = Field(default=0, ge=0)
    vendor_supported: bool = True
    replacement_available: bool = False
    data_classes: list[str] = Field(default_factory=list, description="e.g. PII, PCI, financial, public")
    integrations: list[str] = Field(default_factory=list)
    controls: Controls = Field(default_factory=Controls)


def load_inventory(path: str | Path) -> list[Application]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Application.model_validate(r) for r in rows]
