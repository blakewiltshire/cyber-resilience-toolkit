# =================================================================================================
# File: core/programme_ai_payload.py
# -------------------------------------------------------------------------------------------------
# Build the AI payload (full context + emphasis overlays)
#
# This is intentionally NOT a Streamlit module.
# It can be used by:
# - 🔍 Verify (freeze what AI will see)
# - 🧠 AI Prompt & Response (apply templates, add system/user messaging)
#
# Contract:
# - Full catalogue JSON views are included by default.
# - Emphasis overlays are provided separately (framework mode, selected lenses, focus entities).
# - Guardrails are always included.
# - CSV is authoritative; JSON is derived (via catalogue_json_views).
# -------------------------------------------------------------------------------------------------
# pylint: disable=import-error
# =================================================================================================

from __future__ import annotations

from typing import Any, Dict, Optional

from core.catalogue_json_views import (
    ALL_CRT_CATALOGUES,
    ensure_all_catalogue_json_views,
    load_catalogue_json_view,
)


def build_full_context_ai_payload(
    *,
    crt_catalogue_dir: str,
    programme_bundle: Dict[str, Any],
    programme_manifest: Optional[Dict[str, Any]] = None,
    output_pattern: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Assemble the full-context AI payload:
    - programme_bundle (source of truth)
    - (optional) programme_manifest (source, if you want it visible to AI)
    - full catalogue universe (JSON projections)
    - emphasis overlays (taken from bundle)
    - guardrails (taken from bundle)

    Notes:
    - This does not call AI.
    - This does not edit any catalogues.
    """

    # Ensure JSON projections exist (regen if stale)
    ensure_all_catalogue_json_views(crt_catalogue_dir, force=False, catalogue_keys=ALL_CRT_CATALOGUES)

    # Load full catalogue universe
    universe: Dict[str, Any] = {}
    for k in ALL_CRT_CATALOGUES:
        universe[k] = load_catalogue_json_view(crt_catalogue_dir, k)

    org_profile = programme_bundle.get("org_profile") if isinstance(programme_bundle.get("org_profile"), dict) else {}
    org_scope = programme_bundle.get("org_governance_scope") if isinstance(programme_bundle.get("org_governance_scope"), dict) else {}

    structural_lenses = programme_bundle.get("structural_lenses") if isinstance(programme_bundle.get("structural_lenses"), dict) else {}
    entities = programme_bundle.get("entities") if isinstance(programme_bundle.get("entities"), dict) else {}

    emphasis = {
        "frameworks_mode": str(org_scope.get("frameworks_mode") or "").strip(),
        "frameworks_in_scope": org_scope.get("frameworks_in_scope") if isinstance(org_scope.get("frameworks_in_scope"), list) else [],
        "obligations_ids_in_scope": org_scope.get("obligations_ids_in_scope") if isinstance(org_scope.get("obligations_ids_in_scope"), list) else [],
        "selected_structural_lenses": sorted(list(structural_lenses.keys())),
        "focus_entities": {k: v for k, v in entities.items() if isinstance(v, list) and v},
    }

    guardrails = programme_bundle.get("guardrails") if isinstance(programme_bundle.get("guardrails"), dict) else {
        "no_advice": True,
        "no_configuration": True,
        "no_assurance": True,
    }

    payload: Dict[str, Any] = {
        "programme_bundle": programme_bundle,
        "programme_manifest": programme_manifest or {},
        "structural_universe": universe,
        "governance_context": {
            "org_profile": org_profile,
            "org_governance_scope": org_scope,
        },
        "emphasis": emphasis,
        "guardrails": guardrails,
        "output_pattern": output_pattern or {},
    }

    return payload
