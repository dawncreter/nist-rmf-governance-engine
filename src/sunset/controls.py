"""Baseline control checks mapped to NIST SP 800-53 Rev. 5, ISO/IEC 27001:2022 Annex A and GDPR Art. 32.

Each check is a small, testable predicate. A failed check becomes a ``Gap`` that carries every
framework reference, so one finding satisfies several audit requirements at once.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .inventory import Application

PERSONAL_DATA = {"PII", "PHI", "PCI"}


@dataclass(frozen=True)
class Check:
    key: str
    title: str
    nist: str
    iso: str
    severity: int  # 1 low .. 3 high
    passes: Callable[[Application], bool]
    personal_data_only: bool = False


@dataclass(frozen=True)
class Gap:
    app_id: str
    key: str
    title: str
    nist: str
    iso: str
    gdpr: str | None
    severity: int


CHECKS: tuple[Check, ...] = (
    Check("mfa", "Multi-factor authentication", "IA-2(1)", "A.8.5", 3, lambda a: a.controls.mfa),
    Check("logging", "Audit logging enabled", "AU-2, AU-12", "A.8.15", 2, lambda a: a.controls.audit_logging),
    Check("enc_rest", "Encryption at rest", "SC-28", "A.8.24", 3, lambda a: a.controls.encryption_at_rest,
          personal_data_only=True),
    Check("enc_transit", "Encryption in transit", "SC-8", "A.8.24", 3, lambda a: a.controls.encryption_in_transit),
    Check("access_review", "Access reviewed at least every 90 days", "AC-2(3)", "A.5.18", 2,
          lambda a: a.controls.access_review_days <= 90),
    Check("backup", "Backups tested", "CP-9", "A.8.13", 1, lambda a: a.controls.backup_tested),
    Check("patching", "Critical vulnerabilities remediated within 30 days", "SI-2", "A.8.8", 3,
          lambda a: a.critical_cves == 0 or a.days_since_patch <= 30),
    Check("supported", "Vendor-supported components", "SA-22", "A.8.8", 3, lambda a: a.vendor_supported),
)


def assess(app: Application) -> list[Gap]:
    """Return every failed control for one application."""
    personal = bool(PERSONAL_DATA & set(app.data_classes))
    gaps = []
    for c in CHECKS:
        if c.personal_data_only and not personal:
            continue
        if not c.passes(app):
            gdpr = "Art. 32" if personal and c.key in {"enc_rest", "enc_transit", "mfa", "access_review", "backup"} \
                else None
            gaps.append(Gap(app.app_id, c.key, c.title, c.nist, c.iso, gdpr, c.severity))
    return gaps


def control_coverage(apps: list[Application]) -> dict[str, float]:
    """Share of applicable applications passing each control (0-1)."""
    out = {}
    for c in CHECKS:
        scope = [a for a in apps if not c.personal_data_only or PERSONAL_DATA & set(a.data_classes)]
        out[c.key] = round(sum(c.passes(a) for a in scope) / len(scope), 3) if scope else 1.0
    return out
