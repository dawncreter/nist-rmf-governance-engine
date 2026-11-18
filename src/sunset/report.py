"""Executive scorecard in Markdown."""
from __future__ import annotations

from collections import Counter

from .controls import CHECKS, control_coverage
from .spi import Assessment


def scorecard(results: list[Assessment], top: int = 10) -> str:
    apps = [r.app for r in results]
    disp = Counter(r.disposition for r in results)
    retire = [r for r in results if r.disposition == "Retire"]
    savings = sum(r.app.annual_cost for r in retire)
    crit = sum(r.app.critical_cves for r in retire)
    cov = control_coverage(apps)
    lines = [
        "# Application Portfolio Risk Scorecard",
        "",
        f"**Applications assessed:** {len(results)} · "
        + " · ".join(f"**{k}:** {disp.get(k, 0)}" for k in ("Retire", "Remediate", "Modernize", "Retain")),
        "",
        f"Retiring the recommended applications removes **${savings:,.0f}/yr** in run cost and "
        f"**{crit} critical vulnerabilities**.",
        "",
        "## Highest sunset priority",
        "| SPI | App | Owner | Disposition | Risk | Value | Gaps |",
        "|---|---|---|---|---|---|---|",
        *[f"| {r.spi} | {r.app.name} | {r.app.owner} | {r.disposition} | {r.risk:.2f} | {r.value:.2f} | "
          f"{', '.join(g.nist for g in r.gaps) or '—'} |" for r in results[:top]],
        "",
        "## Control coverage (NIST SP 800-53 / ISO 27001)",
        "| Control | NIST | ISO | Passing |",
        "|---|---|---|---|",
        *[f"| {c.title} | {c.nist} | {c.iso} | {cov[c.key]:.0%} |" for c in CHECKS],
    ]
    return "\n".join(lines)
