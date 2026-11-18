"""Generate a decommissioning playbook with audit evidence for a retiring application."""
from __future__ import annotations

from .controls import PERSONAL_DATA
from .spi import Assessment

RETENTION = {
    "financial": "Archive to records system; retain per finance retention schedule (commonly 7 years).",
    "PII": ("Export only what retention rules require; securely delete the rest and record the deletion "
            "(GDPR Art. 5(1)(e), 17)."),
    "PCI": "Securely delete cardholder data; obtain PCI DSS scope-reduction sign-off.",
    "PHI": "Retain per health-records schedule; document disposal method.",
    "public": "No retention requirement; delete.",
}


def playbook(a: Assessment) -> list[str]:
    app = a.app
    steps = [
        f"1. Confirm decision with owner ({app.owner}) and record the SPI rationale (SPI {a.spi}, risk {a.risk}, "
        f"value {a.value}).",
        f"2. Notify {app.active_users} active users; publish the read-only date and the replacement path.",
        "3. Freeze changes (CM-3) and take a final verified backup (CP-9).",
    ]
    n = 4
    for dc in app.data_classes or ["public"]:
        steps.append(f"{n}. Data — {dc}: {RETENTION.get(dc, 'Classify, then apply the matching retention rule.')}")
        n += 1
    for integ in app.integrations:
        steps.append(f"{n}. Re-point or retire integration: {integ}; confirm no downstream failures.")
        n += 1
    steps += [
        f"{n}. Revoke all accounts, service credentials and API keys (AC-2); rotate shared secrets.",
        f"{n + 1}. Remove DNS records, firewall rules and certificates; release licenses and infrastructure.",
        f"{n + 2}. Sanitize or destroy storage media (MP-6) and capture the certificate of destruction.",
        f"{n + 3}. Update the CMDB / system inventory (CM-8) and the risk register; close open POA&M items.",
        f"{n + 4}. File the evidence pack (approvals, data disposition, access revocation, sanitization) for audit.",
    ]
    if PERSONAL_DATA & set(app.data_classes):
        steps.append(f"{n + 5}. Update the record of processing activities (GDPR Art. 30).")
    return steps
