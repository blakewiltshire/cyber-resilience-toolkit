"""
Module Pattern (5-Part Skeleton)
Cyber Resilience Toolkit (CRT)
--------------------------------------------------------

This module provides shared structures and helpers for CRT modules.

It encodes the locked 5-part pattern:

    1) collect_input()
    2) extract_properties()
    3) build_structural_mapping()
    4) render_output_panels()
    5) build_ai_context_bundle()

The goal is to keep each module consistent, deterministic, and aligned
to the AI bundle schema defined in crt_modules_run_order.txt.

This module never:
- imports Streamlit
- calls AI
- performs policy, risk, or assurance actions
- changes catalogue content

It only helps modules organise structural data and construct bundles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from core.bundle_builder import build_ai_bundle


# -------------------------------------------------------------------
# Shared state container for CRT modules
# -------------------------------------------------------------------


@dataclass
class CRTModuleState:
    """
    Shared state used by CRT modules to organise structural data
    before building an AI bundle.

    Fields map directly to the locked bundle schema.
    """

    # 1) Primary entity (what this module is "about")
    #    e.g. { "type": "data_domain", "id": "D-0003" }
    primary_entity: Dict[str, Any] = field(default_factory=dict)

    # 2) Entities (catalogue slices) grouped by type
    #    Each list element should be a dict representing a row or record
    entities: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=lambda: {
            "assets": [],
            "identities": [],
            "data_domains": [],
            "vendors": [],
            "controls": [],
            "failures": [],
            "telemetry": [],
        }
    )

    # 3) Relationships between entities
    #    Example:
    #    {
    #      "from_type": "asset",
    #      "from_id": "AS-0001",
    #      "rel": "handles_data",
    #      "to_type": "data_domain",
    #      "to_id": "D-0003"
    #    }
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    # 4) Structural findings derived by the module
    #    Gaps, compensations, coverage calculations, propagation paths, etc.
    structural_findings: Dict[str, Any] = field(
        default_factory=lambda: {
            "gaps": [],
            "compensations": [],
            "coverage": {},
            "propagation_paths": [],
        }
    )


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


def initialise_module_state() -> CRTModuleState:
    """
    Create a fresh, empty CRTModuleState instance.

    Modules should call this once at the beginning of their workflow
    (e.g. at the top of the Streamlit page) and then mutate the state
    as they collect inputs, extract properties, and build mappings.
    """
    return CRTModuleState()


def add_entity(
    state: CRTModuleState,
    entity_type: str,
    entity: Dict[str, Any],
) -> None:
    """
    Add a single entity record to the appropriate list in state.entities.

    Parameters
    ----------
    state : CRTModuleState
        The shared module state to mutate.

    entity_type : str
        One of: "assets", "identities", "data_domains",
        "vendors", "controls", "failures", "telemetry".

    entity : dict
        A dictionary representing a row from a catalogue.
    """
    if entity_type not in state.entities:
        # Be defensive but keep behaviour predictable
        state.entities[entity_type] = []
    state.entities[entity_type].append(entity)


def add_relationship(
    state: CRTModuleState,
    from_type: str,
    from_id: str,
    rel: str,
    to_type: str,
    to_id: str,
) -> None:
    """
    Add a structural relationship between two entities.

    This is a thin wrapper to keep relationships consistent across modules.
    """
    state.relationships.append(
        {
            "from_type": from_type,
            "from_id": from_id,
            "rel": rel,
            "to_type": to_type,
            "to_id": to_id,
        }
    )


def note_gap(
    state: CRTModuleState,
    description: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a structural gap in the module's findings.

    description:
        A short, structural explanation of the gap
        (e.g. "No mapped telemetry source for this control").

    context:
        Optional small dict with additional structural context, e.g. IDs.
    """
    entry = {"description": description}
    if context:
        entry["context"] = context
    state.structural_findings.setdefault("gaps", []).append(entry)


def note_compensation(
    state: CRTModuleState,
    n_id: str,
    notes: Optional[str] = None,
) -> None:
    """
    Register that a specific compensating control (CRT-N) is relevant.

    notes should remain structural (e.g. "Mapped via CRT-C-0007"),
    not advisory.
    """
    entry: Dict[str, Any] = {"n_id": n_id}
    if notes:
        entry["notes"] = notes
    state.structural_findings.setdefault("compensations", []).append(entry)


def set_coverage(
    state: CRTModuleState,
    coverage: Dict[str, Any],
) -> None:
    """
    Set the coverage structure for the module.

    Example:
        {
          "visible_controls": ["CRT-C-0001", "CRT-C-0003"],
          "unmapped_controls": ["CRT-C-0007"],
          "has_telemetry": true
        }
    """
    state.structural_findings["coverage"] = coverage


def add_propagation_path(
    state: CRTModuleState,
    path: List[Dict[str, Any]],
) -> None:
    """
    Add a propagation path describing how a failure or incident
    could traverse entities.

    path should be a list of steps, each a small dict with IDs/types.
    """
    state.structural_findings.setdefault("propagation_paths", []).append(path)


# -------------------------------------------------------------------
# Bundle construction for modules
# -------------------------------------------------------------------


def build_bundle_for_module(
    *,
    module_name: str,
    bundle_type: str,
    state: CRTModuleState,
    extra_guardrails: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """
    Construct a locked-schema AI bundle for a module
    using the shared CRTModuleState.

    This is the final step in the 5-part pattern:

        1) collect_input()
        2) extract_properties()
        3) build_structural_mapping()
        4) render_output_panels()
        5) build_ai_context_bundle()  ← this function

    Parameters
    ----------
    module_name : str
        Short identifier for the module, e.g. "DCR", "CAV", "ASM".

    bundle_type : str
        One of the approved bundle types:
        architecture | exposure | metrics | simulation |
        supply_chain | identity | data | governance | signals | observation

    state : CRTModuleState
        The fully-populated module state.

    extra_guardrails : dict, optional
        Additional boolean flags (if needed in future).
        Core guardrails (no_advice / no_configuration / no_assurance)
        are always enforced.
    """
    guardrails = extra_guardrails or {}

    bundle = build_ai_bundle(
        module=module_name,
        bundle_type=bundle_type,
        primary_entity=state.primary_entity,
        entities=state.entities,
        relationships=state.relationships,
        structural_findings=state.structural_findings,
        guardrails=guardrails,
    )

    return bundle
