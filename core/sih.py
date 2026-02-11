"""
System Integrator Hub (SIH)
Cyber Resilience Toolkit (CRT)
--------------------------------------------------------

Backbone responsibilities:

1) Load & validate all CRT catalogues
2) Respect backbone vs append-only rules
3) Expose a thin, stable API for module consumption

The SIH never:
- generates output
- renders UI
- calls AI
- performs policy, risk or assurance actions
"""

from __future__ import annotations
import os
import pandas as pd
from typing import Dict, Any, List, Optional


BACKBONE_CATALOGUES = [
    "CRT-C",   # Controls
    "CRT-F",   # Failures
    "CRT-N",   # Compensations
    "CRT-POL", # Policies
    "CRT-STD", # Standards
]

APPEND_ONLY_CATALOGUES = [
    "CRT-LR",  # Legal / Regulatory requirements
    "CRT-REQ", # Requirements (internal / external)
    "CRT-D",   # Data & Classification
    "CRT-AS",  # Assets & Surface
    "CRT-I",   # Identity & Trust Anchors
    "CRT-SC",  # Supply-Chain & Vendors
    "CRT-T",   # Telemetry & Signal Sources
    "CRT-G",   # Control Groups / Domains
]

class SystemIntegratorHub:
    """
    The SIH is instantiated once at app load and shared across modules.
    """

    def __init__(self, base_path: str):
        self.base_path = base_path
        self.catalogues: Dict[str, pd.DataFrame] = {}

        # Load catalogues at startup
        self._load_all_catalogues()

    # --------------------------------------------------------------
    # Catalogue loading
    # --------------------------------------------------------------
    def _load_catalogue(self, filename: str) -> pd.DataFrame:
        path = os.path.join(self.base_path, filename)

        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            df = pd.read_csv(path, dtype=str).fillna("")
            return df
        except Exception:
            return pd.DataFrame()

    def _load_all_catalogues(self):
        """
        Loads all CRT CSVs into memory.

        Backbones are treated as authoritative.
        Append-only catalogues may have user extensions applied at the CSV level,
        but SIH does not merge or rewrite them.
        """
        self.catalogues["CRT-C"] = self._load_catalogue("CRT-C.csv")
        self.catalogues["CRT-F"] = self._load_catalogue("CRT-F.csv")
        self.catalogues["CRT-N"] = self._load_catalogue("CRT-N.csv")
        self.catalogues["CRT-POL"] = self._load_catalogue("CRT-POL.csv")
        self.catalogues["CRT-STD"] = self._load_catalogue("CRT-STD.csv")

        self.catalogues["CRT-LR"]  = self._load_catalogue("CRT-LR.csv")
        self.catalogues["CRT-REQ"] = self._load_catalogue("CRT-REQ.csv")
        self.catalogues["CRT-D"]   = self._load_catalogue("CRT-D.csv")
        self.catalogues["CRT-AS"]  = self._load_catalogue("CRT-AS.csv")
        self.catalogues["CRT-I"]   = self._load_catalogue("CRT-I.csv")
        self.catalogues["CRT-SC"]  = self._load_catalogue("CRT-SC.csv")
        self.catalogues["CRT-T"]   = self._load_catalogue("CRT-T.csv")
        self.catalogues["CRT-G"]   = self._load_catalogue("CRT-G.csv")


    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------
    def get_catalogue(self, name: str) -> pd.DataFrame:
        """
        Return the requested catalogue as a DataFrame.
        Always returns a valid DataFrame (possibly empty).
        """
        return self.catalogues.get(name, pd.DataFrame()).copy()

    def get_all_entities(self, catalogue: str) -> List[Dict[str, Any]]:
        """
        Return the entire catalogue as dicts.
        """
        df = self.get_catalogue(catalogue)
        return df.to_dict(orient="records")

    def resolve_entity(self, catalogue: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single entity by ID.
        """
        df = self.get_catalogue(catalogue)
        if df.empty:
            return None

        key_col_candidates = [
            "control_id", "failure_id", "n_id", "policy_id",
            "standard_id", "lr_id",
            "requirement_id", "requirement_set_id",
            "d_id", "as_id",
            "i_id", "sc_id", "telemetry_id",
            "group_id",
        ]


        for key in key_col_candidates:
            if key in df.columns:
                row = df[df[key] == entity_id]
                if not row.empty:
                    return row.to_dict(orient="records")[0]

        return None

    def build_relationships(self, primary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build structural relationships for an entity.
        Uses CRT-C → CRT-F → CRT-N → LR/REQ and AS/D/I/SC/T as needed.
        Deterministic and catalogue-driven.
        """
        rels: List[Dict[str, Any]] = []
        if not primary:
            return rels

        # Example: if entity is a control, map failures and compensations
        if "control_id" in primary:
            cid = primary["control_id"]

            failures = self.get_catalogue("CRT-F")
            if not failures.empty and "mapped_control_ids" in failures.columns:
                for _, row in failures.iterrows():
                    if cid in (row.get("mapped_control_ids") or ""):
                        rels.append({
                            "from_type": "control",
                            "from_id": cid,
                            "rel": "failure_implication",
                            "to_type": "failure",
                            "to_id": row.get("failure_id", "")
                        })

            comp = self.get_catalogue("CRT-N")
            if not comp.empty and "mapped_control_ids" in comp.columns:
                for _, row in comp.iterrows():
                    if cid in (row.get("mapped_control_ids") or ""):
                        rels.append({
                            "from_type": "control",
                            "from_id": cid,
                            "rel": "compensated_by",
                            "to_type": "compensation",
                            "to_id": row.get("n_id", "")
                        })

        # Additional relationship logic for assets/data/identity/vendors/telemetry
        # can be added here as the catalogues mature.

        return rels

    # --------------------------------------------------------------
    # Bundle validation
    # --------------------------------------------------------------
    def validate_bundle(self, bundle: Dict[str, Any]) -> bool:
        """
        Ensures the outbound bundle matches the locked schema.
        Used before export or AI handoff.
        """
        required_keys = {
            "bundle_type", "module", "primary_entity",
            "entities", "relationships", "structural_findings",
            "guardrails"
        }

        return required_keys.issubset(bundle.keys())


# --------------------------------------------------------------
# Singleton accessor
# --------------------------------------------------------------
_sih_instance: Optional[SystemIntegratorHub] = None

def get_sih(base_path: str) -> SystemIntegratorHub:
    """
    Accessor for a process-wide SIH instance.
    """
    global _sih_instance
    if _sih_instance is None:
        _sih_instance = SystemIntegratorHub(base_path)
    return _sih_instance
