"""
AI Bundle Builder
Cyber Resilience Toolkit (CRT)
--------------------------------------------------------

This module constructs normalised AI bundles for every CRT module.
Bundles follow the locked schema defined in crt_modules_run_order.txt.

The Bundle Builder never:
- embeds narrative text
- generates recommendations
- interprets catalogue content
- changes ontology
- performs analysis

It simply assembles structured data into the approved AI bundle format.
"""

from __future__ import annotations
from typing import Dict, Any, List
import json


# --------------------------------------------------------------
# Locked bundle schema
# --------------------------------------------------------------

def build_ai_bundle(
    *,
    module: str,
    bundle_type: str,
    primary_entity: Dict[str, Any],
    entities: Dict[str, List[Dict[str, Any]]],
    relationships: List[Dict[str, Any]],
    structural_findings: Dict[str, Any],
    guardrails: Dict[str, bool]
) -> Dict[str, Any]:
    """
    Construct a fully normalised AI bundle using the locked schema.

    All inputs must already be:
    - dictionary / list structures
    - deterministic
    - free of free-text commentary

    This function is intentionally minimal.

    Parameters
    ----------
    module : str
        The module responsible for generating this bundle.

    bundle_type : str
        One of the approved bundle types:
        architecture | exposure | metrics | simulation |
        supply_chain | identity | data | governance | signals | observation

    primary_entity : dict
        The main entity the module is analysing.
        Example:
        { "type": "data_domain", "id": "D-0003" }

    entities : dict[str, list[dict]]
        Structured catalogue slices:
        {
          "assets": [...],
          "identities": [...],
          "data_domains": [...],
          "vendors": [...],
          "controls": [...],
          "failures": [...],
          "telemetry": [...]
        }

    relationships : list[dict]
        Structural relationships (control → failure, asset → control, etc)

    structural_findings : dict
        Gaps, compensations, paths, coverage arrays

    guardrails : dict
        Safety flags for AI interpretation
    """

    return {
        "bundle_type": bundle_type,
        "module": module,
        "primary_entity": primary_entity,
        "entities": {
            "assets": entities.get("assets", []),
            "identities": entities.get("identities", []),
            "data_domains": entities.get("data_domains", []),
            "vendors": entities.get("vendors", []),
            "controls": entities.get("controls", []),
            "failures": entities.get("failures", []),
            "telemetry": entities.get("telemetry", []),
        },
        "relationships": relationships,
        "structural_findings": {
            "gaps": structural_findings.get("gaps", []),
            "compensations": structural_findings.get("compensations", []),
            "coverage": structural_findings.get("coverage", {}),
            "propagation_paths": structural_findings.get("propagation_paths", []),
        },
        "guardrails": {
            "no_advice": True,
            "no_configuration": True,
            "no_assurance": True,
            **guardrails   # allows for future safe flags
        }
    }


# --------------------------------------------------------------
# Utility: Pretty-print bundle for UI
# --------------------------------------------------------------

def bundle_to_pretty_json(bundle: Dict[str, Any]) -> str:
    """
    Produce a deterministic, prettified JSON string
    for display in Streamlit or export panels.
    """
    try:
        return json.dumps(bundle, indent=2, ensure_ascii=False)
    except Exception:
        return "{}"
