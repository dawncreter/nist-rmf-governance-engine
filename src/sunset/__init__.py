"""Application sunset & compliance engine.

NIST SP 800-53 / ISO 27001 gap assessment, Sunset Priority Index and decommissioning playbooks.
"""
from .spi import Assessment, rank, score

__all__ = ["Assessment", "rank", "score"]
__version__ = "0.1.0"
