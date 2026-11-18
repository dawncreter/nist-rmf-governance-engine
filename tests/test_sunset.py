from pathlib import Path

import pytest
from pydantic import ValidationError

from sunset import rank, score
from sunset.cli import main
from sunset.controls import CHECKS, assess, control_coverage
from sunset.inventory import Application, Controls, load_inventory
from sunset.playbook import playbook
from sunset.report import scorecard
from sunset.synthetic import generate, write

DATA = Path(__file__).resolve().parents[1] / "data" / "app_inventory.json"
GOOD = Controls(mfa=True, audit_logging=True, encryption_at_rest=True, encryption_in_transit=True,
                access_review_days=30, backup_tested=True)


def app(**kw) -> Application:
    base = dict(app_id="A1", name="App", owner="IT", business_criticality=3, active_users=500, annual_cost=50_000,
                controls=GOOD)
    base.update(kw)
    return Application(**base)


# --- controls ---------------------------------------------------------------------
def test_fully_controlled_app_has_no_gaps():
    assert assess(app(data_classes=["PII"])) == []


def test_gaps_carry_nist_iso_and_gdpr_references():
    a = app(data_classes=["PII"], critical_cves=2, days_since_patch=200, vendor_supported=False,
            controls=Controls())
    gaps = {g.key: g for g in assess(a)}
    assert set(gaps) == {c.key for c in CHECKS}
    assert gaps["mfa"].nist == "IA-2(1)" and gaps["mfa"].iso == "A.8.5" and gaps["mfa"].gdpr == "Art. 32"
    assert gaps["patching"].gdpr is None


def test_encryption_at_rest_only_applies_to_personal_data():
    keys = {g.key for g in assess(app(data_classes=["public"], controls=Controls(encryption_in_transit=True)))}
    assert "enc_rest" not in keys and "mfa" in keys


def test_control_coverage():
    cov = control_coverage([app(), app(app_id="A2", controls=Controls())])
    assert cov["mfa"] == 0.5 and cov["enc_rest"] == 1.0  # no personal-data apps in scope


# --- scoring -----------------------------------------------------------------------
def test_risky_low_value_app_is_retired_and_ranked_first():
    risky = app(app_id="OLD", business_criticality=1, active_users=10, annual_cost=200_000, critical_cves=4,
                high_cves=8, days_since_patch=700, vendor_supported=False, data_classes=["PII"],
                controls=Controls())
    healthy = app(app_id="NEW", business_criticality=5, active_users=3000)
    ranked = rank([healthy, risky])
    assert ranked[0].app.app_id == "OLD" and ranked[0].disposition == "Retire"
    assert ranked[1].disposition == "Retain" and ranked[0].spi > ranked[1].spi


@pytest.mark.parametrize("replacement,expected", [(False, "Remediate"), (True, "Modernize")])
def test_risky_critical_app_is_fixed_not_retired(replacement, expected):
    a = app(business_criticality=5, active_users=2500, annual_cost=2_000_000, critical_cves=5, high_cves=10,
            days_since_patch=400, vendor_supported=False, data_classes=["PCI"], controls=Controls(),
            replacement_available=replacement)
    assert score(a).disposition == expected


def test_cheap_unused_app_is_retired_on_cost():
    s = score(app(business_criticality=1, active_users=2, annual_cost=20_000))
    assert s.risk < 0.5 and s.disposition == "Retire"


def test_scores_are_bounded():
    s = score(app(critical_cves=50, high_cves=50, days_since_patch=5000, annual_cost=10**9, active_users=0,
                  vendor_supported=False, replacement_available=True, data_classes=["PII"], controls=Controls()))
    assert all(0 <= v <= 1 for v in (s.security, s.cost, s.debt, s.regulatory)) and s.spi <= 100


def test_inventory_validation():
    with pytest.raises(ValidationError):
        app(business_criticality=9)


# --- outputs -------------------------------------------------------------------------
def test_playbook_covers_data_integrations_and_audit_evidence():
    a = score(app(data_classes=["PII", "financial", "unknown"], integrations=["ERP"]))
    steps = "\n".join(playbook(a))
    for needle in ("GDPR Art. 5", "7 years", "Classify", "ERP", "MP-6", "CM-8", "Art. 30"):
        assert needle in steps
    assert "Art. 30" not in "\n".join(playbook(score(app())))


def test_scorecard_and_bundled_inventory():
    results = rank(load_inventory(DATA))
    assert len(results) == 25
    md = scorecard(results)
    assert "Portfolio Risk Scorecard" in md and "IA-2(1)" in md and "/yr" in md


def test_generator_is_deterministic(tmp_path):
    assert generate(5, seed=1) == generate(5, seed=1)
    assert len(generate(30)) == 30 and generate(30)[-1]["name"].endswith("2")
    out = tmp_path / "inv.json"
    write(out, n=3)
    assert len(load_inventory(out)) == 3


def test_cli(capsys, tmp_path):
    assert main(["scorecard"]) == 0
    assert main(["playbook"]) == 0
    assert main(["playbook", "APP-001"]) == 0
    assert main(["playbook", "NOPE"]) == 1
    healthy = tmp_path / "ok.json"
    healthy.write_text("[]")
    assert main(["--inventory", str(healthy), "playbook"]) == 1
    assert "Decommissioning playbook" in capsys.readouterr().out
