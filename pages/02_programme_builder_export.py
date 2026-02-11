# -------------------------------------------------------------------------------------------------
# CRT lint profile (Streamlit UI modules)
#
# CRT modules prioritise stability and readability over strict lint formality.
# We suppress style/complexity noise that is common in UI orchestration code.
#
# Correctness signals (e.g., import errors, unused variables, unsafe IO patterns)
# are intentionally NOT disabled globally — only locally where justified.
# -------------------------------------------------------------------------------------------------
# pylint: disable=wrong-import-position, wrong-import-order
# pylint: disable=invalid-name, non-ascii-file-name
# pylint: disable=too-many-locals, too-many-statements, too-many-arguments
# pylint: disable=line-too-long, too-many-lines
# pylint: disable=too-many-branches, too-many-return-statements
# pylint: disable=unused-argument
# pylint: disable=simplifiable-if-expression

"""
🎛 Programmes — Task Builder — Cyber Resilience Toolkit (CRT)

Unified task builder for:
- 🧭 Governance
- 🧱 Security Architecture
- 📈 Resilience Metrics
- 📊 Incident Simulation

This page:
- DOES NOT edit catalogues, lenses, or org profiles.
- DOES NOT call AI.
- ONLY assembles:
  - a compact manifest (human-facing build summary)
  - a normalised bundle (schema-clean structural container)
and hands them to:
  - 🧠 AI Observation Console (via session_state), and/or
  - External tools via JSON downloads.

Platinum principle:
Build one thing → it gets placed on the shelf → you may pick another or switch context.

Depth + Aperture = Platinum (wherever human reasoning intersects with data).
"""

from __future__ import annotations

# -------------------------------------------------------------------------------------------------
# Standard Library
# -------------------------------------------------------------------------------------------------
import os
import uuid
import sys
import json
import csv
import re
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# -------------------------------------------------------------------------------------------------
# Third-party Libraries
# -------------------------------------------------------------------------------------------------
import streamlit as st

# -------------------------------------------------------------------------------------------------
# Core Utilities & Paths
# -------------------------------------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "apps"))
sys.path.append(os.path.join(PROJECT_ROOT, "core"))
sys.path.append(os.path.join(PROJECT_ROOT, "data"))

from core.helpers import (  # pylint: disable=import-error
    load_markdown_file,
    build_sidebar_links,
)

try:  # pylint: disable=wrong-import-position
    from core.sih import get_sih  # type: ignore
except Exception:  # pylint: disable=broad-except
    get_sih = None  # type: ignore

from core.bundle_builder import bundle_to_pretty_json  # type: ignore  # noqa: F401
from core.module_pattern import (  # type: ignore
    initialise_module_state,
    build_bundle_for_module,
)
ABOUT_APP_MD = os.path.join(PROJECT_ROOT, "docs", "about_program_builder.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_ROOT, "docs", "about_and_support.md")
BRAND_LOGO_PATH = os.path.join(PROJECT_ROOT, "brand", "blake_logo.png")
ORG_PROFILES_PATH = os.path.join(PROJECT_ROOT, "data", "org_profiles.json")

# -------------------------------------------------------------------------------------------------
# Workspace Paths (persistent shelf)
# -------------------------------------------------------------------------------------------------
WORKSPACE_BASE = os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_workspace", "programmes")
LENS_SHELF_DIR = os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_workspace", "lenses")

WORKSPACE_MANIFESTS_DIR = os.path.join(WORKSPACE_BASE, "manifests")
WORKSPACE_BUNDLES_DIR = os.path.join(WORKSPACE_BASE, "bundles")
WORKSPACE_PACKAGES_DIR = os.path.join(WORKSPACE_BASE, "packages")
WORKSPACE_HANDOFF_SNAPSHOTS_DIR = os.path.join(WORKSPACE_BASE, "handoff_snapshots")

# AI Prompt & Response storage (templates + saved AI handoffs)
WORKSPACE_AI_EXPORTS_DIR = os.path.join(WORKSPACE_BASE, "ai_exports")

# Verified artefacts (immutable inputs for AI Prompt & Response)
WORKSPACE_VERIFIED_DIR = os.path.join(WORKSPACE_BASE, "verified")

# Session key for optional manual instructions
CRT_AI_MANUAL_INSTRUCTIONS_KEY = "crt_ai_manual_instructions"


# -------------------------------------------------------------------------------------------------
# Templates (defaults + user-defined)

# Governance template subtype mapping (deterministic scope matching)
GOV_TEMPLATE_SUBTYPE_BY_ID: Dict[str, str] = {
    "TPL-GOV-POLICY-V1": "policy",
    "TPL-GOV-STANDARD-V1": "standard",
    "TPL-GOV-RISK-BRIEF-V1": "risk_brief",
    "TPL-GOV-TP-QUESTIONNAIRE-V1": "questionnaire",
    "TPL-GOV-AUDIT-CHECKLIST-V1": "audit_checklist",
    "TPL-GOV-AWARENESS-V1": "awareness",
    "TPL-GOV-EXCEPTION-REGISTER-V1": "exception_register",
    "TPL-GOV-CONTROL-NARRATIVE-V1": "control_narrative",
    "TPL-GOV-VENDOR-SUMMARY-V1": "vendor_summary",
}
# -------------------------------------------------------------------------------------------------
DEFAULT_TEMPLATES_JSON = os.path.join(PROJECT_ROOT, "apps", "data_sources", "defaults", "templates", "output_templates.default.json")
USER_TEMPLATES_JSON = os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_workspace", "templates", "output_templates.user.json")

# -------------------------------------------------------------------------------------------------
# Constants & Session Keys
# -------------------------------------------------------------------------------------------------
UI_TITLE = "🎛 Programme Builder & AI Export"
MODULE_NAME = "ProgrammesAndOutputs"  # Used by module_pattern

# Label → bundle_type key used by downstream tools
PROGRAMME_MODES: Dict[str, str] = {
    "🧭 Governance": "governance",
    "🧱 Security Architecture": "architecture",
    "📈 Resilience Metrics": "metrics",
    "📊 Incident Simulation": "simulation",
}

# Lens bundles — expected to be set by lens pages (historic / session pattern)
LENS_SESSION_KEYS: Dict[str, str] = {
    "🧮 Data Classification Registry (DCR)": "dcr_last_bundle",
    "🧩 Attack Surface Mapper (ASM)": "asm_last_bundle",
    "🔐 Identity & Access Lens (IAL)": "ial_last_bundle",
    "🛰 Supply-Chain Exposure Scanner (SCES)": "sces_last_bundle",
    "📡 Telemetry & Signal Console (TSC)": "tsc_last_bundle",
}

# Org profile + governance scope bundle (in-session keys)
ORG_PROFILE_KEY = "org_profile"
ORG_SCOPE_BUNDLE_KEY = "org_governance_scope_bundle"

# Handoff keys (AOC reads these)
CURRENT_PROGRAMME_BUNDLE_KEY = "current_programme_bundle"
CURRENT_PROGRAMME_MANIFEST_KEY = "current_programme_manifest"

# Section 4 registry key (newer lens pattern)
CRT_PUBLISHED_LENSES_KEY = "crt_published_lens_bundles"

# Template selection (per task build)
CURRENT_TASK_TEMPLATE_KEY = "current_task_template_selection"

# Widget keys
KEY_TONE_SELECT = "programme_manifest_tone_select"

# -------------------------------------------------------------------------------------------------
# Manifest Notes examples (illustrative; not exported unless user writes their own content)
# -------------------------------------------------------------------------------------------------
MANIFEST_OVERRIDE_EXAMPLES: Dict[str, Dict[str, str]] = {
    "policy": {
        "audience": "Governance owners, risk stakeholders, audit liaison.",
        "tone": "neutral",
        "explicit_exclusions": "No configuration steps, no implementation guidance, no assurance statements.",
        "reviewer_notes": "Confirm scope boundaries, ownership, review cadence, and mapped control references.",
    },
    "standard": {
        "audience": "Control owners, implementation stakeholders, governance reviewers.",
        "tone": "neutral",
        "explicit_exclusions": "No vendor-specific hardening, no deployment steps, no tool configuration.",
        "reviewer_notes": "Check statements align with mapped controls and remain consistent across sections.",
    },
    "risk_brief": {
        "audience": "Risk forum participants, leadership consumers, assurance reviewers.",
        "tone": "neutral",
        "explicit_exclusions": "No acceptance decisions, no recommendations, no probability claims beyond provided fields.",
        "reviewer_notes": "Validate labels, impact framing, and that mappings reference the intended IDs.",
    },
    "questionnaire": {
        "audience": "Suppliers / vendors and internal third-party risk reviewers.",
        "tone": "neutral",
        "explicit_exclusions": "No legal commitments, no contractual language, no requirements beyond mapped IDs.",
        "reviewer_notes": "Ensure questions map cleanly to control IDs and remain measurable and unambiguous.",
    },
    "audit_checklist": {
        "audience": "Internal audit, compliance reviewers, control owners preparing evidence.",
        "tone": "neutral",
        "explicit_exclusions": "No pass/fail assertions; checklist is a structural prompt list only.",
        "reviewer_notes": "Confirm evidence examples are illustrative and mapping references are correct.",
    },
    "awareness": {
        "audience": "General staff and team leads.",
        "tone": "neutral",
        "explicit_exclusions": "No operational procedures; conceptual awareness framing only.",
        "reviewer_notes": "Keep language plain; avoid tool-specific assumptions; confirm key terms match scope.",
    },
    "exception_register": {
        "audience": "Governance approvers, risk owners, audit reviewers.",
        "tone": "neutral",
        "explicit_exclusions": "No approval decisions included; register captures context only.",
        "reviewer_notes": "Ensure each exception references scope, rationale, expiry markers, and mapped control IDs.",
    },
    "control_narrative": {
        "audience": "Assurance stakeholders, auditors, governance owners.",
        "tone": "neutral",
        "explicit_exclusions": "No assurance claims; narrative describes structural intent and evidence pointers only.",
        "reviewer_notes": "Avoid implying monitoring completeness; keep traceability to IDs explicit.",
    },
    "vendor_summary": {
        "audience": "Procurement, third-party risk, governance stakeholders.",
        "tone": "neutral",
        "explicit_exclusions": "No contractual language; no posture claims beyond provided inputs; no guarantees.",
        "reviewer_notes": "Verify supplier scope, dependency notes, mapped controls, and any obligation references.",
    },
    "architecture": {
        "audience": "Architecture reviewers, security engineering stakeholders, governance consumers.",
        "tone": "neutral",
        "explicit_exclusions": "No network configuration; structural view only (boundaries, roles, dependencies).",
        "reviewer_notes": "Confirm trust boundaries, primary entities, and mapped controls reflect the intended lens.",
    },
    "metrics": {
        "audience": "Leadership stakeholders, governance owners, resilience reviewers.",
        "tone": "neutral",
        "explicit_exclusions": "No targets or commitments; no benchmarking claims unless explicitly provided.",
        "reviewer_notes": "Ensure metrics are framed as snapshots and referenced to sources/windows where available.",
    },
    "simulation": {
        "audience": "Risk stakeholders, leadership consumers, governance reviewers.",
        "tone": "neutral",
        "explicit_exclusions": "No probability forecasts; no impact guarantees; illustrative structural analysis only.",
        "reviewer_notes": "Ensure assumptions are explicit and derived from known catalogue inputs.",
    },
    "general": {
        "audience": "",
        "tone": "neutral",
        "explicit_exclusions": "No configuration, advice, or assurance statements.",
        "reviewer_notes": "",
    },
}

# -------------------------------------------------------------------------------------------------
# CSS (kept in-file; minimal)
# -------------------------------------------------------------------------------------------------
def _inject_manifest_notes_css() -> None:
    st.markdown(
        """
<style>
.crt-example {
  font-size: 0.82rem;
  color: rgba(49, 51, 63, 0.55);
  margin-top: -8px;
  margin-bottom: 10px;
}
h3 { margin-bottom: 0.35rem; }
</style>
""",
        unsafe_allow_html=True,
    )

# -------------------------------------------------------------------------------------------------
# Small file helpers
# -------------------------------------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_load_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:  # pylint: disable=broad-except
        return None


def _safe_write_json(path: str, payload: Dict[str, Any]) -> bool:
    try:
        _ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except Exception:  # pylint: disable=broad-except
        return False

def render_markdown_file(path: str, fallback: str) -> None:
    """
    Render markdown from a file if present; otherwise show a simple fallback.
    Mirrors the defensive pattern used in other CRT modules.
    """
    content: Optional[str] = load_markdown_file(path)
    if content:
        st.markdown(content, unsafe_allow_html=True)
    else:
        st.markdown(fallback)

# -------------------------------------------------------------------------------------------------
# Templates (defaults + user-defined) — loaders
# -------------------------------------------------------------------------------------------------
def _built_in_default_templates() -> Dict[str, Dict[str, Any]]:
    return {
        "TPL-GOV-POLICY-V1": {
            "template_id": "TPL-GOV-POLICY-V1",
            "name": "Policy document",
            "applies_to": ["governance", "policy"],
            "sections": [
                "Purpose",
                "Scope",
                "Definitions",
                "Governance and Accountability",
                "Policy Statements",
                "Exceptions",
                "Evidence and Records",
                "Review and Maintenance",
            ],
            "notes": "Fallback only (file missing). Form only.",
        },
        "TPL-GOV-STANDARD-V1": {
            "template_id": "TPL-GOV-STANDARD-V1",
            "name": "Standard",
            "applies_to": ["governance", "standard"],
            "sections": [
                "Purpose",
                "Scope",
                "Control Statements",
                "Evidence and Verification",
                "Exceptions",
                "Review and Maintenance",
            ],
            "notes": "Fallback only (file missing). Form only.",
        },
        "TPL-GOV-TP-QUESTIONNAIRE-V1": {
            "template_id": "TPL-GOV-TP-QUESTIONNAIRE-V1",
            "name": "Third-party questionnaire",
            "applies_to": ["governance", "questionnaire"],
            "sections": [
                "Supplier Context",
                "Data Handling",
                "Identity and Access",
                "Control Environment",
                "Monitoring and Telemetry",
                "Incident and Continuity",
                "Evidence Requests",
            ],
            "notes": "Fallback only (file missing). Form only.",
        },
        "TPL-GOV-RISK-BRIEF-V1": {
            "template_id": "TPL-GOV-RISK-BRIEF-V1",
            "name": "Risk management brief / register snapshot",
            "applies_to": ["governance", "risk_brief"],
            "sections": [
                "Context",
                "Scope",
                "Risk Register Snapshot",
                "Dependencies and Assumptions",
                "Observations",
                "Unknowns",
                "Appendix",
            ],
            "notes": "Fallback only (file missing). Form only.",
        },
    }


def _normalise_template_dict(raw: Any) -> Dict[str, Dict[str, Any]]:
    """Normalise templates into the internal dict form keyed by template_id.

    Supports:
      - dict form: { "<id>": {template_id,name,applies_to,sections,...}, ... }
      - list form (defaults/user file style): [ {template_id,category,label,sections,...}, ... ]
    """
    out: Dict[str, Dict[str, Any]] = {}

    def _add(
        template_id: str,
        name: str,
        applies_to: List[str],
        sections: List[str],
        notes: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not template_id or not name or not sections:
            return
        clean_sections = [str(s).strip() for s in sections if str(s).strip()]
        if not clean_sections:
            return
        applies = [str(x).strip().lower() for x in (applies_to or []) if str(x).strip()]
        payload: Dict[str, Any] = {
            "template_id": template_id,
            "name": name,
            "label": name,  # keep a stable label field
            "applies_to": applies,
            "sections": clean_sections,
            "notes": (notes or "").strip(),
        }
        if extra:
            payload.update(extra)
        out[template_id] = payload

    # Dict form
    if isinstance(raw, dict):
        for tid, tpl in raw.items():
            if not isinstance(tid, str) or not isinstance(tpl, dict):
                continue
            template_id = str(tpl.get("template_id") or tid).strip()
            name = str(tpl.get("name") or tpl.get("label") or "").strip()
            sections = tpl.get("sections")
            if not isinstance(sections, list):
                continue
            applies_to = tpl.get("applies_to", [])
            if not isinstance(applies_to, list):
                applies_to = []
            notes = tpl.get("notes", "") if tpl.get("notes", "") is not None else ""
            extra = {k: v for k, v in tpl.items() if k not in {"template_id", "name", "label", "applies_to", "sections", "notes"}}
            _add(template_id, name, applies_to, sections, str(notes), extra)
        return out

    # List form
    if isinstance(raw, list):
        for tpl in raw:
            if not isinstance(tpl, dict):
                continue

            template_id = str(tpl.get("template_id") or "").strip()
            name = str(tpl.get("label") or tpl.get("name") or "").strip()
            category = str(tpl.get("category") or "").strip().lower()
            sections = tpl.get("sections")

            if not template_id or not name or not isinstance(sections, list) or not sections:
                continue

            # Applies-to: category + (optional) explicit applies_to from file
            applies_to: List[str] = []
            if category:
                applies_to.append(category)

            # If governance, derive deterministic subtype.
            if category == "governance":
                subtype: Optional[str] = None

                # 1) If this is a known built-in template id → subtype
                subtype = GOV_TEMPLATE_SUBTYPE_BY_ID.get(template_id)

                # 2) If it's a user template derived from a known default → subtype
                if not subtype:
                    derived = str(tpl.get("derived_from_template_id") or "").strip()
                    if derived:
                        subtype = GOV_TEMPLATE_SUBTYPE_BY_ID.get(derived)

                # 3) Keyword fallback (last resort)
                if not subtype:
                    lname = name.lower()
                    if "policy" in lname:
                        subtype = "policy"
                    elif "standard" in lname:
                        subtype = "standard"
                    elif "questionnaire" in lname:
                        subtype = "questionnaire"
                    elif "risk" in lname and "brief" in lname:
                        subtype = "risk_brief"
                    elif "audit" in lname or "checklist" in lname:
                        subtype = "audit_checklist"
                    elif "awareness" in lname or "training" in lname:
                        subtype = "awareness"
                    elif "exception" in lname:
                        subtype = "exception_register"
                    elif "narrative" in lname:
                        subtype = "control_narrative"
                    elif "vendor" in lname:
                        subtype = "vendor_summary"

                if subtype:
                    applies_to.append(subtype)

            if isinstance(tpl.get("applies_to"), list):
                applies_to.extend([str(x).strip().lower() for x in tpl.get("applies_to") if str(x).strip()])

            notes = tpl.get("notes", "") if tpl.get("notes", "") is not None else ""
            extra = {k: v for k, v in tpl.items() if k not in {"template_id", "name", "label", "applies_to", "category", "sections", "notes"}}

            # Preserve category as a first-class internal field
            if category:
                extra["category"] = category

            _add(template_id, name, applies_to, sections, str(notes), extra)
        return out

    return out


def load_default_templates() -> Dict[str, Dict[str, Any]]:
    payload = _safe_load_json(DEFAULT_TEMPLATES_JSON)
    if payload is None:
        st.info("Default output templates file not found. Using built-in minimal fallbacks.")
        st.code(DEFAULT_TEMPLATES_JSON, language="text")
        return _built_in_default_templates()

    raw_templates = payload.get("templates")
    if not isinstance(raw_templates, list):
        st.error("Default templates file has invalid schema (expected list under 'templates').")
        st.code(DEFAULT_TEMPLATES_JSON, language="text")
        st.stop()

    out: Dict[str, Dict[str, Any]] = {}

    for tpl in raw_templates:
        if not isinstance(tpl, dict):
            continue

        tid = str(tpl.get("template_id", "")).strip()
        label = str(tpl.get("label", "")).strip()
        category = str(tpl.get("category", "")).strip().lower()
        sections = tpl.get("sections")

        if not tid or not label or not category or not isinstance(sections, list) or not sections:
            continue

        clean_sections = [str(s).strip() for s in sections if str(s).strip()]
        if not clean_sections:
            continue

        # --- Applies-to (deterministic)
        # Always include the category, so category-level matching works as a fallback.
        applies_to: List[str] = [category]

        if category == "governance":
            subtype = GOV_TEMPLATE_SUBTYPE_BY_ID.get(tid)
            if subtype:
                applies_to.append(subtype)

        out[tid] = {
            "template_id": tid,
            "name": label,
            "label": label,
            "category": category,
            "applies_to": applies_to,
            "sections": clean_sections,
            "notes": str(tpl.get("notes") or "").strip(),
        }

    if not out:
        st.error("Default templates file loaded but no valid templates were found.")
        st.code(DEFAULT_TEMPLATES_JSON, language="text")
        st.stop()

    return out


def load_user_templates() -> Dict[str, Dict[str, Any]]:
    payload = _safe_load_json(USER_TEMPLATES_JSON)
    if not payload:
        return {}

    templates = payload.get("templates")
    return _normalise_template_dict(templates)


def _save_user_templates(user_templates: Dict[str, Dict[str, Any]]) -> bool:
    # Persist in list-form (matches default templates style, plus user metadata fields)
    now = _now_utc_iso()
    out_list: List[Dict[str, Any]] = []
    for tid, tpl in user_templates.items():
        if not isinstance(tpl, dict):
            continue
        template_id = str(tpl.get("template_id") or tid).strip()
        label = str(tpl.get("label") or tpl.get("name") or "").strip()
        sections = tpl.get("sections")
        if not template_id or not label or not isinstance(sections, list) or not sections:
            continue

        category = str(tpl.get("category") or "").strip().lower()
        if not category:
            # Derive a category from applies_to (best-effort; governance is the default)
            applies = tpl.get("applies_to", [])
            applies = [str(x).strip().lower() for x in applies] if isinstance(applies, list) else []
            for cand in ["governance", "architecture", "metrics", "simulation"]:
                if cand in applies:
                    category = cand
                    break
            if not category:
                category = "governance"

        payload_tpl: Dict[str, Any] = {
            "template_id": template_id,
            "category": category,
            "label": label,
            "sections": [str(s).strip() for s in sections if str(s).strip()],
            "notes": str(tpl.get("notes") or "").strip(),
            "updated_at": now,
            "is_user": True,
        }

        # Preserve optional lineage + timestamps if present
        if tpl.get("created_at"):
            payload_tpl["created_at"] = tpl.get("created_at")
        else:
            payload_tpl["created_at"] = now
        if tpl.get("derived_from_template_id"):
            payload_tpl["derived_from_template_id"] = str(tpl.get("derived_from_template_id")).strip()

        out_list.append(payload_tpl)

    payload = {
        "version": "1.0",
        "updated_at": now,
        "templates": out_list,
    }
    return _safe_write_json(USER_TEMPLATES_JSON, payload)

def merge_templates(default_templates: Dict[str, Dict[str, Any]], user_templates: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    merged = dict(default_templates)
    merged.update(user_templates)
    return merged


def resolve_all_templates() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    defaults = load_default_templates()
    users = load_user_templates()
    merged = merge_templates(defaults, users)
    return merged, users


def _template_scope_key(programme_mode_label: str, task_type: str) -> str:
    """
    Maps current selection → template applies_to key.
    Mirrors the way Manifest Notes are keyed.
    """
    p = (programme_mode_label or "").strip()
    t = (task_type or "").strip().lower()

    if p == "🧱 Security Architecture":
        return "architecture"
    if p == "📈 Resilience Metrics":
        return "metrics"
    if p == "📊 Incident Simulation":
        return "simulation"

    if "policy" in t:
        return "policy"
    if t == "standard":
        return "standard"
    if "questionnaire" in t:
        return "questionnaire"
    if "risk management brief" in t or "risk" in t:
        return "risk_brief"
    if "audit checklist" in t or "checklist" in t:
        return "audit_checklist"
    if "awareness" in t or "training" in t:
        return "awareness"
    if "exception" in t:
        return "exception_register"
    if "continuous control narrative" in t or "narrative" in t:
        return "control_narrative"
    if "vendor risk summary" in t or "vendor" in t:
        return "vendor_summary"

    return "governance"



def _scope_to_category(scope_key: str) -> str:
    s = (scope_key or "").strip().lower()
    if s in {"architecture", "metrics", "simulation", "governance"}:
        return s
    # policy/standard/etc are governance-family templates
    return "governance"


def render_templates_after_manifest_notes(
    programme_mode_label: str,
    task_type: str,
) -> Dict[str, Any]:
    """
    NOT a tab.

    Sits directly after 📝 Manifest Notes, aligned to Task Type,
    and writes template selection into session_state for the build.
    """
    st.markdown("### 🧱 Templates")
    st.caption("Template selection is included in the exported handoff payload.")

    scope_key = _template_scope_key(programme_mode_label, task_type)
    merged, user_templates = resolve_all_templates()

    applicable: List[Dict[str, Any]] = []
    for tpl in merged.values():
        if not isinstance(tpl, dict):
            continue
        applies = tpl.get("applies_to", [])
        if isinstance(applies, list) and scope_key in [str(x).strip().lower() for x in applies]:
            applicable.append(tpl)

    # Stable ordering: user templates first (by name), then defaults (by name)
    def _is_user(tpl: Dict[str, Any]) -> bool:
        tid = str(tpl.get("template_id", "")).strip()
        return tid in user_templates

    applicable.sort(key=lambda x: (0 if _is_user(x) else 1, str(x.get("name", "")).lower(), str(x.get("template_id", ""))))

    if not applicable:
        st.warning(f"No templates apply to this task type (`{scope_key}`).")
        st.caption("You can still use a one-off custom section list below.")
        applicable = []

    # Default selection: first applicable, or a one-off custom
    choice_labels: List[str] = ["(Custom — one-off)"]
    label_to_tpl: Dict[str, Dict[str, Any]] = {}
    for tpl in applicable:
        tid = str(tpl.get("template_id", "")).strip()
        name = str(tpl.get("name", "")).strip()
        src = "user" if _is_user(tpl) else "default"
        label = f"{name}  ·  {tid}  ·  {src}"
        choice_labels.append(label)
        label_to_tpl[label] = tpl

    selected_label = st.selectbox(
        "Template for this task",
        options=choice_labels,
        index=1 if len(choice_labels) > 1 else 0,
        help="Defaults align to the task type. You may also use a one-off custom section list.",
    )

    selected_payload: Dict[str, Any] = {
        "scope_key": scope_key,
        "selection_mode": "custom_one_off" if selected_label == "(Custom — one-off)" else "template",
        "template_id": None,
        "template_name": None,
        "template_source": None,
        "sections": [],
        "notes": "",
    }

    if selected_label != "(Custom — one-off)":
        tpl = label_to_tpl.get(selected_label, {})
        tid = str(tpl.get("template_id", "")).strip()
        name = str(tpl.get("name", "")).strip()
        sections = tpl.get("sections", [])
        notes = str(tpl.get("notes", "") or "").strip()
        source = "user" if _is_user(tpl) else "default"

        clean_sections = [str(s).strip() for s in sections if str(s).strip()] if isinstance(sections, list) else []

        selected_payload.update(
            {
                "template_id": tid,
                "template_name": name,
                "template_source": source,
                "sections": clean_sections,
                "notes": notes,
            }
        )

        with st.expander("Preview template layout", expanded=False):
            st.write(f"**Applies to:** `{scope_key}`")
            st.write(f"**Source:** `{source}`")
            if notes:
                st.caption(notes)
            st.write("**Sections:**")
            for s in clean_sections:
                st.write(f"- {s}")


        with st.expander("Show default template library (read-only)", expanded=False):
            st.caption("Source file (defaults)")
            st.code(DEFAULT_TEMPLATES_JSON, language="text")
            defaults_payload = _safe_load_json(DEFAULT_TEMPLATES_JSON)
            if isinstance(defaults_payload, dict):
                st.code(json.dumps(defaults_payload, indent=2, ensure_ascii=False), language="json")
            else:
                st.info("Defaults file not found or unreadable.")

    else:
        st.markdown("#### Custom sections (one-off)")
        raw = st.text_area(
            "Sections (one per line)",
            value="",
            height=160,
            placeholder="e.g.\nPurpose\nScope\nDefinitions\n...\n",
        )
        custom_sections = [line.strip() for line in (raw or "").splitlines() if line.strip()]
        selected_payload["sections"] = custom_sections

        with st.expander("Save as a user template (optional)", expanded=False):
            save_flag = st.checkbox("Save this custom layout as a user template", value=False)
            if save_flag:
                user_tid = st.text_input("Template ID", value=f"TPL-USER-{scope_key.upper()}-V1")
                user_name = st.text_input("Template name", value=f"{task_type} (User)")
                user_notes = st.text_input("Notes (optional)", value="")

                can_save = bool(user_tid.strip()) and bool(user_name.strip()) and bool(custom_sections)

                if st.button("💾 Save user template", disabled=not can_save, use_container_width=True):
                    tid = user_tid.strip()
                    user_templates = load_user_templates()  # refresh from disk
                    category_for_save = _scope_to_category(scope_key)
                    user_templates[tid] = {
                        "template_id": tid,
                        "name": user_name.strip(),
                        "label": user_name.strip(),
                        "category": category_for_save,
                        "applies_to": [category_for_save, scope_key],
                        "sections": custom_sections,
                        "notes": user_notes.strip(),
                        "created_at": _now_utc_iso(),
                        "updated_at": _now_utc_iso(),
                        "derived_from_template_id": str(selected_payload.get("template_id") or "").strip(),
                        "is_user": True,
                    }
                    ok = _save_user_templates(user_templates)
                    if ok:
                        st.success("Saved user template.")
                        st.rerun()
                    else:
                        st.error("Failed to save user template (write error).")

    # Persist for build step
    st.session_state[CURRENT_TASK_TEMPLATE_KEY] = selected_payload
    return selected_payload

# -------------------------------------------------------------------------------------------------
# Task YAML (as provided earlier)
# -------------------------------------------------------------------------------------------------
def load_task_options_for_mode(mode_label: str) -> List[str]:
    programme = PROGRAMME_MODES.get(mode_label)
    if not programme:
        return []

    default_options = {
        "governance": [
            "Policy document",
            "Standard",
            "Risk management brief / register snapshot",
            "Third-party questionnaire",
            "Audit checklist",
            "Awareness script / training outline",
            "Exception register",
            "Continuous control narrative",
            "Vendor risk summary",
        ],
        "architecture": [
            "Security architecture view",
            "Control coverage summary",
            "Zoning / trust-boundary view",
            "Data-flow / service-chain summary",
        ],
        "metrics": [
            "Resilience metrics brief",
            "Domain-specific metrics summary",
            "Coverage / gap overview",
        ],
        "simulation": [
            "Incident response playbook",
            "Scenario analysis summary",
            "“What if” structural simulation brief",
        ],
    }

    base = default_options.get(programme, []).copy()

    try:
        import yaml  # type: ignore

        config_path = os.path.join(PROJECT_ROOT, "apps", "config", "programme_tasks.yaml")
        if not os.path.exists(config_path):
            return base

        with open(config_path, "r", encoding="utf-8") as f:
            entries = yaml.safe_load(f) or []

        extra_labels = [
            e["label"]
            for e in entries
            if isinstance(e, dict) and e.get("programme") == programme and e.get("label")
        ]

        for lbl in extra_labels:
            if lbl not in base:
                base.append(lbl)

        return base

    except Exception:  # pylint: disable=broad-except
        return base


def get_task_description(mode_label: str, task_label: str) -> Optional[str]:
    programme = PROGRAMME_MODES.get(mode_label)
    if not programme or not task_label:
        return None

    try:
        import yaml  # type: ignore

        config_path = os.path.join(PROJECT_ROOT, "apps", "config", "programme_tasks.yaml")
        if not os.path.exists(config_path):
            return None

        with open(config_path, "r", encoding="utf-8") as f:
            entries = yaml.safe_load(f) or []

        for entry in entries:
            if (
                isinstance(entry, dict)
                and entry.get("programme") == programme
                and entry.get("label") == task_label
            ):
                desc = entry.get("description")
                if isinstance(desc, str) and desc.strip():
                    return desc.strip()
        return None

    except Exception:  # pylint: disable=broad-except
        return None

# -------------------------------------------------------------------------------------------------
# Shared helpers — SIH, org profiles, and bundles
# -------------------------------------------------------------------------------------------------
def get_sih_instance() -> Optional[Any]:
    if get_sih is None:
        return None

    cache_key = "_sih_instance_task_builder"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    base_catalogue_path = os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues")
    try:
        sih = get_sih(base_catalogue_path)  # type: ignore[misc]
        st.session_state[cache_key] = sih
        return sih
    except Exception as exc:  # pylint: disable=broad-except
        st.error("Failed to initialise System Integrator Hub (SIH) for Task Builder.")
        st.exception(exc)
        return None


def get_lens_bundle_from_session(session_key: str) -> Optional[Dict[str, Any]]:
    raw = st.session_state.get(session_key)
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def catalog_options(
    catalogue_name: str,
    id_column: str,
    label_column: str,
    sih: Any,
) -> List[Tuple[str, str]]:
    if sih is None:
        return []

    try:
        df = sih.get_catalogue(catalogue_name)
    except Exception:  # pylint: disable=broad-except
        return []

    if df is None or df.empty:
        return []

    options: List[Tuple[str, str]] = []
    for _, row in df.iterrows():
        _id = str(row.get(id_column, "")).strip()
        label = str(row.get(label_column, "")).strip()
        if not _id:
            continue
        display = f"{_id} — {label}" if label else _id
        options.append((_id, display))
    return options


def _load_org_profiles_from_disk() -> Optional[Dict[str, Any]]:
    if not os.path.exists(ORG_PROFILES_PATH):
        return None
    try:
        with open(ORG_PROFILES_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:  # pylint: disable=broad-except
        return None
    return data if isinstance(data, dict) else None


def _map_profile_to_org_profile_and_scope(profile: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    org_profile: Dict[str, Any] = {
        "profile_name": profile.get("profile_name"),
        "profile_purpose": profile.get("profile_purpose"),
        "organisation_name": profile.get("org_name"),
        "org_name": profile.get("org_name"),
        "industry": profile.get("industry"),
        "environment": profile.get("environment"),
        "jurisdictions": profile.get("jurisdictions", []),
        "org_size": profile.get("org_size"),
        "notes": profile.get("notes", ""),
    }

    org_scope: Dict[str, Any] = {
        "frameworks_in_scope": profile.get("frameworks_in_scope", []),
        "frameworks_mode": profile.get("frameworks_mode", "default_only"),
        "obligations_ids_in_scope": profile.get("obligations_ids_in_scope", []),
    }

    return org_profile, org_scope


def _derive_active_profile_and_scope_from_disk() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    data = _load_org_profiles_from_disk()
    if not data:
        return None, None

    profiles = data.get("profiles") or {}
    if not isinstance(profiles, dict) or not profiles:
        return None, None

    active_name = data.get("active_org_profile")
    profile: Optional[Dict[str, Any]] = None

    if active_name and active_name in profiles:
        profile = profiles[active_name]
    else:
        first_key = next(iter(profiles.keys()))
        profile = profiles.get(first_key)

    if not isinstance(profile, dict):
        return None, None

    org_profile, org_scope = _map_profile_to_org_profile_and_scope(profile)
    return org_profile, org_scope


def get_org_profile_and_scope() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    data = _load_org_profiles_from_disk()
    profiles_from_disk: Dict[str, Any] = {}
    active_name_disk: Optional[str] = None

    if data and isinstance(data.get("profiles"), dict):
        profiles_from_disk = data.get("profiles", {})  # type: ignore[assignment]
        active_name_disk = data.get("active_org_profile")

    profiles_session = st.session_state.get("org_profiles")
    active_name_session = st.session_state.get("active_org_profile")

    if isinstance(profiles_session, dict) and profiles_session:
        profiles = profiles_session
        active_name = active_name_session or active_name_disk
    else:
        profiles = profiles_from_disk
        active_name = active_name_disk

    if isinstance(profiles, dict) and profiles:
        profile_names = sorted(profiles.keys())

        current_task_name = st.session_state.get("current_task_profile_name")
        if current_task_name in profile_names:
            default_name = current_task_name
        elif active_name in profile_names:
            default_name = active_name
        else:
            default_name = profile_names[0]

        default_index = profile_names.index(default_name)

        selected_name = st.selectbox(
            "Profile for this task",
            options=profile_names,
            index=default_index,
            help=(
                "Profiles are defined in 📂 Structural Controls & Frameworks → "
                "🏛 Org Governance Profile — Organisation & Scope."
            ),
        )

        st.session_state["current_task_profile_name"] = selected_name
        profile = profiles[selected_name]

        org_profile, org_scope = _map_profile_to_org_profile_and_scope(profile)
        return org_profile, org_scope

    value_profile = st.session_state.get(ORG_PROFILE_KEY)
    org_profile = value_profile if isinstance(value_profile, dict) else None

    value_scope = st.session_state.get(ORG_SCOPE_BUNDLE_KEY)
    org_scope = value_scope if isinstance(value_scope, dict) else None

    if org_profile or org_scope:
        return org_profile, org_scope

    return _derive_active_profile_and_scope_from_disk()

# -------------------------------------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------------------------------------
def render_sidebar() -> None:
    st.sidebar.title("📂 Navigation Menu")
    st.sidebar.page_link("app.py", label="CRT Portal")
    for path, label in build_sidebar_links():
        st.sidebar.page_link(path, label=label)
    st.sidebar.divider()
    st.logo(BRAND_LOGO_PATH)  # pylint: disable=no-member

    st.sidebar.markdown("### 🔄 Programme artefacts flow")
    st.sidebar.caption(
        "- Structural Controls & Frameworks → Org context\n"
        "- Structural Lenses → Lens bundles\n"
        "- Task Builder → Manifests & bundles\n"
        "- Verify → Verified artefact\n"
        "- AI Prompt & Response → AI handoff"
    )

    st.sidebar.divider()
    with st.sidebar.expander("ℹ️ About & Support"):
        support_md = load_markdown_file(ABOUT_SUPPORT_MD)
        if support_md:
            st.markdown(support_md, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------
# Section 1 — Governance Context Summary (read-only)
# -------------------------------------------------------------------------------------------------
def render_context_summary(org_profile: Optional[Dict[str, Any]], org_scope: Optional[Dict[str, Any]]) -> None:
    st.subheader("1. 🏛 Governance Context")
    if not org_profile and not org_scope:
        st.info(
            "No Org Governance Profile or scope bundle found in this session or on disk.\n\n"
            "Set these in **📂 Structural Controls & Frameworks → 🏛 Org Governance Profile — Organisation & Scope**.\n"
            "You can still build artefacts, but they may be less precise."
        )
        st.divider()
        return

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Org Profile")
        if not org_profile:
            st.write("_Org profile not available._")
        else:
            org_name = org_profile.get("organisation_name") or org_profile.get("org_name") or "Not specified"
            industry = org_profile.get("industry") or "Not specified"
            environment = org_profile.get("environment") or "Not specified"
            size = org_profile.get("org_size") or "Not specified"
            regions = org_profile.get("jurisdictions") or []

            st.write(f"**Organisation:** {org_name}")
            st.write(f"**Industry / Sector:** {industry}")
            st.write(f"**Environment:** {environment}")
            st.write(f"**Scale:** {size}")
            if regions:
                st.write("**Jurisdictions in Scope:**")
                st.write(", ".join(regions))

            profile_name = org_profile.get("profile_name")
            profile_purpose = org_profile.get("profile_purpose")
            if profile_name:
                st.write(f"**Profile:** {profile_name}")
            if profile_purpose:
                st.write(f"**Profile Purpose:** {profile_purpose}")

    with col_right:
        st.markdown("#### Frameworks & Obligations")
        if not org_scope:
            st.write("_No org governance scope information available._")
        else:
            frameworks = org_scope.get("frameworks_in_scope", [])
            frameworks_mode_key = org_scope.get("frameworks_mode", "default_only")
            obligations = org_scope.get("obligations_ids_in_scope", [])

            mode_label_map = {
                "default_only": "Default Only",
                "overlay": "Overlay Mode (recommended)",
                "framework_only": "Frameworks as Primary Lens",
            }
            mode_label = mode_label_map.get(frameworks_mode_key, frameworks_mode_key)

            st.write(f"**Frameworks Mode:** {mode_label}")

            if frameworks:
                st.write("**Frameworks in Scope (CRT-REQ requirement_set_id):**")
                st.write(", ".join(frameworks))
            else:
                st.write("_No frameworks listed in scope._")

            if obligations:
                st.write(f"**Legal & Regulatory Obligations (CRT-LR):** {len(obligations)} obligations in scope")
            else:
                st.write("_No obligations explicitly listed in scope._")

    st.divider()

# -------------------------------------------------------------------------------------------------
# Section 2 — Programme Mode Selector
# -------------------------------------------------------------------------------------------------
def render_programme_mode_selector() -> str:
    st.subheader("2. Programme Mode")
    st.markdown(
        "Select the programme lens you want to work in. "
        "This determines which **task types** appear next and how downstream tools frame the artefact."
    )

    mode_label = st.radio(
        "Which programme are you working in?",
        options=list(PROGRAMME_MODES.keys()),
        horizontal=True,
    )

    mode_help = {
        "🧭 Governance": "Policies, standards, questionnaires, checklists, awareness material.",
        "🧱 Security Architecture": "Architecture views, zoning, trust boundaries, service chains.",
        "📈 Resilience Metrics": "Structural metrics briefs, coverage and gap overviews.",
        "📊 Incident Simulation": "Scenario bundles, incident playbooks, and 'what if' structures.",
    }
    st.caption(mode_help.get(mode_label, ""))
    st.divider()
    return mode_label

# -------------------------------------------------------------------------------------------------
# Section 3 — Task Type & Artefact Anchor
# -------------------------------------------------------------------------------------------------
def _task_to_manifest_example_key(programme_mode_label: str, task_type: str) -> str:
    t = (task_type or "").strip().lower()
    p = (programme_mode_label or "").strip()

    if p == "🧱 Security Architecture":
        return "architecture"
    if p == "📈 Resilience Metrics":
        return "metrics"
    if p == "📊 Incident Simulation":
        return "simulation"

    if "policy" in t:
        return "policy"
    if t == "standard":
        return "standard"
    if "risk management brief" in t or "risk" in t:
        return "risk_brief"
    if "questionnaire" in t:
        return "questionnaire"
    if "audit checklist" in t or "checklist" in t:
        return "audit_checklist"
    if "awareness" in t or "training" in t:
        return "awareness"
    if "exception" in t:
        return "exception_register"
    if "continuous control narrative" in t or "narrative" in t:
        return "control_narrative"
    if "vendor risk summary" in t or "vendor" in t:
        return "vendor_summary"

    return "general"


def render_manifest_notes(task_type: str, programme_mode_label: str) -> Dict[str, Any]:
    st.markdown("### 📝 Manifest Notes")
    st.caption("Additional context included in the exported handoff payload.")

    example_key = _task_to_manifest_example_key(programme_mode_label, task_type)
    examples = MANIFEST_OVERRIDE_EXAMPLES.get(example_key, MANIFEST_OVERRIDE_EXAMPLES.get("general", {}))

    audience = st.text_input("Audience", value="", placeholder="(optional)")
    st.markdown(
        f"<div class='crt-example'><strong>Example:</strong> {examples.get('audience','')}</div>",
        unsafe_allow_html=True,
    )

    tone_options = ["", "neutral", "plain", "formal"]
    tone = st.selectbox("Tone", options=tone_options, index=0, key=KEY_TONE_SELECT)
    st.markdown(
        f"<div class='crt-example'><strong>Example:</strong> {examples.get('tone','neutral') or 'neutral'}</div>",
        unsafe_allow_html=True,
    )

    explicit_exclusions = st.text_input("Explicit exclusions", value="", placeholder="(optional)")
    st.markdown(
        f"<div class='crt-example'><strong>Example:</strong> {examples.get('explicit_exclusions','')}</div>",
        unsafe_allow_html=True,
    )

    reviewer_notes = st.text_input("Reviewer / maintenance notes", value="", placeholder="(optional)")
    st.markdown(
        f"<div class='crt-example'><strong>Example:</strong> {examples.get('reviewer_notes','')}</div>",
        unsafe_allow_html=True,
    )

    notes: Dict[str, Any] = {
        "audience": audience.strip() if isinstance(audience, str) and audience.strip() else None,
        "tone": tone.strip() if isinstance(tone, str) and tone.strip() else None,
        "explicit_exclusions": explicit_exclusions.strip() if isinstance(explicit_exclusions, str) and explicit_exclusions.strip() else None,
        "reviewer_notes": reviewer_notes.strip() if isinstance(reviewer_notes, str) and reviewer_notes.strip() else None,
    }

    if not any(v for v in notes.values()):
        return {}

    return notes


def render_task_type_selector(
    mode_label: str,
) -> Tuple[str, Optional[str], Optional[str], Dict[str, Any], Dict[str, Any]]:
    st.subheader("3. Task Type & Artefact Anchor")
    st.markdown(
        "Choose what you are building this artefact for, then anchor it to a specific policy, "
        "standard, register, or scenario reference."
    )

    task_options = load_task_options_for_mode(mode_label)
    if not task_options:
        st.error("No task types are available for this programme.")
        return "", None, None, {}, {}

    task_type = st.selectbox("Task Type", options=task_options, index=0)

    task_description = get_task_description(mode_label, task_type)
    if task_description:
        with st.expander("What does this task type cover?", expanded=False):
            st.write(task_description)

    st.markdown("#### Artefact Anchor")

    anchor_id: Optional[str] = None
    anchor_name: Optional[str] = None

    if mode_label == "🧭 Governance" and task_type in ("Policy document", "Standard"):
        anchor_mode = st.radio(
            "How do you want to anchor this task?",
            options=["Select existing", "Custom artefact"],
            horizontal=True,
        )

        if anchor_mode == "Select existing":
            sih = get_sih_instance()
            if sih is None:
                st.warning("SIH is not available in this runtime. Switch to **Custom artefact**.")
            else:
                if task_type == "Policy document":
                    catalogue_name = "CRT-POL"
                    id_col = "policy_id"
                    label_col = "policy_name"
                    existing_label = "Existing Policy (CRT-POL)"
                else:
                    catalogue_name = "CRT-STD"
                    id_col = "standard_id"
                    label_col = "standard_name"
                    existing_label = "Existing Standard (CRT-STD)"

                options = catalog_options(catalogue_name, id_col, label_col, sih)
                if not options:
                    st.warning(f"No entries found in `{catalogue_name}` via SIH. Switch to **Custom artefact**.")
                else:
                    display_options = [display for _, display in options]
                    choice = st.selectbox(existing_label, options=["(none)"] + display_options)
                    if choice != "(none)":
                        idx = display_options.index(choice)
                        anchor_id = options[idx][0]
                        anchor_name = choice

        else:
            anchor_id = st.text_input("Artefact ID (optional)", value="")
            anchor_name = st.text_input("Artefact Name / Title", value="")

    else:
        anchor_name = st.text_input("Artefact Name / Title")
        anchor_id = st.text_input("Artefact Reference ID (optional)")

    # ✅ As locked: Manifest Notes, then Templates (NOT a tab)
    manifest_notes = render_manifest_notes(task_type=task_type, programme_mode_label=mode_label)
    template_selection = render_templates_after_manifest_notes(programme_mode_label=mode_label, task_type=task_type)

    st.caption("Anchor + notes + templates are structural metadata only. They do not create or edit CRT records.")
    st.divider()
    return task_type, anchor_id, anchor_name, manifest_notes, template_selection

# -------------------------------------------------------------------------------------------------
# Section 4 — Input Bundles & Lenses (Platinum)
# -------------------------------------------------------------------------------------------------
def _ensure_lens_registry() -> Dict[str, Dict[str, Any]]:
    if CRT_PUBLISHED_LENSES_KEY not in st.session_state or not isinstance(
        st.session_state.get(CRT_PUBLISHED_LENSES_KEY), dict
    ):
        st.session_state[CRT_PUBLISHED_LENSES_KEY] = {}
    return st.session_state[CRT_PUBLISHED_LENSES_KEY]  # type: ignore[return-value]


def _safe_len_list(v: Any) -> int:
    return len(v) if isinstance(v, list) else 0


def _try_load_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:  # pylint: disable=broad-except
        return None


def _fingerprint_dict(obj: Dict[str, Any]) -> str:
    try:
        payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    except Exception:  # pylint: disable=broad-except
        return hashlib.sha256(str(obj).encode("utf-8")).hexdigest()[:16]


def _format_utc_stamp(value: Optional[str]) -> str:
    if not value or not isinstance(value, str):
        return ""
    v = value.strip()
    if "T" in v and "-" in v:
        try:
            d, t = v.split("T", 1)
            hhmm = t[:5]
            return f"{d} {hhmm}Z"
        except Exception:  # pylint: disable=broad-except
            return v
    if len(v) >= 16 and "T" in v:
        return f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[9:11]}:{v[11:13]}Z"
    return v


def _first_entity(bundle: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    entities = bundle.get("entities") if isinstance(bundle.get("entities"), dict) else {}
    lst = entities.get(key)
    if isinstance(lst, list) and lst:
        return lst[0] if isinstance(lst[0], dict) else None
    return None


def _pick_text(*vals: Any) -> Optional[str]:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _pick_note(*vals: Any, max_len: int = 180) -> Optional[str]:
    raw = _pick_text(*vals)
    if not raw:
        return None
    s = " ".join(raw.split())
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def _lens_scope_hint(bundle: Dict[str, Any]) -> str:
    btype = bundle.get("bundle_type") if isinstance(bundle.get("bundle_type"), str) else ""

    if btype in ("data_classification", "data_domain", "data"):
        d = _first_entity(bundle, "data_domains")
        if isinstance(d, dict):
            name = _pick_text(d.get("data_name"), d.get("data_domain_name"), d.get("domain_name"), d.get("data_id"))
            cls = _pick_text(d.get("classification_level"), d.get("classification"))
            tier = _pick_text(d.get("data_tier"))
            env = _pick_text(d.get("environment"))
            ctx = " · ".join([x for x in [cls, tier, env] if x])
            return f"Data: {name or 'Data domain'}" + (f" ({ctx})" if ctx else "")
        return "Data classification context"

    if btype == "attack_surface":
        a = _first_entity(bundle, "assets")
        if isinstance(a, dict):
            name = _pick_text(a.get("asset_name"), a.get("asset_id"), "Asset")
            atype = _pick_text(a.get("asset_type"))
            env = _pick_text(a.get("environment"))
            exposure = _pick_text(a.get("exposure_type"))
            ctx = " · ".join([x for x in [atype, env, exposure] if x])
            return f"Asset: {name}" + (f" ({ctx})" if ctx else "")
        return "Attack surface context"

    if btype == "identity":
        i = _first_entity(bundle, "identities")
        if isinstance(i, dict):
            name = _pick_text(i.get("name"), i.get("identity_name"), i.get("identity_id"), "Identity")
            itype = _pick_text(i.get("type"), i.get("identity_type"))
            zone = _pick_text(i.get("zone"))
            priv = _pick_text(i.get("privilege_level"))
            ctx = " · ".join([x for x in [itype, zone, priv] if x])
            return f"Identity: {name}" + (f" ({ctx})" if ctx else "")
        return "Identity context"

    if btype == "supply_chain":
        v = _first_entity(bundle, "vendors")
        if isinstance(v, dict):
            archetype = _pick_text(v.get("vendor_archetype"))
            service = _pick_text(v.get("service_type"))
            name = archetype or (f"Service: {service}" if service else None) or _pick_text(v.get("vendor_id"), "Vendor")
            dep = _pick_text(v.get("dependency_type"))
            crit = _pick_text(v.get("criticality"))
            region = _pick_text(v.get("region"))
            tier = _pick_text(v.get("contract_tier"))
            ctx = " · ".join([x for x in [dep, crit, region, tier] if x])
            return f"Vendor: {name}" + (f" ({ctx})" if ctx else "")
        return "Vendor / dependency context"

    if btype == "telemetry":
        t = _first_entity(bundle, "telemetry")
        if isinstance(t, dict):
            name = _pick_text(t.get("source_name"), t.get("telemetry_id"), "Telemetry source")
            channel = _pick_text(t.get("channel"))
            klass = _pick_text(t.get("signal_class"))
            retain = t.get("retention_days")
            retain_txt = (
                f"{retain}d"
                if isinstance(retain, (int, float)) or (isinstance(retain, str) and retain.strip())
                else None
            )
            ctx = " · ".join([x for x in [channel, klass, retain_txt] if x])
            return f"Source: {name}" + (f" ({ctx})" if ctx else "")
        return "Telemetry context"

    pe = bundle.get("primary_entity") if isinstance(bundle.get("primary_entity"), dict) else {}
    pe_type = pe.get("type") if isinstance(pe.get("type"), str) else "entity"
    pe_id = pe.get("id") if isinstance(pe.get("id"), str) else "—"
    return f"Primary: {pe_type}:{pe_id}"


def _lens_primary_note(bundle: Dict[str, Any]) -> Optional[str]:
    btype = bundle.get("bundle_type") if isinstance(bundle.get("bundle_type"), str) else ""

    if btype in ("data_classification", "data_domain", "data"):
        d = _first_entity(bundle, "data_domains")
        if isinstance(d, dict):
            return _pick_note(d.get("definition"), d.get("description"), d.get("notes"), d.get("examples"))
        return None

    if btype == "attack_surface":
        a = _first_entity(bundle, "assets")
        if isinstance(a, dict):
            return _pick_note(a.get("description"), a.get("notes"), a.get("trust_boundary"), a.get("entry_points"))
        return None

    if btype == "identity":
        i = _first_entity(bundle, "identities")
        if isinstance(i, dict):
            return _pick_note(i.get("notes"), i.get("trust_anchor"), i.get("policy_anchor"), i.get("associated_assets"))
        return None

    if btype == "supply_chain":
        v = _first_entity(bundle, "vendors")
        if isinstance(v, dict):
            ex = _pick_text(v.get("example_vendors"))
            ex_txt = f"Examples: {ex}" if ex else None
            return _pick_note(v.get("notes"), ex_txt, v.get("failure_modes"), v.get("data_access_level"))
        return None

    if btype == "telemetry":
        t = _first_entity(bundle, "telemetry")
        if isinstance(t, dict):
            zones = _pick_text(t.get("linked_zones"))
            zones_txt = f"Zones: {zones}" if zones else None
            return _pick_note(t.get("notes"), zones_txt, t.get("parsing_status"), t.get("enrichment_ready"))
        return None

    return None


def _lens_display_label(bundle: Dict[str, Any], filename: str, lens_code: str) -> str:
    module = bundle.get("module") if isinstance(bundle.get("module"), str) else lens_code.upper()
    btype = bundle.get("bundle_type") if isinstance(bundle.get("bundle_type"), str) else "lens"

    lens_meta = bundle.get("lens_meta") if isinstance(bundle.get("lens_meta"), dict) else {}
    built_at = None
    if isinstance(lens_meta.get("built_at_utc"), str):
        built_at = lens_meta.get("built_at_utc")
    elif isinstance(lens_meta.get("built_at"), str):
        built_at = lens_meta.get("built_at")

    stamp = _format_utc_stamp(built_at) if built_at else ""
    hint = _lens_scope_hint(bundle)

    parts = [p for p in [module, btype, hint, stamp] if p]
    if parts:
        return " · ".join(parts)

    base = os.path.basename(filename).replace(".json", "")
    return f"{lens_code.upper()} · {base}"


def _discover_saved_lenses_from_disk() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}

    if not os.path.isdir(LENS_SHELF_DIR):
        return out

    try:
        for lens_code in sorted(os.listdir(LENS_SHELF_DIR)):
            lens_root = os.path.join(LENS_SHELF_DIR, lens_code)
            bundles_dir = os.path.join(lens_root, "bundles")
            if not os.path.isdir(bundles_dir):
                continue

            for name in sorted(os.listdir(bundles_dir), reverse=True):
                if not name.endswith(".json"):
                    continue

                path = os.path.join(bundles_dir, name)
                payload = _try_load_json_file(path)
                if not isinstance(payload, dict):
                    continue

                label = _lens_display_label(payload, filename=name, lens_code=lens_code)
                if label in out:
                    label = f"{label} · {_fingerprint_dict(payload)[:8]}"

                payload = dict(payload)
                lm = payload.get("lens_meta") if isinstance(payload.get("lens_meta"), dict) else {}
                lm = dict(lm)
                lm.setdefault("source", "disk")
                lm.setdefault("shelf_path_hint", f"lenses/{lens_code}/bundles/{name}")
                payload["lens_meta"] = lm

                out[label] = payload

    except Exception:  # pylint: disable=broad-except
        return out

    return out


def _lens_preview_lines(bundle: Dict[str, Any], show_tech: bool) -> List[str]:
    module = bundle.get("module") if isinstance(bundle.get("module"), str) else None
    btype = bundle.get("bundle_type") if isinstance(bundle.get("bundle_type"), str) else None

    pe = bundle.get("primary_entity") if isinstance(bundle.get("primary_entity"), dict) else {}
    pe_type = pe.get("type") if isinstance(pe.get("type"), str) else None
    pe_id = pe.get("id") if isinstance(pe.get("id"), str) else None

    lens_meta = bundle.get("lens_meta") if isinstance(bundle.get("lens_meta"), dict) else {}
    built_at = lens_meta.get("built_at_utc") or lens_meta.get("built_at") or None
    source = lens_meta.get("source") or bundle.get("_source") or "session"
    shelf_hint = lens_meta.get("shelf_path_hint")

    scope_hint = _lens_scope_hint(bundle)
    note = _lens_primary_note(bundle)

    lines: List[str] = []
    lines.append(f"- **What this lens is about:** {scope_hint}")
    if note:
        lines.append(f"- **Lens note:** {note}")

    lines.append(f"- **Module:** {module or '—'}")
    lines.append(f"- **Bundle type:** `{btype or '—'}`")
    lines.append(f"- **Anchor:** `{pe_type or '—'}` → `{pe_id or '—'}`")

    if built_at:
        lines.append(f"- **Built at:** `{built_at}`")
    lines.append(f"- **Source:** `{source}`")
    if isinstance(shelf_hint, str) and shelf_hint.strip():
        lines.append(f"- **Shelf hint:** `{shelf_hint.strip()}`")

    if show_tech:
        entities = bundle.get("entities") if isinstance(bundle.get("entities"), dict) else {}
        entity_counts: Dict[str, int] = {}
        for k, v in entities.items():
            if isinstance(v, list):
                entity_counts[str(k)] = len(v)
        rel_count = _safe_len_list(bundle.get("relationships"))
        lines.append(f"- **Entities (counts):** `{json.dumps(entity_counts, ensure_ascii=False)}`")
        lines.append(f"- **Relationships:** `{rel_count}`")

    return lines


def _read_historic_last_bundles() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for label, key in LENS_SESSION_KEYS.items():
        b = get_lens_bundle_from_session(key)
        if isinstance(b, dict) and b:
            out[label] = b
    return out


def render_input_bundles_panel(programme_mode_label: str, task_type: str) -> Dict[str, Dict[str, Any]]:
    st.subheader("4. Input Bundles & Lenses")

    with st.expander("✅ Always included", expanded=False):
        st.write(
            "- Org Profile (if present)\n"
            "- Org Governance Scope (frameworks + obligations, if present)\n"
            "- Org Requirements & Legal Obligations\n"
            "- Default lens context (broad scope)\n"
        )
        st.caption("Structural Lenses are optional overlays. Choose them per artefact.")

    included: Dict[str, Dict[str, Any]] = {}

    st.markdown("#### Structural Lenses (optional)")
    st.caption("Select any lenses you want to explicitly anchor into this artefact.")

    show_tech = st.checkbox(
        "Show technical details (counts)",
        value=False,
        help="Optional. Shows entity and relationship counts inside previews.",
    )

    saved_on_disk = _discover_saved_lenses_from_disk()
    published_registry = _ensure_lens_registry()
    historic_last = _read_historic_last_bundles()

    if saved_on_disk:
        with st.expander("💾 Saved lenses on disk (lens shelf)", expanded=False):
            st.caption("Saved lens snapshots (read-only). Select any lenses to include in this build only.")
            options = list(saved_on_disk.keys())
            chosen = st.multiselect(
                "Select saved lenses to include",
                options=options,
                default=[],
                help="Includes the selected saved lenses in this artefact only (no edits).",
            )

            for label in chosen:
                bundle = saved_on_disk.get(label)
                if not isinstance(bundle, dict):
                    continue
                included[label] = bundle
                with st.expander(f"Preview: {label}", expanded=False):
                    for line in _lens_preview_lines(bundle, show_tech=show_tech):
                        st.markdown(line)

    if published_registry:
        with st.expander("📌 Lenses published in this session", expanded=False):
            st.caption("These lenses were published during this runtime session (read-only).")
            for label, bundle in published_registry.items():
                if not isinstance(bundle, dict):
                    continue

                include = st.checkbox(
                    f"Include: {label}",
                    value=False,
                    key=f"include_published_{label}",
                    help="Adds this lens overlay for this build only.",
                )

                with st.expander(f"Preview: {label}", expanded=False):
                    for line in _lens_preview_lines(bundle, show_tech=show_tech):
                        st.markdown(line)

                if include:
                    final_label = label
                    if final_label in included:
                        final_label = f"{label} · {_fingerprint_dict(bundle)[:8]}"
                    included[final_label] = bundle

    if historic_last:
        with st.expander("🧩 Recent lens bundles (session last_bundle keys)", expanded=False):
            st.caption(
                "Compatibility view from historic per-lens session keys (read-only). "
                "Use only if the published registry wasn’t used."
            )
            for label, bundle in historic_last.items():
                if not isinstance(bundle, dict):
                    continue

                include = st.checkbox(
                    f"Include: {label}",
                    value=False,
                    key=f"include_historic_{label}",
                    help="Adds this lens overlay for this build only.",
                )

                with st.expander(f"Preview: {label}", expanded=False):
                    for line in _lens_preview_lines(bundle, show_tech=show_tech):
                        st.markdown(line)

                if include:
                    final_label = label
                    if final_label in included:
                        final_label = f"{label} · {_fingerprint_dict(bundle)[:8]}"
                    included[final_label] = bundle

    if not saved_on_disk and not published_registry and not historic_last:
        st.info("No lens bundles are currently available (session or disk).")
        with st.expander("Create a lens", expanded=False):
            st.page_link("pages/03_🧮_data_classification_registry.py", label="🧮 Data Classification Registry (DCR)")
            st.page_link("pages/04_🧩_attack_surface_mapper.py", label="🧩 Attack Surface Mapper (ASM)")
            st.page_link("pages/05_🔐_identity_access_lens.py", label="🔐 Identity & Access Lens (IAL)")
            st.page_link("pages/06_🛰️_supply_chain_exposure_scanner.py", label="🛰 Supply-Chain Exposure Scanner (SCES)")
            st.page_link("pages/07_📡_telemetry_signal_console.py", label="📡 Telemetry & Signal Console (TSC)")

    if included:
        st.success(f"Selected lenses for this build: {len(included)}")
    else:
        st.caption("No lenses selected. Build will proceed with baseline inclusions only.")

    st.divider()
    return included

# ------------------------------------------------------------
# Section 5 — Build + Save + Manifest + Handoff (Platinum)
# ------------------------------------------------------------
def _safe_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    return v if v else None


def _compute_bundle_id(bundle: Dict[str, Any]) -> str:
    payload = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _save_json(path: str, payload: Dict[str, Any]) -> None:
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _manifest_path(bundle_id: str) -> str:
    return os.path.join(WORKSPACE_MANIFESTS_DIR, f"crt_manifest_{bundle_id}.json")


def _bundle_path(bundle_id: str) -> str:
    return os.path.join(WORKSPACE_BUNDLES_DIR, f"crt_bundle_{bundle_id}.json")


def _build_manifest(
    programme_mode_label: str,
    task_type: str,
    anchor_id: Optional[str],
    anchor_name: Optional[str],
    manifest_notes: Dict[str, Any],
    template_selection: Dict[str, Any],
    lens_bundles: Dict[str, Dict[str, Any]],
    org_profile: Optional[Dict[str, Any]],
    org_scope: Optional[Dict[str, Any]],
    bundle_id: str,
) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    included_lenses: List[Dict[str, Any]] = []
    for label, b in (lens_bundles or {}).items():
        if not isinstance(b, dict):
            continue
        included_lenses.append(
            {
                "label": label,
                "bundle_type": b.get("bundle_type"),
                "module": b.get("module"),
                "lens_id": _fingerprint_dict(b),
                "primary_entity": b.get("primary_entity"),
            }
        )

    baseline = {
        "default_lens_context": "broad_scope",
        "org_profile_included": bool(org_profile),
        "org_governance_scope_included": bool(org_scope),
    }

    compact_profile = None
    if isinstance(org_profile, dict):
        compact_profile = {
            "profile_name": org_profile.get("profile_name"),
            "organisation_name": org_profile.get("organisation_name") or org_profile.get("org_name"),
            "industry": org_profile.get("industry"),
            "environment": org_profile.get("environment"),
            "jurisdictions": org_profile.get("jurisdictions", []),
            "org_size": org_profile.get("org_size"),
        }

    scope_details = None
    if isinstance(org_scope, dict):
        frameworks = org_scope.get("frameworks_in_scope") or []
        obligations = org_scope.get("obligations_ids_in_scope") or []
        scope_details = {
            "frameworks_mode": org_scope.get("frameworks_mode"),
            "frameworks_in_scope": frameworks,
            "framework_count": len(frameworks),
            "obligations_count": len(obligations),
        }

    # Compact template meta (manifest-friendly)
    tpl_meta = {}
    if isinstance(template_selection, dict) and template_selection:
        tpl_meta = {
            "scope_key": template_selection.get("scope_key"),
            "selection_mode": template_selection.get("selection_mode"),
            "template_id": template_selection.get("template_id"),
            "template_name": template_selection.get("template_name"),
            "template_source": template_selection.get("template_source"),
            "sections": template_selection.get("sections", []),
        }

    return {
        "manifest_version": "1.5",
        "bundle_id": bundle_id,
        "built_at_utc": now_utc,
        "programme_mode": programme_mode_label,
        "bundle_type": PROGRAMME_MODES.get(programme_mode_label, "governance"),
        "task_type": task_type,
        "artefact_anchor": {"anchor_id": anchor_id, "anchor_name": anchor_name},
        "task_context_notes": manifest_notes or {},
        "template": tpl_meta,
        "baseline_inclusions": baseline,
        "included_lens_bundles": included_lenses,
        "org_profile": compact_profile,
        "org_governance_scope": scope_details,
        "guardrails": {
            "no_advice": True,
            "no_configuration": True,
            "no_assurance": True,
            "structural_only": True,
        },
        "handoff": {
            "bundle_session_key": CURRENT_PROGRAMME_BUNDLE_KEY,
            "manifest_session_key": CURRENT_PROGRAMME_MANIFEST_KEY,
            "next_module": "🧠 AI Observation Console",
        },
    }


def build_programme_bundle(
    programme_mode_label: str,
    task_type: str,
    anchor_id: Optional[str],
    anchor_name: Optional[str],
    org_profile: Optional[Dict[str, Any]],
    org_scope: Optional[Dict[str, Any]],
    lens_bundles: Dict[str, Dict[str, Any]],
    manifest_notes: Dict[str, Any],
    template_selection: Dict[str, Any],
) -> Dict[str, Any]:
    state = initialise_module_state()
    bundle_type = PROGRAMME_MODES.get(programme_mode_label, "governance")

    artefact_ref = _safe_str(anchor_id) or _safe_str(anchor_name) or "artefact"
    try:
        state.primary_entity = {"type": "artefact", "id": artefact_ref}  # type: ignore[attr-defined]
    except Exception:
        pass

    bundle = build_bundle_for_module(
        module_name=MODULE_NAME,
        bundle_type=bundle_type,
        state=state,
        extra_guardrails={
            "no_advice": True,
            "no_configuration": True,
            "no_assurance": True,
            "structural_only": True,
        },
    )

    bundle["programme_mode"] = programme_mode_label
    bundle["task_type"] = task_type
    bundle["artefact_anchor"] = {"anchor_id": _safe_str(anchor_id), "anchor_name": _safe_str(anchor_name)}
    bundle["org_profile"] = org_profile or {}
    bundle["org_governance_scope"] = org_scope or {}
    bundle["structural_lenses"] = lens_bundles or {}
    bundle["context_notes"] = manifest_notes or {}
    bundle["template"] = template_selection or {}

    meta = bundle.get("meta", {})
    meta["built_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    meta["source"] = "programme_task_builder"
    bundle["meta"] = meta

    return bundle


def _render_current_build_summary(manifest: Dict[str, Any]) -> None:
    anchor = manifest.get("artefact_anchor") or {}
    baseline = manifest.get("baseline_inclusions") or {}
    tpl = manifest.get("template") or {}

    st.markdown(
        f"**Programme:** {manifest.get('programme_mode')} · "
        f"**Task:** {manifest.get('task_type')}  \n"
        f"**Artefact:** {anchor.get('anchor_id') or '—'} — {anchor.get('anchor_name') or '—'}"
    )

    st.caption(
        f"Baseline: `{baseline.get('default_lens_context', 'broad_scope')}`"
        + (" · Org Profile" if baseline.get("org_profile_included") else "")
        + (" · Governance Scope" if baseline.get("org_governance_scope_included") else "")
    )

    if isinstance(tpl, dict) and tpl.get("sections"):
        tname = tpl.get("template_name") or tpl.get("template_id") or "Template"
        st.caption(f"Template: **{tname}** · Sections: {len(tpl.get('sections', []))}")


def render_build_save_handoff(
    programme_mode_label: str,
    task_type: Optional[str],
    anchor_id: Optional[str],
    anchor_name: Optional[str],
    manifest_notes: Dict[str, Any],
    template_selection: Dict[str, Any],
    org_profile: Optional[Dict[str, Any]],
    org_scope: Optional[Dict[str, Any]],
    lens_bundles: Dict[str, Dict[str, Any]],
) -> None:
    st.subheader("5. Build & Handoff")

    missing_task = not (task_type and str(task_type).strip())
    missing_anchor = not _safe_str(anchor_name)
    build_disabled = missing_task or missing_anchor

    c1, c2, c3 = st.columns(3)

    with c1:
        build_clicked = st.button("🔧 Build & Save", disabled=build_disabled, use_container_width=True)

    with c2:
        clear_clicked = st.button(
            "🧹 Clear Current",
            disabled=st.session_state.get(CURRENT_PROGRAMME_MANIFEST_KEY) is None,
            use_container_width=True,
        )

    with c3:
        open_console = st.button("➡️ Open 🧠 AI Observation Console", use_container_width=True)

    if clear_clicked:
        for k in (CURRENT_PROGRAMME_BUNDLE_KEY, CURRENT_PROGRAMME_MANIFEST_KEY):
            st.session_state.pop(k, None)
        st.success("Cleared current handoff. Saved artefacts on disk are unchanged.")
        st.rerun()

    if open_console:
        try:
            st.switch_page("pages/09_🧠_ai_observation_console.py")
        except Exception:
            st.warning("Open the AI Observation Console from the sidebar.")

    if build_clicked and not build_disabled:
        # Pull the latest template choice (in case user changed it and didn’t rerender)
        tpl_sel = st.session_state.get(CURRENT_TASK_TEMPLATE_KEY)
        tpl_sel = tpl_sel if isinstance(tpl_sel, dict) else (template_selection or {})

        built_bundle = build_programme_bundle(
            programme_mode_label=programme_mode_label,
            task_type=str(task_type).strip(),
            anchor_id=_safe_str(anchor_id),
            anchor_name=_safe_str(anchor_name),
            org_profile=org_profile,
            org_scope=org_scope,
            lens_bundles=lens_bundles,
            manifest_notes=manifest_notes or {},
            template_selection=tpl_sel or {},
        )

        bundle_id = _compute_bundle_id(built_bundle)
        manifest = _build_manifest(
            programme_mode_label,
            str(task_type).strip(),
            _safe_str(anchor_id),
            _safe_str(anchor_name),
            manifest_notes or {},
            tpl_sel or {},
            lens_bundles,
            org_profile,
            org_scope,
            bundle_id,
        )

        _save_json(_bundle_path(bundle_id), built_bundle)
        _save_json(_manifest_path(bundle_id), manifest)

        st.session_state[CURRENT_PROGRAMME_BUNDLE_KEY] = built_bundle
        st.session_state[CURRENT_PROGRAMME_MANIFEST_KEY] = manifest

        st.success("Built, saved, and set as current handoff.")

    current_manifest = st.session_state.get(CURRENT_PROGRAMME_MANIFEST_KEY)
    if isinstance(current_manifest, dict):
        st.markdown("#### Current Artefact (Handoff)")
        _render_current_build_summary(current_manifest)

        manifest_json = json.dumps(current_manifest, indent=2, ensure_ascii=False)
        st.download_button(
            "⬇️ Download Current Manifest (JSON)",
            data=manifest_json.encode("utf-8"),
            file_name=f"crt_manifest_{current_manifest.get('bundle_id')}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.code(manifest_json, language="json")
    else:
        st.caption("No current handoff. Configure Sections 1–4, then click **Build & Save**.")

# -------------------------------------------------------------------------------------------------
# Footer — parity
# -------------------------------------------------------------------------------------------------
def crt_footer() -> None:
    st.divider()
    st.caption(
        "© Blake Media Ltd. | Cyber Resilience Toolkit by Blake Wiltshire — "
        "All content is structural and conceptual; no configuration, advice, or assurance is provided."
    )

# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration & Main View
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Programme Builder & AI Export",
    page_icon="🎛",
    layout="wide",
)

def render_header() -> None:
    st.title(UI_TITLE)
    st.caption(
        "Build programme artefacts as a compact manifest + a normalised structural bundle. "
    )


def render_user_templates_tab() -> None:
    """🧱 User Templates — optional workbench (not part of the main build flow)."""
    st.markdown("## 🧱 User Templates")
    st.caption(
        "Reusable section layouts created by you. Templates affect structure only; they do not contain content."
    )

    defaults = load_default_templates()
    users = load_user_templates()

    # --- Quick summary
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Default templates", str(len(defaults)))
    with c2:
        st.metric("User templates", str(len(users)))

    st.divider()

    # --- Filter + selection
    categories = ["governance", "architecture", "metrics", "simulation", "all"]
    filter_cat = st.selectbox("Filter by category", categories, index=0)

    def _cat_of(tpl: Dict[str, Any]) -> str:
        cat = str(tpl.get("category") or "").strip().lower()
        if cat:
            return cat
        applies = tpl.get("applies_to", [])
        applies = [str(x).strip().lower() for x in applies] if isinstance(applies, list) else []
        for cand in ["governance", "architecture", "metrics", "simulation"]:
            if cand in applies:
                return cand
        return "governance"

    # Build list of user templates
    user_list: List[Dict[str, Any]] = []
    for tid, tpl in users.items():
        if not isinstance(tpl, dict):
            continue
        tpl_cat = _cat_of(tpl)
        if filter_cat != "all" and tpl_cat != filter_cat:
            continue
        user_list.append({
            "template_id": str(tpl.get("template_id") or tid).strip(),
            "category": tpl_cat,
            "label": str(tpl.get("label") or tpl.get("name") or "").strip(),
            "sections": tpl.get("sections") if isinstance(tpl.get("sections"), list) else [],
            "notes": str(tpl.get("notes") or "").strip(),
            "derived_from_template_id": str(tpl.get("derived_from_template_id") or "").strip(),
            "created_at": str(tpl.get("created_at") or "").strip(),
            "updated_at": str(tpl.get("updated_at") or "").strip(),
        })

    user_list = sorted(user_list, key=lambda x: (x.get("category",""), x.get("label",""), x.get("template_id","")))

    options = ["(Create new)"] + [f'{u["label"]} — {u["template_id"]}' for u in user_list]
    choice = st.selectbox("Select a user template", options)

    selected: Optional[Dict[str, Any]] = None
    if choice != "(Create new)":
        tid = choice.split("—")[-1].strip()
        selected = next((u for u in user_list if u["template_id"] == tid), None)

    st.divider()

    # --- Clone from default (fast path)
    with st.expander("Clone from a default template", expanded=False):
        default_items = sorted(
            [{"template_id": tid, **tpl} for tid, tpl in defaults.items() if isinstance(tpl, dict)],
            key=lambda x: (str(x.get("category") or ""), str(x.get("name") or ""))
        )

        default_labels = [f'{d.get("name","")} — {d.get("template_id","")}' for d in default_items]
        if default_labels:
            pick = st.selectbox("Default template to clone", ["(Select)"] + default_labels)
            if pick != "(Select)":
                base_id = pick.split("—")[-1].strip()
                base = next((d for d in default_items if d.get("template_id") == base_id), None)
                if base:
                    st.caption("This creates a new user template based on the default structure. Structure only.")
                    if st.button("🧬 Create draft from default", use_container_width=True):
                        new_id = f"TPL-USER-{uuid.uuid4().hex[:8].upper()}"
                        st.session_state["user_tpl_draft"] = {
                            "template_id": new_id,
                            "category": str(base.get("category") or "governance").strip().lower(),
                            "label": f'{str(base.get("name") or "").strip()} (User)',
                            "sections": list(base.get("sections") or []),
                            "notes": "",
                            "derived_from_template_id": str(base.get("template_id") or "").strip(),
                        }
                        st.success("Draft created below. Review and save when ready.")
                        st.rerun()
        else:
            st.info("No default templates available to clone.")

    # Draft from session (optional)
    draft = st.session_state.get("user_tpl_draft")
    if isinstance(draft, dict) and not selected:
        selected = {
            "template_id": draft.get("template_id",""),
            "category": draft.get("category","governance"),
            "label": draft.get("label",""),
            "sections": draft.get("sections", []),
            "notes": draft.get("notes",""),
            "derived_from_template_id": draft.get("derived_from_template_id",""),
            "created_at": "",
            "updated_at": "",
        }

    # --- Editor
    st.subheader("Template editor")
    st.caption("Headings only. No prose. This is a formatting scaffold written into the programme handoff payload.")

    template_id = st.text_input("Template ID", value=(selected.get("template_id") if selected else f"TPL-USER-{uuid.uuid4().hex[:8].upper()}"))
    category = st.selectbox("Category", ["governance", "architecture", "metrics", "simulation"], index=0 if not selected else ["governance","architecture","metrics","simulation"].index(selected.get("category","governance")))
    label = st.text_input("Label", value=(selected.get("label") if selected else ""))
    notes = st.text_input("Notes (optional)", value=(selected.get("notes") if selected else ""))
    derived_from = st.text_input("Derived from template ID (optional)", value=(selected.get("derived_from_template_id") if selected else ""))

    sections_text = ""
    if selected and isinstance(selected.get("sections"), list):
        sections_text = "\n".join([str(s) for s in selected.get("sections") if str(s).strip()])

    raw_sections = st.text_area(
        "Sections (one per line)",
        value=sections_text,
        height=220,
        placeholder="e.g.\nPurpose\nScope\nDefinitions\n...",
    )
    sections = [line.strip() for line in (raw_sections or "").splitlines() if line.strip()]

    # --- Actions
    a, b = st.columns([1, 1])
    can_save = bool(template_id.strip()) and bool(label.strip()) and bool(sections)

    with a:
        if st.button("💾 Save template", disabled=not can_save, use_container_width=True):
            tid = template_id.strip()
            users_latest = load_user_templates()  # refresh
            now = _now_utc_iso()
            existing = users_latest.get(tid, {})
            created_at = str(existing.get("created_at") or now).strip()

            users_latest[tid] = {
                "template_id": tid,
                "name": label.strip(),
                "label": label.strip(),
                "category": category,
                "applies_to": [category],
                "sections": sections,
                "notes": notes.strip(),
                "created_at": created_at,
                "updated_at": now,
                "derived_from_template_id": derived_from.strip(),
                "is_user": True,
            }

            if _save_user_templates(users_latest):
                st.success("User template saved.")
                st.session_state.pop("user_tpl_draft", None)
                st.rerun()
            st.error("Failed to save user template.")

    with b:
        if st.button("🧽 Clear editor", use_container_width=True):
            st.session_state.pop("user_tpl_draft", None)
            st.rerun()

    # --- Transparency
    with st.expander("Show user templates file path", expanded=False):
        st.code(USER_TEMPLATES_JSON, language="text")

# -------------------------------------------------------------------------------------------------
# 🔍 Verify (Current Artefact)
# -------------------------------------------------------------------------------------------------
def render_review_tab() -> None:
    """
    🔍 Verify

    Purpose:
    - Turn the Current manifest + bundle into a **verified artefact** for downstream interpretation.
    - Resolve ambiguous mode fields into explicit, human-readable semantics.
    - Attach in-scope CRT-REQ / CRT-LR records (and lens bundles) so external AI does not have to guess.
    - Attach resolved CRT spine subsets (CRT-C controls + derived CRT-F failures + derived CRT-N compensations)
      with full descriptors (same “record bodies included” behaviour as crt_c_anchor_controls).
    - Write a single immutable JSON file to WORKSPACE_VERIFIED_DIR.

    Verify does not:
    - Call AI
    - Edit catalogues, profiles, or lenses
    """
    st.markdown("## 🔍 Verify")
    st.caption("Prepare a verified artefact for downstream interpretation.")

    # ------------------------------------------------------------
    # Catalogue helpers (local to Verify)
    # ------------------------------------------------------------
    def _catalogue_paths_local(catalogue_name: str) -> Tuple[str, str]:
        """Return (active_csv_path, default_csv_path)."""
        active_path = os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues", f"{catalogue_name}.csv")
        default_path = os.path.join(PROJECT_ROOT, "apps", "data_sources", "defaults", f"{catalogue_name}.csv")
        return active_path, default_path

    def _json_view_dir_local() -> str:
        return os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues", "json")

    def _regenerate_json_view_local(catalogue_name: str, active_path: str) -> Tuple[bool, str]:
        """
        Generate crt_catalogues/json/{CAT}.json as a list-of-records view.

        Critical:
        - Strip UTF-8 BOM from header keys (fixes \ufeffrequirement_set_id etc).
        """
        json_path = os.path.join(_json_view_dir_local(), f"{catalogue_name}.json")
        try:
            if not os.path.isfile(active_path):
                return False, json_path

            _ensure_dir(_json_view_dir_local())

            raw = b""
            with open(active_path, "rb") as f:
                raw = f.read()

            text_csv = ""
            for enc in ("utf-8", "utf-8-sig", "latin1"):
                try:
                    text_csv = raw.decode(enc)
                    break
                except Exception:  # pylint: disable=broad-except
                    continue
            if not text_csv:
                text_csv = raw.decode("utf-8", errors="replace")

            reader = csv.DictReader(text_csv.splitlines())
            records: List[Dict[str, Any]] = []
            for row in reader:
                clean: Dict[str, Any] = {}
                for k, v in row.items():
                    key = str(k).strip().lstrip("\ufeff")  # ✅ BOM strip at source
                    clean[key] = (v if v is not None else "")
                records.append(clean)

            payload: Dict[str, Any] = {
                "catalogue": catalogue_name,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "source_csv": os.path.relpath(active_path, PROJECT_ROOT),
                "records": records,
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            return True, json_path
        except Exception:  # pylint: disable=broad-except
            return False, json_path

    # ----------------------------
    def _manifest_path_for_bundle_id(bundle_id: str) -> str:
        return os.path.join(WORKSPACE_MANIFESTS_DIR, f"crt_manifest_{bundle_id}.json")

    def _bundle_path_for_bundle_id(bundle_id: str) -> str:
        return os.path.join(WORKSPACE_BUNDLES_DIR, f"crt_bundle_{bundle_id}.json")

    def _safe_filename_fragment(value: Optional[str], max_len: int = 48) -> str:
        """Convert free text into a filename-safe fragment."""
        s = str(value or "").strip()
        if not s:
            return ""
        s = re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-._")
        s = re.sub(r"-+", "-", s)
        return s[:max_len] if len(s) > max_len else s

    def _latest_verified_path_for_bundle_id(bundle_id: str, anchor_hint: str = "") -> str:
        """Return the most recent verified artefact matching this bundle_id."""
        try:
            if not os.path.isdir(WORKSPACE_VERIFIED_DIR):
                return ""

            short_prefix = "crt_verified__"
            legacy_prefix = f"crt_verified_{bundle_id}__"

            all_files = [
                f for f in os.listdir(WORKSPACE_VERIFIED_DIR)
                if f.endswith(".json") and (f.startswith(short_prefix) or f.startswith(legacy_prefix))
            ]
            all_files.sort(reverse=True)

            want_anchor = (anchor_hint or "").strip()

            for fn in all_files[:250]:
                fp = os.path.join(WORKSPACE_VERIFIED_DIR, fn)
                payload = _safe_load_json(fp)
                if not isinstance(payload, dict):
                    continue

                if str(payload.get("bundle_id") or "").strip() != str(bundle_id).strip():
                    continue

                if want_anchor:
                    ident = payload.get("identity") if isinstance(payload.get("identity"), dict) else {}
                    a_id = str(ident.get("anchor_id") or "").strip()
                    a_name = str(ident.get("anchor_name") or "").strip()

                    if not a_id and not a_name:
                        aa = payload.get("artefact_anchor") if isinstance(payload.get("artefact_anchor"), dict) else {}
                        a_id = str(aa.get("anchor_id") or "").strip()
                        a_name = str(aa.get("anchor_name") or "").strip()

                    if want_anchor not in (a_id, a_name):
                        continue

                return fp

            return ""
        except Exception:  # pylint: disable=broad-except
            return ""

    def _verified_path_for_bundle_id(bundle_id: str, anchor_hint: str, task_type: str) -> str:
        """Create a non-overwriting verified filename (anchor + timestamp)."""
        _ensure_dir(WORKSPACE_VERIFIED_DIR)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        a = _safe_filename_fragment(anchor_hint, max_len=32) or "artefact"

        base = f"crt_verified__{a}__{ts}.json"
        vp = os.path.join(WORKSPACE_VERIFIED_DIR, base)

        n = 2
        while os.path.exists(vp):
            vp = os.path.join(WORKSPACE_VERIFIED_DIR, f"crt_verified__{a}__{ts}__v{n}.json")
            n += 1
        return vp

    def _list_bundle_ids_on_disk() -> List[str]:
        ids: set[str] = set()

        if os.path.isdir(WORKSPACE_MANIFESTS_DIR):
            for fn in os.listdir(WORKSPACE_MANIFESTS_DIR):
                if fn.startswith("crt_manifest_") and fn.endswith(".json"):
                    bid = fn.replace("crt_manifest_", "").replace(".json", "").strip()
                    if bid:
                        ids.add(bid)

        if os.path.isdir(WORKSPACE_BUNDLES_DIR):
            for fn in os.listdir(WORKSPACE_BUNDLES_DIR):
                if fn.startswith("crt_bundle_") and fn.endswith(".json"):
                    bid = fn.replace("crt_bundle_", "").replace(".json", "").strip()
                    if bid:
                        ids.add(bid)

        return sorted(list(ids), reverse=True)

    def _json_sanitise(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            out: Dict[str, Any] = {}
            for k, v in value.items():
                out[str(k)] = _json_sanitise(v)
            return out
        if isinstance(value, (list, tuple, set)):
            return [_json_sanitise(v) for v in list(value)]
        try:
            import datetime as _dt
            if isinstance(value, (_dt.datetime, _dt.date)):
                return value.isoformat()
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            import pathlib as _pl
            if isinstance(value, _pl.Path):
                return str(value)
        except Exception:  # pylint: disable=broad-except
            pass
        if isinstance(value, (bytes, bytearray)):
            return bytes(value).decode("utf-8", errors="replace")
        return str(value)

    def _safe_dump(obj: Any) -> str:
        try:
            return json.dumps(_json_sanitise(obj), indent=2, ensure_ascii=False)
        except Exception:  # pylint: disable=broad-except
            return json.dumps({"error": "Unable to render JSON"}, indent=2, ensure_ascii=False)

    def _compact_list(v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            s = v.strip()
            return [s] if s else []
        if not isinstance(v, list):
            return []
        out: List[str] = []
        for x in v:
            s = str(x).strip()
            if s:
                out.append(s)
        return out

    def _get_nested(d: Any, path: List[str], default: Any = None) -> Any:
        cur = d
        for k in path:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k)
        return cur if cur is not None else default

    def _catalogue_json_path(catalogue_name: str) -> str:
        return os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues", "json", f"{catalogue_name}.json")

    def _load_or_regen_catalogue_json(catalogue_name: str) -> Tuple[Optional[Dict[str, Any]], str, bool]:
        json_path = _catalogue_json_path(catalogue_name)
        payload = _safe_load_json(json_path)
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return payload, json_path, False

        active_path, _default_path = _catalogue_paths_local(catalogue_name)
        ok, jp = _regenerate_json_view_local(catalogue_name, active_path)
        if ok:
            payload2 = _safe_load_json(jp)
            if isinstance(payload2, dict) and isinstance(payload2.get("records"), list):
                return payload2, jp, True
        return None, json_path, False

    def _filter_records(payload: Dict[str, Any], key_field: str, allowed_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Filter by ID field, with BOM-resilient matching.

        Fixes cases like:
          - requirement_set_id stored as '\ufeffrequirement_set_id'
        """
        allowed = set([str(x).strip() for x in (allowed_ids or []) if str(x).strip()])
        if not allowed:
            return []

        out: List[Dict[str, Any]] = []
        records = payload.get("records", []) if isinstance(payload.get("records"), list) else []
        bom_key = "\ufeff" + str(key_field)

        for r in records:
            if not isinstance(r, dict):
                continue
            v = str(r.get(key_field, "") or r.get(bom_key, "")).strip()
            if v and v in allowed:
                out.append(r)

        return out

    def _frameworks_mode_semantics(mode_key: str) -> Dict[str, str]:
        mapping = {
            "default_only": {
                "mode_key": "default_only",
                "label": "Default only",
                "meaning": "Use only the shipped CRT defaults. CRT-REQ selections are not applied as an overlay.",
            },
            "overlay": {
                "mode_key": "overlay",
                "label": "Overlay",
                "meaning": "Treat selected CRT-REQ requirement sets as an overlay on top of the shipped CRT defaults.",
            },
            "framework_only": {
                "mode_key": "framework_only",
                "label": "Primary requirements lens",
                "meaning": "Treat selected CRT-REQ requirement sets as the primary requirements lens (still structurally mapped via CRT-C).",
            },
        }
        return mapping.get(mode_key, {
            "mode_key": (mode_key or "").strip() or "unknown",
            "label": "Unknown",
            "meaning": "No recognised frameworks_mode value was provided.",
        })

    def _default_lens_semantics(default_lens_context: str) -> Dict[str, str]:
        mapping = {
            "broad_scope": {
                "context_key": "broad_scope",
                "meaning": "Include the shipped default lens context across the CRT spine (broad, baseline scope).",
            }
        }
        return mapping.get(default_lens_context, {
            "context_key": (default_lens_context or "").strip() or "unknown",
            "meaning": "No recognised default_lens_context value was provided.",
        })

    # ------------------------------------------------------------
    # Resolve Current artefact OR load-from-disk
    # ------------------------------------------------------------
    current_manifest: Optional[Dict[str, Any]] = st.session_state.get(CURRENT_PROGRAMME_MANIFEST_KEY)
    current_bundle: Optional[Dict[str, Any]] = st.session_state.get(CURRENT_PROGRAMME_BUNDLE_KEY)

    if not current_manifest or not current_bundle:
        st.markdown("### Load a saved artefact")
        st.caption("No Current artefact is loaded in this session. You can load a saved manifest + bundle by bundle_id.")

        bundle_ids = _list_bundle_ids_on_disk()
        if not bundle_ids:
            st.info("No saved manifests/bundles found on disk yet. Build an artefact in **🎛 Task Builder** first.")
            return

        chosen_id = st.selectbox("Saved bundle_id", options=bundle_ids, index=0, key="crt_verify_load_bundle_id")

        if st.button("📥 Load into Current", use_container_width=True, key="crt_verify_load_into_current"):
            mp = _manifest_path_for_bundle_id(chosen_id)
            bp = _bundle_path_for_bundle_id(chosen_id)

            loaded_m = _safe_load_json(mp)
            loaded_b = _safe_load_json(bp)

            if not loaded_m:
                st.error(f"Manifest not found or unreadable: `{os.path.relpath(mp, PROJECT_ROOT)}`")
                return
            if not loaded_b:
                st.error(f"Bundle not found or unreadable: `{os.path.relpath(bp, PROJECT_ROOT)}`")
                return

            st.session_state[CURRENT_PROGRAMME_MANIFEST_KEY] = loaded_m
            st.session_state[CURRENT_PROGRAMME_BUNDLE_KEY] = loaded_b
            st.success("✅ Loaded into session as Current.")
            st.rerun()

        return

    # ------------------------------------------------------------
    # Extract key fields
    # ------------------------------------------------------------
    bundle_id = str((current_manifest or {}).get("bundle_id") or (current_bundle or {}).get("bundle_id") or "").strip()
    programme_mode = str((current_bundle or {}).get("programme_mode") or (current_manifest or {}).get("programme_mode") or "").strip()
    task_type = str((current_bundle or {}).get("task_type") or (current_manifest or {}).get("task_type") or "").strip()

    anchor_id = str(_get_nested(current_bundle, ["artefact_anchor", "anchor_id"], "") or "").strip()
    anchor_name = str(_get_nested(current_bundle, ["artefact_anchor", "anchor_name"], "") or "").strip()

    template = (current_bundle or {}).get("template") if isinstance((current_bundle or {}).get("template"), dict) else {}
    template_sections = _compact_list((template or {}).get("sections"))
    template_id = str((template or {}).get("template_id") or "").strip()
    template_source = str((template or {}).get("template_source") or (template or {}).get("source") or "").strip() or "default"

    org_scope = (current_bundle or {}).get("org_governance_scope") if isinstance((current_bundle or {}).get("org_governance_scope"), dict) else {}
    frameworks_mode_key = str((org_scope or {}).get("frameworks_mode") or "").strip()
    frameworks_in_scope = _compact_list((org_scope or {}).get("frameworks_in_scope"))
    obligations_ids_in_scope = _compact_list((org_scope or {}).get("obligations_ids_in_scope"))

    baseline_default_lens_context = str(
        (current_manifest or {}).get("baseline_inclusions", {}).get("default_lens_context", "broad_scope")
        if isinstance((current_manifest or {}).get("baseline_inclusions"), dict)
        else "broad_scope"
    ).strip()

    lens_bundles = (current_bundle or {}).get("structural_lenses") if isinstance((current_bundle or {}).get("structural_lenses"), dict) else {}
    lens_keys = sorted([k for k in lens_bundles.keys()])

    # ------------------------------------------------------------
    # Resolve catalogue attachments (CRT-REQ / CRT-LR)
    # ------------------------------------------------------------
    req_payload, req_json_path, req_regen = _load_or_regen_catalogue_json("CRT-REQ")
    lr_payload, lr_json_path, lr_regen = _load_or_regen_catalogue_json("CRT-LR")

    req_records_in_scope: List[Dict[str, Any]] = []
    lr_records_in_scope: List[Dict[str, Any]] = []

    if isinstance(req_payload, dict):
        req_records_in_scope = _filter_records(req_payload, "requirement_set_id", frameworks_in_scope)

    if isinstance(lr_payload, dict):
        lr_records_in_scope = _filter_records(lr_payload, "lr_id", obligations_ids_in_scope)

    # ------------------------------------------------------------
    # Emphasis block (custom vs mapped)
    # ------------------------------------------------------------
    emphasis: Dict[str, Any] = {
        "mapped_context_present": {
            "crt_req_in_scope_records": len(req_records_in_scope),
            "crt_lr_in_scope_records": len(lr_records_in_scope),
            "lens_bundles_selected": len(lens_keys),
        },
        "custom_inputs_present": {
            "custom_titles": bool(_get_nested(current_bundle, ["context_notes", "custom_titles"], None)),
            "custom_notes": bool(str((current_bundle or {}).get("context_notes") or "").strip()),
        },
        "notes": (
            "Mapped items are those referenced by explicit IDs (e.g. CRT-REQ requirement_set_id, CRT-LR lr_id). "
            "Custom items are those supplied as free-text (if present)."
        ),
    }

    # ------------------------------------------------------------
    # Checklist
    # ------------------------------------------------------------
    checks: List[Tuple[str, bool]] = []
    checks.append(("Manifest present", isinstance(current_manifest, dict) and bool(current_manifest)))
    checks.append(("Bundle present", isinstance(current_bundle, dict) and bool(current_bundle)))
    checks.append(("Template scaffold present", bool(template_id) and bool(template_sections)))
    checks.append(("Requirements semantics resolved (default/overlay/primary)", bool(frameworks_mode_key)))
    checks.append(("Lens semantics resolved (default lens context)", bool(baseline_default_lens_context)))
    checks.append(("CRT-REQ JSON attached", isinstance(req_payload, dict)))
    checks.append(("CRT-LR JSON attached", isinstance(lr_payload, dict)))
    checks.append(("Emphasis block written (custom vs mapped)", True))

    all_ok = all(ok for _label, ok in checks)

    # ------------------------------------------------------------
    # UI: Snapshot + Checklist (keep “good display”)
    # ------------------------------------------------------------
    st.markdown("### Snapshot")
    c1, c2 = st.columns([1.15, 0.85])

    with c1:
        if bundle_id:
            st.write(f"**bundle_id:** `{bundle_id}`")
        else:
            st.warning("Missing bundle_id (expected in manifest/bundle).")

        st.write(f"**programme_mode:** `{programme_mode or '—'}`")
        st.write(f"**task_type:** `{task_type or '—'}`")
        if anchor_id or anchor_name:
            st.write(f"**anchor:** `{anchor_name or '—'}`  ·  `{anchor_id or '—'}`")

        st.markdown("#### Resolved semantics")
        fm = _frameworks_mode_semantics(frameworks_mode_key)
        st.write(f"**frameworks_mode:** `{fm.get('mode_key')}` · **{fm.get('label')}**")
        st.caption(fm.get("meaning", ""))

        dl = _default_lens_semantics(baseline_default_lens_context)
        st.write(f"**default_lens_context:** `{dl.get('context_key')}`")
        st.caption(dl.get("meaning", ""))

        st.markdown("#### In-scope selections")
        st.write(f"- **frameworks_in_scope:** `{len(frameworks_in_scope)}`")
        st.write(f"- **obligations_ids_in_scope:** `{len(obligations_ids_in_scope)}`")
        st.write(f"- **lens bundles selected:** `{len(lens_keys)}`")

        with st.expander("Preview template sections", expanded=False):
            if template_sections:
                st.code("\n".join(template_sections), language="text")
            else:
                st.caption("No template sections found.")

    with c2:
        st.markdown("#### Verify checklist")
        for label, ok in checks:
            st.write(f"{'✅' if ok else '—'} {label}")

        st.divider()

        st.markdown("#### Attachments status")
        st.write(f"- CRT-REQ JSON: {'✅' if isinstance(req_payload, dict) else '—'}")
        st.write(f"- CRT-LR JSON: {'✅' if isinstance(lr_payload, dict) else '—'}")
        st.write(f"- Regenerated this session: CRT-REQ `{req_regen}` · CRT-LR `{lr_regen}`")

        with st.expander("Show JSON sources (paths)", expanded=False):
            st.code(os.path.relpath(req_json_path, PROJECT_ROOT), language="text")
            st.code(os.path.relpath(lr_json_path, PROJECT_ROOT), language="text")

    st.divider()

    # ------------------------------------------------------------
    # Create verified artefact
    # ------------------------------------------------------------
    st.markdown("### Create verified artefact")
    st.caption("Writes a single immutable JSON artefact for downstream interpretation.")

    if not bundle_id:
        st.info("A verified artefact requires a bundle_id. Build the artefact again in **🎛 Task Builder**.")
        return

    confirm = st.checkbox("Confirm create verified artefact", value=False, key=f"crt_verify_confirm_{bundle_id}")

    if not all_ok:
        st.warning("Resolve the missing checklist items before creating a verified artefact.")

    if st.button(
        "✅ Create verified artefact",
        use_container_width=True,
        disabled=((not confirm) or (not all_ok)),
        key=f"crt_verify_create_btn_{bundle_id}",
    ):
        try:
            _ensure_dir(WORKSPACE_VERIFIED_DIR)

            # ======================================================================
            # SHARED HELPERS (single source of truth)
            # ======================================================================
            def _norm_token(s: Any) -> str:
                return str(s or "").strip()

            def _split_ids(value: Any) -> List[str]:
                if value is None:
                    return []
                if isinstance(value, list):
                    vals: List[str] = []
                    for v in value:
                        vals.extend(_split_ids(v))
                    return vals
                s = str(value).strip()
                if not s:
                    return []
                parts: List[str] = []
                for tok in s.replace(",", ";").split(";"):
                    t = tok.strip()
                    if t:
                        parts.append(t)
                return parts

            def _strip_bom_key(k: Any) -> str:
                return str(k or "").lstrip("\ufeff").strip()

            def _normalise_record_keys(r: Dict[str, Any]) -> Dict[str, Any]:
                out: Dict[str, Any] = {}
                for k, v in (r or {}).items():
                    out[_strip_bom_key(k)] = v
                return out

            def _normalise_records(records: Any) -> List[Dict[str, Any]]:
                if not isinstance(records, list):
                    return []
                out: List[Dict[str, Any]] = []
                for r in records:
                    if isinstance(r, dict):
                        out.append(_normalise_record_keys(r))
                return out

            def _catalogue_meta(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
                """Return a full catalogue view for AI handoff (records included)."""
                if not isinstance(payload, dict):
                    return {"record_count": 0, "headers": [], "records": []}
                records = _normalise_records(payload.get("records", []))
                headers: List[str] = []
                if records:
                    headers = sorted({str(k) for rr in records for k in rr.keys()})
                return {
                    "record_count": len(records),
                    "headers": headers,
                    "records": records,
                    "source_csv": payload.get("source_csv"),
                    "generated_at": payload.get("generated_at"),
                }

            def _catalogue_meta_info(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
                """Return metadata-only catalogue view (no record bodies)."""
                if not isinstance(payload, dict):
                    return {"record_count": 0, "headers": []}
                records = _normalise_records(payload.get("records", []))
                headers: List[str] = []
                if records:
                    headers = sorted({str(k) for rr in records for k in rr.keys()})
                return {
                    "record_count": len(records),
                    "headers": headers,
                    "source_csv": payload.get("source_csv"),
                    "generated_at": payload.get("generated_at"),
                }

            def _detect_id_column(records: List[Dict[str, Any]], candidates: List[str]) -> str:
                if not records:
                    return ""
                keys = set(records[0].keys())
                for c in candidates:
                    if c in keys:
                        return c
                return ""

            def _index_by_id(records: List[Dict[str, Any]], id_col: str) -> Dict[str, Dict[str, Any]]:
                idx: Dict[str, Dict[str, Any]] = {}
                if not id_col:
                    return idx
                for r in records:
                    rid = _norm_token(r.get(id_col))
                    if rid:
                        idx[rid] = r
                return idx

            def _select_rows_by_ids(
                payload: Optional[Dict[str, Any]],
                id_candidates: List[str],
                wanted_ids: List[str],
            ) -> Tuple[str, List[Dict[str, Any]], List[str]]:
                """
                Deterministic row selection:
                - normalise keys (strip BOM)
                - detect id column
                - build id->row map
                - return rows in the same order as wanted_ids
                - also return missing ids for traceability
                """
                if not isinstance(payload, dict):
                    return "", [], sorted(set([_norm_token(x) for x in (wanted_ids or []) if _norm_token(x)]))

                records = _normalise_records(payload.get("records", []))
                id_col = _detect_id_column(records, id_candidates)
                if not id_col:
                    missing = sorted(set([_norm_token(x) for x in (wanted_ids or []) if _norm_token(x)]))
                    return "", [], missing

                idx = _index_by_id(records, id_col)
                out: List[Dict[str, Any]] = []
                missing: List[str] = []

                for wid in [ _norm_token(x) for x in (wanted_ids or []) if _norm_token(x) ]:
                    row = idx.get(wid)
                    if row:
                        out.append(row)
                    else:
                        missing.append(wid)

                # dedupe missing
                missing = sorted(set([m for m in missing if m]))
                return id_col, out, missing

            def _extract_mapped_ids_from_controls(
                controls: List[Dict[str, Any]],
                field_candidates: List[str],
            ) -> List[str]:
                ids: List[str] = []
                for c in controls or []:
                    if not isinstance(c, dict):
                        continue
                    # keys already normalised for CRT-C rows via _normalise_record_keys if we apply it
                    picked: Any = None
                    for f in field_candidates:
                        if f in c and str(c.get(f) or "").strip():
                            picked = c.get(f)
                            break
                    ids.extend(_split_ids(picked))
                cleaned = [_norm_token(x) for x in ids if _norm_token(x)]
                return sorted(set(cleaned))

            # ======================================================================
            # Resolve CRT backbone + default lens context (orientation)
            # ======================================================================
            backbone_catalogues = ["CRT-G", "CRT-C", "CRT-F", "CRT-N"]
            backbone: Dict[str, Any] = {}
            backbone_regen: List[str] = []

            for cat in backbone_catalogues:
                pld, jp, did_regen = _load_or_regen_catalogue_json(cat)
                backbone[cat] = _catalogue_meta(pld)
                backbone[cat]["json_path"] = jp
                if did_regen:
                    backbone_regen.append(cat)

            lens_catalogues = ["CRT-AS", "CRT-D", "CRT-I", "CRT-SC", "CRT-T"]
            default_lens_context: Dict[str, Any] = {
                "default_lens_context": baseline_default_lens_context or "broad_scope",
                "catalogues": {},
            }
            for cat in lens_catalogues:
                pld, jp, did_regen = _load_or_regen_catalogue_json(cat)
                default_lens_context["catalogues"][cat] = _catalogue_meta(pld)
                default_lens_context["catalogues"][cat]["json_path"] = jp
                if did_regen:
                    backbone_regen.append(cat)

            # ======================================================================
            # Anchor record attachment (STD/POL) + anchor-mapped controls
            # ======================================================================
            def _anchor_catalogue_for_anchor_id(aid: str) -> Tuple[str, str]:
                x = (aid or "").strip().upper()
                if x.startswith("STD-"):
                    return "CRT-STD", "standard_id"
                if x.startswith("POL-"):
                    return "CRT-POL", "policy_id"
                return "", ""

            def _find_anchor_record(payload: Optional[Dict[str, Any]], id_field: str, aid: str) -> Optional[Dict[str, Any]]:
                if not isinstance(payload, dict):
                    return None
                records = _normalise_records(payload.get("records", []))
                want = str(aid or "").strip()
                if not want or not id_field:
                    return None
                for r in records:
                    if str(r.get(id_field) or "").strip() == want:
                        return r
                return None

            anchor_catalogue_name, anchor_id_field = _anchor_catalogue_for_anchor_id(anchor_id)

            anchor_catalogue_payload: Optional[Dict[str, Any]] = None
            anchor_catalogue_json_path = ""
            anchor_catalogue_regen = False
            anchor_record: Optional[Dict[str, Any]] = None
            anchor_mapped_control_ids: List[str] = []
            anchor_mapped_policy_ids: List[str] = []

            if anchor_catalogue_name and anchor_id_field and anchor_id:
                anchor_catalogue_payload, anchor_catalogue_json_path, anchor_catalogue_regen = _load_or_regen_catalogue_json(anchor_catalogue_name)
                anchor_record = _find_anchor_record(anchor_catalogue_payload, anchor_id_field, anchor_id)

                if isinstance(anchor_record, dict):
                    anchor_mapped_control_ids = _split_ids(
                        anchor_record.get("mapped_control_ids")
                        or anchor_record.get("mapped_controls")
                        or anchor_record.get("control_ids")
                    )
                    anchor_mapped_policy_ids = _split_ids(
                        anchor_record.get("mapped_policy_ids")
                        or anchor_record.get("mapped_policies")
                        or anchor_record.get("policy_ids")
                    )

            anchor_only_control_ids = sorted(set([c for c in anchor_mapped_control_ids if _norm_token(c)]))

            # ======================================================================
            # Broad referenced control ids from LR/REQ + anchor controls
            # ======================================================================
            referenced_control_ids: List[str] = []
            referenced_control_ids.extend(anchor_only_control_ids)

            for rec in (lr_records_in_scope or []):
                if isinstance(rec, dict):
                    referenced_control_ids.extend(
                        _split_ids(rec.get("mapped_control_ids") or rec.get("mapped_controls") or rec.get("control_ids"))
                    )
            for rec in (req_records_in_scope or []):
                if isinstance(rec, dict):
                    referenced_control_ids.extend(
                        _split_ids(rec.get("mapped_control_ids") or rec.get("mapped_controls") or rec.get("control_ids"))
                    )

            referenced_control_ids = sorted(set([c for c in referenced_control_ids if _norm_token(c)]))

            # ======================================================================
            # Resolve CRT-C controls (broad + tight) — include full descriptors
            # ======================================================================
            crt_c_context: Dict[str, Any] = {
                "referenced_control_ids_count": len(referenced_control_ids),
                "id_column": "",
                "controls": [],
            }
            crt_c_anchor_context: Dict[str, Any] = {
                "anchor_control_ids_count": len(anchor_only_control_ids),
                "anchor_control_ids": anchor_only_control_ids,
                "id_column": "",
                "controls": [],
            }

            try:
                crt_c_payload, _, _ = _load_or_regen_catalogue_json("CRT-C")
                if isinstance(crt_c_payload, dict):
                    records = _normalise_records(crt_c_payload.get("records", []))
                    if records:
                        for id_col in ["control_id", "crt_c_id", "id"]:
                            if id_col in records[0]:
                                if referenced_control_ids:
                                    want = set(referenced_control_ids)
                                    crt_c_context["controls"] = [r for r in records if _norm_token(r.get(id_col)) in want]
                                    crt_c_context["id_column"] = id_col

                                if anchor_only_control_ids:
                                    want_a = set(anchor_only_control_ids)
                                    crt_c_anchor_context["controls"] = [r for r in records if _norm_token(r.get(id_col)) in want_a]
                                    crt_c_anchor_context["id_column"] = id_col
                                break
            except Exception:  # pylint: disable=broad-except
                pass

            # ======================================================================
            # LOCKED REQUIREMENT:
            # crt_f_in_scope_records and crt_n_in_scope_records MUST include full record bodies
            # (same “descriptor complete” behaviour as crt_c_anchor_controls).
            #
            # Correct mapping:
            # - CRT-C controls → mapped_failure_ids        → CRT-F rows
            # - CRT-C controls → mapped_compensation_ids   → CRT-N rows
            #
            # NOTE (production, not “sample”):
            # "focused/tight" means "derived from the resolved control set (anchor if present)",
            # not a sampling strategy.
            # ======================================================================

            # Focus order: tight anchor controls if present, else broad referenced controls
            focus_control_ids = anchor_only_control_ids if anchor_only_control_ids else referenced_control_ids

            focus_controls_resolved: List[Dict[str, Any]] = []
            if isinstance(crt_c_anchor_context.get("controls"), list) and crt_c_anchor_context.get("controls"):
                focus_controls_resolved = [r for r in crt_c_anchor_context.get("controls") if isinstance(r, dict)]
            elif isinstance(crt_c_context.get("controls"), list) and crt_c_context.get("controls"):
                focus_controls_resolved = [r for r in crt_c_context.get("controls") if isinstance(r, dict)]

            broad_controls_resolved: List[Dict[str, Any]] = (
                [r for r in crt_c_context.get("controls") if isinstance(r, dict)]
                if isinstance(crt_c_context.get("controls"), list)
                else []
            )

            # IDs derived from CRT-C control rows
            focus_failure_ids = _extract_mapped_ids_from_controls(
                focus_controls_resolved,
                field_candidates=["mapped_failure_ids", "failure_ids", "mapped_failures", "failures"],
            )
            focus_compensation_ids = _extract_mapped_ids_from_controls(
                focus_controls_resolved,
                field_candidates=["mapped_compensation_ids", "compensation_ids", "mapped_compensations", "compensations"],
            )

            broad_failure_ids = _extract_mapped_ids_from_controls(
                broad_controls_resolved,
                field_candidates=["mapped_failure_ids", "failure_ids", "mapped_failures", "failures"],
            )
            broad_compensation_ids = _extract_mapped_ids_from_controls(
                broad_controls_resolved,
                field_candidates=["mapped_compensation_ids", "compensation_ids", "mapped_compensations", "compensations"],
            )

            # Attach rows deterministically from CRT-F / CRT-N
            crt_f_payload2, crt_f_json_path, crt_f_regen = _load_or_regen_catalogue_json("CRT-F")
            crt_n_payload2, crt_n_json_path, crt_n_regen = _load_or_regen_catalogue_json("CRT-N")

            # CRT-F: typical id column = failure_id (FM-xxx)
            crt_f_id_col, crt_f_records_focused, crt_f_missing_focused = _select_rows_by_ids(
                crt_f_payload2,
                id_candidates=["failure_id", "fm_id", "crt_f_id", "id"],
                wanted_ids=focus_failure_ids,
            )
            _crt_f_id_col2, crt_f_records_broad, crt_f_missing_broad = _select_rows_by_ids(
                crt_f_payload2,
                id_candidates=["failure_id", "fm_id", "crt_f_id", "id"],
                wanted_ids=broad_failure_ids,
            )

            # CRT-N: YOUR SHAPE uses n_id (CRT-N-xxxx). Keep alternates for legacy compatibility.
            crt_n_id_col, crt_n_records_focused, crt_n_missing_focused = _select_rows_by_ids(
                crt_n_payload2,
                id_candidates=["n_id", "compensation_id", "cn_id", "crt_n_id", "id"],
                wanted_ids=focus_compensation_ids,
            )
            _crt_n_id_col2, crt_n_records_broad, crt_n_missing_broad = _select_rows_by_ids(
                crt_n_payload2,
                id_candidates=["n_id", "compensation_id", "cn_id", "crt_n_id", "id"],
                wanted_ids=broad_compensation_ids,
            )

            crt_f_in_scope_records: Dict[str, Any] = {
                "description": (
                    "CRT-F in-scope records are derived from the resolved CRT-C control set. "
                    "We extract mapped_failure_ids from CRT-C controls, then attach the full CRT-F rows for those failures."
                ),
                "focus_control_ids_count": len(focus_control_ids),
                "focus_control_ids": focus_control_ids,
                "focus_failure_ids_count": len(focus_failure_ids),
                "focus_failure_ids": focus_failure_ids,
                "id_column": crt_f_id_col,
                "records_tight_or_focused_count": len(crt_f_records_focused),
                "records_tight_or_focused": crt_f_records_focused,
                "records_broad_count": len(crt_f_records_broad),
                "records_broad": crt_f_records_broad,
                "missing_focus_failure_ids": crt_f_missing_focused,
                "missing_broad_failure_ids": crt_f_missing_broad,
                "json_path": crt_f_json_path,
                "regenerated": bool(crt_f_regen),
            }

            crt_n_in_scope_records: Dict[str, Any] = {
                "description": (
                    "CRT-N in-scope records are derived from the resolved CRT-C control set. "
                    "We extract mapped_compensation_ids from CRT-C controls, then attach the full CRT-N rows for those compensations."
                ),
                "focus_control_ids_count": len(focus_control_ids),
                "focus_control_ids": focus_control_ids,
                "focus_compensation_ids_count": len(focus_compensation_ids),
                "focus_compensation_ids": focus_compensation_ids,
                "id_column": crt_n_id_col,
                "records_tight_or_focused_count": len(crt_n_records_focused),
                "records_tight_or_focused": crt_n_records_focused,
                "records_broad_count": len(crt_n_records_broad),
                "records_broad": crt_n_records_broad,
                "missing_focus_compensation_ids": crt_n_missing_focused,
                "missing_broad_compensation_ids": crt_n_missing_broad,
                "json_path": crt_n_json_path,
                "regenerated": bool(crt_n_regen),
            }


            # ======================================================================
            # Attachments payload (REQ/LR are subset-attached; CRT-C/F/N are descriptor complete)
            # ======================================================================
            attachments: Dict[str, Any] = {
                "crt_req": {
                    "catalogue_meta": _catalogue_meta_info(req_payload),
                    "json_path": req_json_path,
                    "regenerated": bool(req_regen),
                    "records_in_scope": req_records_in_scope,
                    "scope_note": "AI should reason primarily from records_in_scope. catalogue_meta is informational only.",
                },
                "crt_lr": {
                    "catalogue_meta": _catalogue_meta_info(lr_payload),
                    "json_path": lr_json_path,
                    "regenerated": bool(lr_regen),
                    "records_in_scope": lr_records_in_scope,
                    "scope_note": "AI should reason primarily from records_in_scope. catalogue_meta is informational only.",
                },
                "crt_backbone": {
                    "catalogues": backbone,
                    "crt_c_referenced_controls": crt_c_context,
                    "crt_c_anchor_controls": crt_c_anchor_context,
                    "crt_f_in_scope_records": crt_f_in_scope_records,
                    "crt_n_in_scope_records": crt_n_in_scope_records,
                    "regenerated": sorted(set(backbone_regen)),
                    "note": (
                        "Backbone catalogues are provided as orientation. "
                        "AI-reasoning should rely on the resolved in-scope subsets above "
                        "(CRT-C controls + CRT-F/CRT-N derived subsets)."
                    ),
                },
                "default_lens_context": default_lens_context,
                "artefact_anchor_record": {
                    "catalogue": anchor_catalogue_name or "",
                    "id_field": anchor_id_field or "",
                    "json_path": anchor_catalogue_json_path,
                    "regenerated": bool(anchor_catalogue_regen),
                    "record": anchor_record,
                    "mapped_control_ids": anchor_only_control_ids,
                    "mapped_policy_ids": sorted(set([p for p in anchor_mapped_policy_ids if _norm_token(p)])),
                    "note": (
                        "If present, this anchor record is the tight definition of the artefact’s intended control scope "
                        "(mapped_control_ids)."
                    ),
                },
            }

            # ----------------------------
            # Under-the-hood dedupe (UI unchanged)
            # ----------------------------
            def _deepcopy_json_safe(obj: Any) -> Any:
                return json.loads(json.dumps(obj, ensure_ascii=False))

            def _slim_manifest_for_verified(m: Dict[str, Any]) -> Dict[str, Any]:
                out: Dict[str, Any] = _deepcopy_json_safe(m) if isinstance(m, dict) else {}
                for k in ["bundle_id", "programme_mode", "task_type", "artefact_anchor"]:
                    out.pop(k, None)
                tpl = out.get("template") if isinstance(out.get("template"), dict) else None
                if isinstance(tpl, dict):
                    tpl.pop("template_id", None)
                    tpl.pop("template_source", None)
                    out["template"] = tpl
                return out

            def _slim_bundle_for_verified(b: Dict[str, Any]) -> Dict[str, Any]:
                out: Dict[str, Any] = _deepcopy_json_safe(b) if isinstance(b, dict) else {}
                for k in [
                    "programme_mode",
                    "task_type",
                    "artefact_anchor",
                    "org_profile",
                    "org_governance_scope",
                    "context_notes",
                    "template",
                    "guardrails",
                ]:
                    out.pop(k, None)

                meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
                if isinstance(meta, dict) and meta:
                    out["meta"] = {
                        "built_at_utc": meta.get("built_at_utc"),
                        "source": meta.get("source"),
                    }
                else:
                    out.pop("meta", None)
                return out

            manifest_for_verified: Dict[str, Any] = _slim_manifest_for_verified(current_manifest) if isinstance(current_manifest, dict) else {}
            bundle_for_verified: Dict[str, Any] = _slim_bundle_for_verified(current_bundle) if isinstance(current_bundle, dict) else {}

            # ----------------------------
            # Mapping guidance (explicit for external AI)
            # ----------------------------
            mapping_guidance: Dict[str, Any] = {
                "crt_spine_principle": "CRT-C is the primary spine. All other catalogues are interpreted through CRT-C mappings.",
                "primary_focus_order": [
                    "1) artefact_anchor_record.record (if present) and artefact_anchor_record.mapped_control_ids",
                    "2) crt_backbone.crt_c_anchor_controls (tight set) OR crt_backbone.crt_c_referenced_controls (broad set)",
                    "3) crt_backbone.crt_f_in_scope_records (derived from CRT-C mapped_failure_ids; full CRT-F rows attached)",
                    "4) crt_backbone.crt_n_in_scope_records (derived from CRT-C mapped_compensation_ids; full CRT-N rows attached)",
                    "5) crt_req.records_in_scope and crt_lr.records_in_scope (explicit emphasis sets)",
                    "6) structural lens bundles in verified.bundle.structural_lenses (additional emphasis, not exclusion)",
                    "7) default_lens_context (baseline universe / orientation only)",
                ],
                "how_to_use_emphasis": (
                    "Emphasis means 'start here and go deeper'. It does NOT mean other context is false or excluded. "
                    "Where an anchor-mapped control set exists (STD/POL), it is treated as the tight authoritative scope."
                ),
                "note_on_local_paths": (
                    "json_path fields are traceability references to the local workspace. External AI cannot open them. "
                    "Reason only from embedded records/subsets included in this verified artefact."
                ),
            }

            verified_payload: Dict[str, Any] = {
                "verified_version": "1.0",
                "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "bundle_id": bundle_id,
                "identity": {
                    "anchor_id": anchor_id,
                    "anchor_name": anchor_name,
                    "programme_mode": programme_mode,
                    "task_type": task_type,
                    "template_id": template_id,
                    "template_source": template_source,
                },
                "resolved_semantics": {
                    "frameworks_mode": _frameworks_mode_semantics(frameworks_mode_key),
                    "default_lens_context": _default_lens_semantics(baseline_default_lens_context),
                    "notes": "Semantics are resolved for downstream interpretation. Do not re-infer from keys.",
                },
                "in_scope": {
                    "frameworks_in_scope": frameworks_in_scope,
                    "obligations_ids_in_scope": obligations_ids_in_scope,
                    "lens_keys": lens_keys,
                },
                "mapping_guidance": mapping_guidance,
                "attachments": attachments,
                "emphasis": emphasis,
                "manifest": manifest_for_verified,
                "bundle": bundle_for_verified,
            }

            anchor_hint = anchor_id or anchor_name or ""
            verified_path = _verified_path_for_bundle_id(bundle_id, anchor_hint=anchor_hint, task_type=task_type)
            _save_json(verified_path, verified_payload)

            st.success(f"✅ Verified artefact created: `{os.path.relpath(verified_path, PROJECT_ROOT)}`")
            st.rerun()

        except Exception as e:  # pylint: disable=broad-except
            vp = (verified_path if "verified_path" in locals() else _latest_verified_path_for_bundle_id(bundle_id) or "")
            st.error(f"Unable to create verified artefact (write error).\n\nPath: `{vp}`\nError: {e}")



# -------------------------------------------------------------------------------------------------
# 📦 Package & Restore — save / download / restore current artefact (manifest + bundle)
# -------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------
# Small helpers (used by Verify / Package tabs)
# -------------------------------------------------------------------------------------------------
def _get_nested(obj: Any, path: List[str], default: Any = None) -> Any:
    """Safely read nested dict paths.

    Example: _get_nested(bundle, ["artefact_anchor","anchor_id"], "")
    """
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def _compact_list(value: Any) -> List[str]:
    """Normalise unknown list-like fields into a clean list[str]."""
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        if item is None:
            continue
        s = str(item).strip()
        if s:
            out.append(s)
    return out


# -------------------------------------------------------------------------------------------------
# 🧠 AI Prompt & Response — export-only (no API, no personas, JSON-in → SYSTEM/USER out)
#   Template selection is implicit (derived from task_type → filename suffix)
# -------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------
# 🧠 AI Prompt & Response — export-only (no API, no personas, JSON-in → SYSTEM/USER out)
#   - Source of truth for AI interpretation is the VERIFIED artefact (immutable input)
#   - Saved AI handoffs are stored under /ai_exports (separate from prompt templates)
#   - Prompt template selection is implicit (derived from programme_mode and task_type)
# -------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------
# Helpers (file IO)
# -------------------------------------------------------------------------------------------------
def _list_json_files(folder: str) -> List[str]:
    try:
        if not os.path.isdir(folder):
            return []
        files = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        return sorted(files, reverse=True)
    except Exception:  # pylint: disable=broad-except
        return []


def _load_json_from_path(path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception:  # pylint: disable=broad-except
        return None


def _extract_task_type(payload: Dict[str, Any]) -> str:
    for path in [
        ["bundle", "task_type"],
        ["manifest", "task_type"],
        ["task_type"],
        ["artefact", "bundle", "task_type"],
        ["artefact", "manifest", "task_type"],
    ]:
        v = _get_nested(payload, path, "")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _extract_programme_mode(payload: Dict[str, Any]) -> str:
    for path in [
        ["bundle", "programme_mode"],
        ["manifest", "programme_mode"],
        ["programme_mode"],
        ["artefact", "bundle", "programme_mode"],
        ["artefact", "manifest", "programme_mode"],
    ]:
        v = _get_nested(payload, path, "")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _extract_template_sections(payload: Dict[str, Any]) -> List[str]:
    candidates = [
        ["bundle", "template", "sections"],
        ["artefact", "bundle", "template", "sections"],
        ["manifest", "template", "sections"],
        ["artefact", "manifest", "template", "sections"],
    ]
    for path in candidates:
        v = _get_nested(payload, path, None)
        if isinstance(v, list):
            out: List[str] = []
            for s in v:
                ss = str(s).strip()
                if ss:
                    out.append(ss)
            if out:
                return out
    return []


def _task_family_delta(task_type: str, programme_mode: str) -> str:
    """
    NOTE:
    This delta is for the AI message envelope (SYSTEM/USER),
    not for upstream build/verify behaviour.
    """
    t = (task_type or "").strip().lower()
    p = (programme_mode or "").strip()

    if "Security Architecture" in p:
        return (
            "This task produces a structural architecture view.\n"
            "Focus on components, boundaries, relationships, and coverage using the provided structural findings.\n"
            "Do not prescribe design choices, implementation steps, or controls beyond what is already mapped."
        )

    if "Resilience Metrics" in p:
        return (
            "This task produces a metrics or coverage artefact.\n"
            "Focus on what is measured, how it is grouped, and what it represents structurally.\n"
            "Avoid targets, thresholds, performance judgement, or optimisation guidance."
        )

    if "Incident Simulation" in p:
        return (
            "This task produces a scenario or simulation narrative.\n"
            "Focus on structural pathways, dependencies, and uncertainty.\n"
            "Do not recommend actions, response steps, or playbooks."
        )

    # Governance family (default)
    if any(x in t for x in ["policy", "standard", "questionnaire", "audit", "checklist", "risk", "vendor", "exception", "awareness", "training"]):
        return (
            "This task produces a governance artefact.\n"
            "Focus on clarity of intent, scope boundaries, roles, and traceability.\n"
            "Describe what is governed, by whom, and under which constraints — not how to implement it."
        )

    return (
        "This task produces a governance artefact.\n"
        "Focus on clarity of intent, scope boundaries, roles, and traceability.\n"
        "Describe what is governed, by whom, and under which constraints — not how to implement it."
    )


def _load_prompt_templates(path: str) -> List[Dict[str, Any]]:
    """
    Expected schema:
    {
      "version": "...",
      "updated_at": "...",            # optional
      "templates": [
        {
          "template_id": "...",
          "label": "Governance (default delta)",
          "description": "...",       # optional
          "applies_to": ["..."],       # optional
          "system_append": "...",      # optional
          "user_append": "..."         # optional
        }
      ]
    }

    Back-compat: if 'prompt' exists, treat as user_append.
    """
    payload = _load_json_from_path(path)
    if not isinstance(payload, dict):
        return []

    raw = payload.get("templates")
    if not isinstance(raw, list):
        return []

    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        label = str(item.get("label") or "").strip()
        if not label:
            continue

        if "user_append" not in item and isinstance(item.get("prompt"), str):
            item = dict(item)
            item["user_append"] = str(item.get("prompt") or "").strip()

        out.append(item)

    return out


def _choose_template_suffix(task_type: str, programme_mode: str) -> str:
    """Choose the prompt template family file (governance/architecture/metrics/simulation)."""
    p = (programme_mode or "").strip().lower()
    t = (task_type or "").strip().lower()

    if "security architecture" in p or any(x in t for x in ["architecture", "data-flow", "trust-boundary", "zoning"]):
        return "architecture"
    if "resilience metrics" in p or any(x in t for x in ["metrics", "coverage / gap", "coverage", "gap overview"]):
        return "metrics"
    if "incident simulation" in p or any(x in t for x in ["playbook", "scenario", "what if", "simulation"]):
        return "simulation"

    # Default
    return "governance"


def _resolve_prompt_template_file(task_type: str, programme_mode: str) -> Tuple[str, str]:
    """
    Returns: (template_path, suffix)

    Template files live in /ai_exports:
      - crt_ai_prompt_templates.governance.json
      - crt_ai_prompt_templates.architecture.json
      - crt_ai_prompt_templates.metrics.json
      - crt_ai_prompt_templates.simulation.json

    Fallback: governance.
    """
    suffix = _choose_template_suffix(task_type=task_type, programme_mode=programme_mode)
    chosen = os.path.join(WORKSPACE_AI_EXPORTS_DIR, f"crt_ai_prompt_templates.{suffix}.json")

    if os.path.isfile(chosen):
        return chosen, suffix

    fallback = os.path.join(WORKSPACE_AI_EXPORTS_DIR, "crt_ai_prompt_templates.governance.json")
    return fallback, "governance"


def _pick_single_template(templates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """No dropdown. Deterministic selection (prefer 'default', else first)."""
    if not templates:
        return {}
    for t in templates:
        label = str(t.get("label") or "").strip().lower()
        if "default" in label:
            return t
    return templates[0]


# -------------------------------------------------------------------------------------------------
# Locked message builders
# -------------------------------------------------------------------------------------------------
def build_system_message_locked() -> str:
    return (
        "You are an AI operating in a decision-support and governance analysis context.\n\n"
        "Your role is to interpret structured governance artefacts neutrally and descriptively.\n\n"
        "Behaviour\n\n"
        "Neutral, non-advisory, non-prescriptive\n"
        "Structural and observational only\n"
        "Explicit about uncertainty and missing context\n\n"
        "Constraints\n\n"
        "Do not provide advice, recommendations, configuration steps, or assurance statements\n"
        "Do not introduce controls, obligations, frameworks, or scope not present in the provided bundle\n"
        "Do not assume implementation maturity or effectiveness\n\n"
        "Output Rules\n\n"
        "Follow the provided template sections exactly and in order\n"
        "Use plain, structured text suitable for Word or Google Docs\n"
        "Bold section headings only\n"
        "Do not add or remove sections\n"
        "Do not include a conclusion unless the template explicitly contains one\n"
        "If information is missing, unclear, or out of scope, state this explicitly rather than inferring.\n\n"
        "This output is for governance documentation support only."
    )


def build_user_message_locked(
    payload_json: Dict[str, Any],
    task_type: str,
    programme_mode: str,
    template_sections: List[str],
    prompt_user_append: str,
    manual_instructions: str,
) -> str:
    delta = _task_family_delta(task_type=task_type, programme_mode=programme_mode)

    sections_block = ""
    if template_sections:
        sections_lines = "\n".join([f"- {s}" for s in template_sections])
        sections_block = "\n\nTemplate Sections (must be followed exactly)\n\n" + sections_lines

    user_append = (prompt_user_append or "").strip()
    if user_append:
        user_append = "\n\nAdditional Task Instructions (from template)\n\n" + user_append

    manual = (manual_instructions or "").strip()
    if manual:
        manual = "\n\nManual Customisation (optional)\n\n" + manual

    return (
        "Analyse the following AI export bundle.\n\n"
        "The bundle contains:\n\n"
        "Governance context and organisational scope\n"
        "Structural findings from multiple analytical lenses\n"
        "Explicit guardrails and exclusions\n"
        "A predefined output template defining section structure\n\n"
        "Task Context\n"
        f"This task produces an artefact: a {task_type or 'Governance artefact'}.\n\n"
        "Focus on:\n\n"
        "Clarity of intent and scope\n"
        "Governance roles and accountability\n"
        "Structural traceability to organisational context and mapped findings\n\n"
        "Do not:\n\n"
        "Provide implementation guidance\n"
        "Provide configuration steps\n"
        "Provide assurance or compliance claims\n\n"
        "Return plain, structured text suitable for Word or Google Docs.\n"
        "Use the template sections exactly as provided and in the same order.\n\n"
        "Output Format (Locked)\n\n"
        "Plain text suitable for direct use in Word or Google Docs\n"
        "Bold section headings only\n"
        "One blank line before and after each section heading\n"
        "No markdown headers, dividers, or decorative formatting\n"
        "No advice, recommendations, implementation steps, or assurance statements\n"
        f"\n\nTask-Type Instruction Delta (Locked)\n\n{delta}"
        f"{sections_block}"
        f"{user_append}"
        f"{manual}"
        "\n\n[AI EXPORT BUNDLE JSON]\n\n"
        "```json\n"
        + json.dumps(payload_json, indent=2, ensure_ascii=False)
        + "\n```"
    )


# -------------------------------------------------------------------------------------------------
# 🧠 AI Prompt & Response (UI)
# -------------------------------------------------------------------------------------------------
def render_ai_prompt_response_tab() -> None:
    st.markdown("## 🧠 AI Prompt & Response")
    st.caption(
        "Attach prompt context and save an AI-ready handoff. "
        "Uses the verified artefact as immutable input."
    )

    _ensure_dir(WORKSPACE_AI_EXPORTS_DIR)
    _ensure_dir(WORKSPACE_VERIFIED_DIR)

    st.divider()

    # -----------------------------------------
    # 1) Source bundle
    # -----------------------------------------
    st.markdown("### 1) Source bundle")
    st.caption("Choose **Verified** wherever possible. Saved AI handoffs are separate exports.")

    payload: Optional[Dict[str, Any]] = None
    payload_path: Optional[str] = None

    source_mode = st.radio(
        "Select source",
        options=["Verified (recommended)", "Current (session)", "Saved AI handoffs"],
        horizontal=False,
    )

    if source_mode == "Current (session)":
        cm = st.session_state.get(CURRENT_PROGRAMME_MANIFEST_KEY)
        cb = st.session_state.get(CURRENT_PROGRAMME_BUNDLE_KEY)
        if isinstance(cm, dict) and isinstance(cb, dict):
            payload = {
                "source": "session_current",
                "created_at_utc": _now_utc_iso(),
                "manifest": cm,
                "bundle": cb,
            }
        else:
            st.info("No current artefact in session. Build one in 🎛 Task Builder.")
    elif source_mode == "Saved AI handoffs":
        files = [f for f in _list_json_files(WORKSPACE_AI_EXPORTS_DIR) if not f.startswith("crt_ai_prompt_templates.")]
        if not files:
            st.info("No saved AI handoffs found yet.")
        else:
            chosen = st.selectbox("Choose saved AI handoff", options=files, index=0)
            payload_path = os.path.join(WORKSPACE_AI_EXPORTS_DIR, chosen)
            payload = _load_json_from_path(payload_path)
    else:
        # Verified (recommended)
        vfiles = _list_json_files(WORKSPACE_VERIFIED_DIR)
        if not vfiles:
            st.info("No verified artefacts found yet. Create one in 🔍 Verify first.")
        else:
            chosen = st.selectbox("Choose verified artefact", options=vfiles, index=0)
            payload_path = os.path.join(WORKSPACE_VERIFIED_DIR, chosen)
            payload = _load_json_from_path(payload_path)

    st.divider()

    # -----------------------------------------
    # ✏️ Manual Customisation (Optional)
    # -----------------------------------------
    st.markdown("### ✏️ Notes (optional)")
    st.caption("These notes are appended into the USER message (they do not change the verified input).")

    manual_instructions = st.text_area(
        "Notes",
        value=str(st.session_state.get(CRT_AI_MANUAL_INSTRUCTIONS_KEY, "") or ""),
        height=140,
        placeholder="Example: keep tone formal; preserve internal terminology; emphasise scope boundaries; ...",
    )
    st.session_state[CRT_AI_MANUAL_INSTRUCTIONS_KEY] = manual_instructions

    clear_col, _ = st.columns([1, 3])
    with clear_col:
        if st.button("🧽 Clear notes", use_container_width=True):
            st.session_state[CRT_AI_MANUAL_INSTRUCTIONS_KEY] = ""
            st.rerun()

    st.divider()

    # -----------------------------------------
    # 3) Messages
    # -----------------------------------------
    st.markdown("### 3) Messages")
    st.caption(
        "Copy SYSTEM + USER into your AI tool. "
        "If the USER message is too large to paste, use the AI handoff (JSON) below."
    )

    if not isinstance(payload, dict):
        st.info("Select a source to generate messages.")
        return

    # Detect context (internal) + apply template delta silently
    task_type = _extract_task_type(payload) or "Governance artefact"
    programme_mode = _extract_programme_mode(payload) or "🧭 Governance"
    template_sections = _extract_template_sections(payload)

    # Resolve template family file (no dropdown UI)
    template_path, _template_suffix = _resolve_prompt_template_file(task_type=task_type, programme_mode=programme_mode)
    templates = _load_prompt_templates(template_path)
    chosen_tpl: Dict[str, Any] = _pick_single_template(templates) if templates else {}

    # Build messages (heavy strings)
    system_msg = build_system_message_locked()
    system_append_final = str(chosen_tpl.get("system_append") or "").strip()
    if system_append_final:
        system_msg = system_msg + "\n\n" + system_append_final

    user_msg = build_user_message_locked(
        payload_json=payload,
        task_type=task_type,
        programme_mode=programme_mode,
        template_sections=template_sections,
        prompt_user_append=str(chosen_tpl.get("user_append") or "").strip(),
        manual_instructions=manual_instructions,
    )

    with st.expander("🧩 SYSTEM (copy from here)", expanded=False):
        st.code(system_msg, language="text")

    with st.expander("👤 USER (copy from here)", expanded=False):
        st.code(user_msg, language="text")

    with st.expander("What’s included", expanded=False):
        st.markdown(
            "- SYSTEM: locked behaviour + constraints\n"
            "- USER: task context + locked output rules + your notes + verified JSON"
        )

    st.divider()

    # -----------------------------------------
    # AI handoff (JSON)
    # -----------------------------------------
    st.markdown("### AI handoff (JSON)")
    st.caption("Download to upload into your AI tool, or save to reuse later.")

    safe_task = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in (task_type or "governance").strip().lower()])
    safe_task = safe_task.strip("_") or "governance"
    default_name = f"crt_ai_handoff_{safe_task}_{uuid.uuid4().hex[:10]}.json"
    file_name = st.text_input("File name", value=default_name)

    handoff_payload = {
        "version": "0.1",
        "export_type": "crt_ai_prompt_handoff",
        "created_at_utc": _now_utc_iso(),
        "task_context": {
            "programme_mode": programme_mode,
            "task_type": task_type,
            "template_sections": template_sections,
        },
        "manual_customisation": (manual_instructions or "").strip() or None,
        "messages": {
            "system": system_msg,
            "user": user_msg,
        },
        "verified_json": payload,
    }

    pretty = json.dumps(handoff_payload, indent=2, ensure_ascii=False)

    a, b = st.columns([1, 1])

    with a:
        st.download_button(
            "⬇️ Download AI handoff (JSON)",
            data=pretty.encode("utf-8"),
            file_name=(file_name.strip() if isinstance(file_name, str) and file_name.strip() else default_name),
            mime="application/json",
            use_container_width=True,
        )

    with b:
        if st.button("💾 Save AI handoff", use_container_width=True):
            safe = (file_name or "").strip() or default_name
            if not safe.lower().endswith(".json"):
                safe = safe + ".json"

            target = os.path.join(WORKSPACE_AI_EXPORTS_DIR, safe)
            ok = _safe_write_json(target, handoff_payload)

            if ok:
                st.success("AI handoff saved.")
            else:
                st.error("Unable to save AI handoff.")

# -------------------------------------------------------------------------------------------------
# Maintenance —  file management + session hygiene
# -------------------------------------------------------------------------------------------------

def render_maintenance_tab() -> None:
    """
    🧹 Maintenance

    Platinum intent:
    - Keep workspaces tidy and transparent
    - Provide safe file management for the working layer
    - Align wording to the actual build flow

    Flow:
    1) Org Governance Profiles
    2) Governance Setup catalogues (CRT-REQ / CRT-LR)
    3) Operational Extensions catalogues (CRT-AS / CRT-D / CRT-I / CRT-SC / CRT-T)
    4) Structural lens bundles (crt_workspace/lenses/**/bundles)
    5) Programme artefacts (manifests / bundles / verified / AI handoffs)
    6) User output templates (delete ONE template + backup)
    """
    st.markdown("## 🧹 Maintenance")
    st.caption("Housekeeping and storage management.")

    # ----------------------------
    # Helpers (local to Maintenance)
    # ----------------------------
    def _safe_list_files(folder: str, extensions: Optional[Tuple[str, ...]] = None) -> List[str]:
        try:
            if not os.path.isdir(folder):
                return []
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            if extensions:
                files = [f for f in files if f.lower().endswith(extensions)]
            return sorted(files, reverse=True)
        except Exception:  # pylint: disable=broad-except
            return []

    def _safe_read_json(path: str) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.isfile(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except Exception:  # pylint: disable=broad-except
            return None

    def _safe_write_json(path: str, payload: Dict[str, Any]) -> bool:
        try:
            _ensure_dir(os.path.dirname(path))
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    def _safe_read_text(path: str, max_chars: int = 8000) -> str:
        try:
            if not os.path.isfile(path):
                return ""
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_chars)
        except Exception:  # pylint: disable=broad-except
            return ""

    def _pretty(obj: Any) -> str:
        try:
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except Exception:  # pylint: disable=broad-except
            return json.dumps({"error": "Unable to render JSON"}, indent=2, ensure_ascii=False)

    def _count_files(folder: str, extensions: Optional[Tuple[str, ...]] = None) -> int:
        return len(_safe_list_files(folder, extensions=extensions))

    def _filename_hint(name: str) -> str:
        if name.endswith(" "):
            return f"{name.rstrip()}␠"
        return name

    def _load_user_output_templates() -> Dict[str, Any]:
        payload = _safe_read_json(USER_TEMPLATES_JSON)
        if not isinstance(payload, dict):
            return {"version": "0.1", "templates": []}
        if not isinstance(payload.get("templates"), list):
            payload["templates"] = []
        if "version" not in payload:
            payload["version"] = "0.1"
        return payload

    def _template_label(tpl: Dict[str, Any]) -> str:
        for k in ["label", "title", "name"]:
            v = tpl.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        v2 = tpl.get("template_id")
        if isinstance(v2, str) and v2.strip():
            return v2.strip()
        return "Unnamed template"

    def _template_id(tpl: Dict[str, Any]) -> str:
        v = tpl.get("template_id")
        if isinstance(v, str) and v.strip():
            return v.strip()
        return hashlib.sha256(_pretty(tpl).encode("utf-8")).hexdigest()[:12]

    def _copy_file(src: str, dst: str) -> bool:
        try:
            if not os.path.isfile(src):
                return False
            _ensure_dir(os.path.dirname(dst))
            with open(src, "rb") as fsrc:
                data = fsrc.read()
            with open(dst, "wb") as fdst:
                fdst.write(data)
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    def _catalogue_paths(catalogue_name: str) -> Tuple[str, str]:
        active_path = os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues", f"{catalogue_name}.csv")
        default_path = os.path.join(PROJECT_ROOT, "apps", "data_sources", "defaults", f"{catalogue_name}.csv")
        return active_path, default_path

    # ------------------------------------------------------------
    # Catalogue restore helpers (CSV → JSON view regeneration)
    # ------------------------------------------------------------
    def _backup_dir() -> str:
        return os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues", "backup")

    def _json_view_dir() -> str:
        return os.path.join(PROJECT_ROOT, "apps", "data_sources", "crt_catalogues", "json")

    def _create_timestamped_backup(active_path: str, catalogue_name: str) -> str:
        try:
            if not os.path.isfile(active_path):
                return ""
            _ensure_dir(_backup_dir())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(_backup_dir(), f"{catalogue_name}.{ts}.csv")
            return backup_path if _copy_file(active_path, backup_path) else ""
        except Exception:  # pylint: disable=broad-except
            return ""

    def _get_latest_backup(catalogue_name: str) -> str:
        try:
            bdir = _backup_dir()
            if not os.path.isdir(bdir):
                return ""
            prefix = f"{catalogue_name}."
            candidates = [
                os.path.join(bdir, f)
                for f in os.listdir(bdir)
                if f.startswith(prefix) and f.endswith(".csv")
            ]
            candidates.sort()
            return candidates[-1] if candidates else ""
        except Exception:  # pylint: disable=broad-except
            return ""

    def _regenerate_json_view(catalogue_name: str, active_path: str) -> Tuple[bool, str]:
        json_path = os.path.join(_json_view_dir(), f"{catalogue_name}.json")
        try:
            if not os.path.isfile(active_path):
                return False, json_path

            _ensure_dir(_json_view_dir())

            raw = b""
            with open(active_path, "rb") as f:
                raw = f.read()

            text = ""
            for enc in ("utf-8", "utf-8-sig", "latin1"):
                try:
                    text = raw.decode(enc)
                    break
                except Exception:  # pylint: disable=broad-except
                    continue
            if not text:
                text = raw.decode("utf-8", errors="replace")

            reader = csv.DictReader(text.splitlines())
            records: List[Dict[str, Any]] = []
            for row in reader:
                clean = {str(k).strip(): (v if v is not None else "") for k, v in row.items()}
                records.append(clean)

            payload: Dict[str, Any] = {
                "catalogue": catalogue_name,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "source_csv": os.path.relpath(active_path, PROJECT_ROOT),
                "records": records,
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            return True, json_path
        except Exception:  # pylint: disable=broad-except
            return False, json_path

    def _render_catalogue_manager(catalogue_name: str) -> None:
        active_path, default_path = _catalogue_paths(catalogue_name)
        latest_backup = _get_latest_backup(catalogue_name)

        active_exists = os.path.isfile(active_path)
        default_exists = os.path.isfile(default_path)
        backup_exists = bool(latest_backup) and os.path.isfile(latest_backup)

        json_path = os.path.join(_json_view_dir(), f"{catalogue_name}.json")
        json_exists = os.path.isfile(json_path)

        col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])
        with col_a:
            st.metric("Active", "Present" if active_exists else "Missing")
        with col_b:
            st.metric("Latest backup", "Present" if backup_exists else "—")
        with col_c:
            st.metric("Default", "Present" if default_exists else "Missing")
        with col_d:
            st.metric("JSON view", "Present" if json_exists else "—")

        with st.expander("Preview (active)", expanded=False):
            if active_exists:
                st.code(_safe_read_text(active_path, max_chars=8000), language="text")
            else:
                st.info("Active file not found.")

        with st.expander("Preview (JSON view)", expanded=False):
            if json_exists:
                st.code(_safe_read_text(json_path, max_chars=8000), language="json")
            else:
                st.caption("No JSON view generated yet for this catalogue.")

        st.markdown("**Download**")
        d1, d2, d3 = st.columns(3)

        def _read_bytes(path: str) -> bytes:
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:  # pylint: disable=broad-except
                return b""

        with d1:
            st.download_button(
                "⬇️ Active CSV (edit this)",
                data=_read_bytes(active_path) if active_exists else b"",
                file_name=os.path.basename(active_path),
                mime="text/csv",
                use_container_width=True,
                disabled=(not active_exists),
                key=f"cat_dl_active_{catalogue_name}",
            )

        with d2:
            st.download_button(
                "⬇️ Latest backup (restore only)",
                data=_read_bytes(latest_backup) if backup_exists else b"",
                file_name=os.path.basename(latest_backup) if backup_exists else f"{catalogue_name}.backup.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=(not backup_exists),
                key=f"cat_dl_backup_{catalogue_name}",
            )

        with d3:
            st.download_button(
                "⬇️ Shipped default (restore only)",
                data=_read_bytes(default_path) if default_exists else b"",
                file_name=f"{catalogue_name}.default.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=(not default_exists),
                key=f"cat_dl_default_{catalogue_name}",
            )

        st.divider()

        st.markdown("**Restore**")
        st.caption("Restores a source CSV into the active catalogue and regenerates the JSON view immediately.")

        r1, r2 = st.columns(2)

        with r1:
            st.markdown("**From latest backup**")
            st.caption("Uses the most recent timestamped backup. Creates a new backup of the current active first.")
            if st.button(
                "♻️ Restore latest backup",
                use_container_width=True,
                disabled=(not backup_exists),
                key=f"cat_restore_backup_{catalogue_name}",
            ):
                prior_backup = _create_timestamped_backup(active_path, catalogue_name)

                if _copy_file(latest_backup, active_path):
                    ok_json, jp = _regenerate_json_view(catalogue_name, active_path)
                    st.success("✅ Latest backup restored to active.")
                    if prior_backup:
                        st.caption(f"Previous active backed up: `{os.path.relpath(prior_backup, PROJECT_ROOT)}`")
                    if ok_json:
                        st.caption(f"JSON regenerated: `{os.path.relpath(jp, PROJECT_ROOT)}`")
                    else:
                        st.warning(f"Active restored, but JSON regeneration failed: `{os.path.relpath(jp, PROJECT_ROOT)}`")
                    st.rerun()
                else:
                    st.error("Unable to restore from latest backup (copy error).")

        with r2:
            st.markdown("**From shipped default**")
            st.caption("Restores the shipped baseline from `/apps/data_sources/defaults/`. No backup is created here.")
            if st.button(
                "♻️ Restore shipped default",
                use_container_width=True,
                disabled=(not default_exists),
                key=f"cat_restore_default_{catalogue_name}",
            ):
                if _copy_file(default_path, active_path):
                    ok_json, jp = _regenerate_json_view(catalogue_name, active_path)
                    st.success("✅ Shipped default restored to active.")
                    if ok_json:
                        st.caption(f"JSON regenerated: `{os.path.relpath(jp, PROJECT_ROOT)}`")
                    else:
                        st.warning(f"Active restored, but JSON regeneration failed: `{os.path.relpath(jp, PROJECT_ROOT)}`")
                    st.rerun()
                else:
                    st.error("Unable to restore shipped default (copy error).")

    def _lens_folder_label(code: str) -> str:
        code = (code or "").strip().lower()
        mapping = {
            "dcr": "🧮 Data Classification Registry (CRT-D)",
            "asm": "🧩 Attack Surface Mapper (CRT-AS)",
            "ial": "🔐 Identity Access Lens (CRT-I)",
            "sces": "🛰️ Supply Chain Exposure Scanner (CRT-SC)",
            "tsc": "📡 Telemetry Signal Console (CRT-T)",
        }
        return mapping.get(code, code)

    # ----------------------------
    # Workspace summary — aligned to Maintenance flow
    # ----------------------------
    def _count_profiles() -> int:
        try:
            raw = None
            if isinstance(st.session_state.get("org_profiles"), dict):
                raw = st.session_state.get("org_profiles")
            elif os.path.isfile(ORG_PROFILES_PATH):
                with open(ORG_PROFILES_PATH, "r", encoding="utf-8") as f:
                    raw = json.load(f)
            return len(raw.keys()) if isinstance(raw, dict) else 0
        except Exception:  # pylint: disable=broad-except
            return 0

    def _file_present(path: str) -> bool:
        try:
            return os.path.isfile(path)
        except Exception:  # pylint: disable=broad-except
            return False

    def _count_lens_bundles_total() -> int:
        try:
            if not os.path.isdir(LENS_SHELF_DIR):
                return 0
            total = 0
            for lens_code in os.listdir(LENS_SHELF_DIR):
                bundles_dir = os.path.join(LENS_SHELF_DIR, lens_code, "bundles")
                if os.path.isdir(bundles_dir):
                    total += len(_safe_list_files(bundles_dir, extensions=(".json",)))
            return total
        except Exception:  # pylint: disable=broad-except
            return 0

    def _governance_catalogues_status() -> str:
        try:
            active_req, _ = _catalogue_paths("CRT-REQ")
            active_lr, _ = _catalogue_paths("CRT-LR")
            present = int(_file_present(active_req)) + int(_file_present(active_lr))
            return f"{present}/2"
        except Exception:  # pylint: disable=broad-except
            return "—"

    def _operational_catalogues_status() -> str:
        try:
            names2 = ["CRT-AS", "CRT-D", "CRT-I", "CRT-SC", "CRT-T"]
            present = 0
            for n in names2:
                active_path, _ = _catalogue_paths(n)
                if _file_present(active_path):
                    present += 1
            return f"{present}/5"
        except Exception:  # pylint: disable=broad-except
            return "—"

    # Summary rows
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        st.metric("Org profiles", str(_count_profiles()))
    with r1c2:
        st.metric("Governance catalogues", _governance_catalogues_status())
    with r1c3:
        st.metric("Operational catalogues", _operational_catalogues_status())
    with r1c4:
        st.metric("Lens bundles", str(_count_lens_bundles_total()))

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        st.metric("Manifests", str(_count_files(WORKSPACE_MANIFESTS_DIR, extensions=(".json",))))
    with r2c2:
        st.metric("Bundles", str(_count_files(WORKSPACE_BUNDLES_DIR, extensions=(".json",))))
    with r2c3:
        st.metric("Verified artefacts", str(_count_files(WORKSPACE_VERIFIED_DIR, extensions=(".json",))))
    with r2c4:
        st.metric("AI handoffs", str(_count_files(WORKSPACE_AI_EXPORTS_DIR, extensions=(".json",))))

    st.divider()

    # =====================================================================
    # 1) Org Governance Profiles
    # =====================================================================
    st.markdown("### 1) Org Governance Profiles")
    st.caption("Delete one saved profile (non-active only).")

    profiles: Dict[str, Any] = {}
    if isinstance(st.session_state.get("org_profiles"), dict):
        profiles = st.session_state.get("org_profiles", {})
    else:
        try:
            if os.path.isfile(ORG_PROFILES_PATH):
                with open(ORG_PROFILES_PATH, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    profiles = raw
        except Exception:  # pylint: disable=broad-except
            profiles = {}

    active_name = str(st.session_state.get("active_org_profile") or "").strip()
    names = sorted([n for n in profiles.keys() if str(n).strip()])

    if not names:
        st.info("No saved profiles found.")
    else:
        if active_name and active_name in names:
            st.info(f"Active profile: **{active_name}**")

        deletable = [n for n in names if n != active_name]
        if deletable:
            selected = st.selectbox(
                "Select profile to delete",
                options=["(Select)"] + deletable,
                index=0,
                key="crt_profile_delete_select",
            )
            if selected != "(Select)":
                current = profiles.get(selected, {}) if isinstance(profiles.get(selected), dict) else {}
                with st.expander("Profile preview", expanded=False):
                    st.code(_pretty(current), language="json")

                st.markdown("**Permanent deletion**")
                st.caption("Deletes this profile from disk. This cannot be undone in-app.")

                confirm_del = st.checkbox(
                    "Confirm permanent deletion",
                    value=False,
                    key=f"crt_profile_delete_confirm_{selected}",
                )

                if st.button(
                    "🗑️ Delete profile",
                    use_container_width=True,
                    disabled=(not confirm_del),
                    key=f"crt_delete_profile_btn_{selected}",
                ):
                    try:
                        profiles.pop(selected, None)
                        _ensure_dir(os.path.dirname(ORG_PROFILES_PATH))
                        with open(ORG_PROFILES_PATH, "w", encoding="utf-8") as f:
                            json.dump(profiles, f, indent=2, ensure_ascii=False)
                        st.session_state["org_profiles"] = profiles
                        st.success("✅ Profile deleted.")
                        st.rerun()
                    except Exception:  # pylint: disable=broad-except
                        st.error("Unable to delete profile (write error).")
        else:
            st.caption("No deletable profiles (active profile cannot be deleted here).")

    st.divider()

    # =====================================================================
    # 2) Governance Setup catalogues (CRT-REQ / CRT-LR)
    # =====================================================================
    st.markdown("### 2) Governance Setup catalogues")
    st.caption("Preview, download, or restore the active catalogue files used by the system.")

    with st.expander("CRT-REQ — Requirements Catalogue", expanded=False):
        _render_catalogue_manager("CRT-REQ")

    with st.expander("CRT-LR — Legal & Regulatory Obligations", expanded=False):
        _render_catalogue_manager("CRT-LR")

    st.divider()

    # =====================================================================
    # 3) Operational Extensions catalogues (CRT-AS / CRT-D / CRT-I / CRT-SC / CRT-T)
    # =====================================================================
    st.markdown("### 3) Operational Extensions catalogues")
    st.caption("Preview, download, or restore the active catalogue files used by the system.")

    with st.expander("CRT-AS — Asset & Technology Landscape", expanded=False):
        _render_catalogue_manager("CRT-AS")

    with st.expander("CRT-D — Data & Classification Catalogue", expanded=False):
        _render_catalogue_manager("CRT-D")

    with st.expander("CRT-I — Identity Zones & Trust Anchors", expanded=False):
        _render_catalogue_manager("CRT-I")

    with st.expander("CRT-SC — Supply-Chain & Vendor Catalogue", expanded=False):
        _render_catalogue_manager("CRT-SC")

    with st.expander("CRT-T — Telemetry & Signal Sources", expanded=False):
        _render_catalogue_manager("CRT-T")

    st.divider()

    # =====================================================================
    # 4) Structural lens bundles (crt_workspace/lenses/**/bundles)
    # =====================================================================
    st.markdown("### 4) Structural lens bundles")
    st.caption("Preview or delete saved lens bundles.")

    _ensure_dir(LENS_SHELF_DIR)

    try:
        lens_dirs = sorted([d for d in os.listdir(LENS_SHELF_DIR) if os.path.isdir(os.path.join(LENS_SHELF_DIR, d))])
    except Exception:  # pylint: disable=broad-except
        lens_dirs = []

    if not lens_dirs:
        st.info("No lens folders found yet.")
    else:
        lens_labels = [_lens_folder_label(d) for d in lens_dirs]
        label_to_dir = {_lens_folder_label(d): d for d in lens_dirs}

        lens_choice_label = st.selectbox("Select lens", options=lens_labels, index=0, key="crt_maint_lens_choice")
        lens_choice = label_to_dir.get(lens_choice_label, lens_dirs[0])

        bundles_dir = os.path.join(LENS_SHELF_DIR, lens_choice, "bundles")
        _ensure_dir(bundles_dir)

        lens_files = _safe_list_files(bundles_dir, extensions=(".json",))
        if not lens_files:
            st.info("No bundles saved for this lens yet.")
        else:
            disp = ["(Select)"] + [_filename_hint(f) for f in lens_files]
            rev = {_filename_hint(f): f for f in lens_files}
            lf_disp = st.selectbox("Select bundle", options=disp, index=0, key="crt_maint_lens_file")

            if lf_disp != "(Select)":
                lf = rev.get(lf_disp, lf_disp)
                lf_path = os.path.join(bundles_dir, lf)
                lf_payload = _safe_read_json(lf_path)

                with st.expander("Preview", expanded=False):
                    if lf_payload is not None:
                        st.code(_pretty(lf_payload), language="json")
                    else:
                        st.info("Unable to preview (not valid JSON).")

                st.markdown("**Delete lens bundle**")
                st.caption("Permanent deletion. Removes this bundle file from the workspace. This cannot be undone in-app.")

                del_confirm = st.checkbox(
                    "Confirm permanent deletion",
                    value=False,
                    key=f"crt_maint_lens_delete_confirm_{lens_choice}_{lf}",
                )

                if st.button(
                    "🗑️ Delete bundle file",
                    use_container_width=True,
                    disabled=(not del_confirm),
                    key=f"crt_maint_lens_delete_btn_{lens_choice}_{lf}",
                ):
                    try:
                        os.remove(lf_path)
                        st.success("✅ Deleted.")
                        st.rerun()
                    except Exception:  # pylint: disable=broad-except
                        st.error("Unable to delete this file.")

    st.divider()

    # =====================================================================
    # 5) Programme artefacts (manifests / bundles / verified / AI handoffs)
    # =====================================================================
    st.markdown("### 5) Programme artefacts")
    st.caption("Saved artefacts produced during the workflow. Preview to inspect, or delete items you no longer need.")
    st.caption("Flow: 🧾 Manifest → 📦 Bundle → ✅ Verified → 🧠 AI handoff")

    shelves: Dict[str, Dict[str, Any]] = {
        "🧾 Manifests (Task Builder)": {"dir": WORKSPACE_MANIFESTS_DIR, "extensions": (".json",)},
        "📦 Bundles (Task Builder)": {"dir": WORKSPACE_BUNDLES_DIR, "extensions": (".json",)},
        "✅ Verified (for export)": {"dir": WORKSPACE_VERIFIED_DIR, "extensions": (".json",)},
        "🧠 AI handoffs (SYSTEM + USER)": {"dir": WORKSPACE_AI_EXPORTS_DIR, "extensions": (".json",)},
    }

    shelf_label = st.selectbox(
        "Select shelf",
        options=list(shelves.keys()),
        index=0,
        key="crt_maintenance_shelf_select",
    )
    shelf = shelves[shelf_label]
    shelf_dir = str(shelf.get("dir"))
    shelf_ext = shelf.get("extensions")

    _ensure_dir(shelf_dir)

    files = _safe_list_files(shelf_dir, extensions=shelf_ext)
    if not files:
        st.info("Nothing saved here yet.")
    else:
        display = ["(Select)"] + [_filename_hint(f) for f in files]
        reverse_map = {_filename_hint(f): f for f in files}

        chosen_disp = st.selectbox(
            "Select file",
            options=display,
            index=0,
            key="crt_maintenance_file_select",
        )

        if chosen_disp != "(Select)":
            chosen = reverse_map.get(chosen_disp, chosen_disp)
            full_path = os.path.join(shelf_dir, chosen)

            is_json = chosen.lower().endswith(".json")
            payload = _safe_read_json(full_path) if is_json else None

            with st.expander("Preview", expanded=False):
                if is_json and payload is not None:
                    st.code(_pretty(payload), language="json")
                else:
                    st.code(_safe_read_text(full_path, 10_000_000), language="text")

            st.markdown("**Permanent deletion**")
            st.caption("Deletes this file from the workspace. This cannot be undone in-app.")

            del_confirm = st.checkbox(
                "Confirm permanent deletion",
                value=False,
                key=f"crt_maintenance_confirm_delete_{shelf_label}_{chosen}",
            )

            if st.button(
                "🗑️ Delete file",
                use_container_width=True,
                disabled=(not del_confirm),
                key=f"crt_maintenance_delete_{shelf_label}_{chosen}",
            ):
                try:
                    os.remove(full_path)
                    st.success("✅ Deleted.")
                    st.rerun()
                except Exception:  # pylint: disable=broad-except
                    st.error("Unable to delete this file.")

    st.divider()

    # =====================================================================
    # 6) User output templates (container semantics)
    # =====================================================================
    st.markdown("### 6) User output templates")
    st.caption("This file contains multiple templates. Download a backup or delete a single template.")

    user_tpl_payload = _load_user_output_templates()
    tpl_list = user_tpl_payload.get("templates", [])
    if not isinstance(tpl_list, list):
        tpl_list = []
        user_tpl_payload["templates"] = tpl_list

    st.download_button(
        "⬇️ Download templates backup (JSON)",
        data=_pretty(user_tpl_payload).encode("utf-8"),
        file_name="crt_output_templates_user_backup.json",
        mime="application/json",
        use_container_width=True,
    )

    if not tpl_list:
        st.info("No user templates found yet.")
    else:
        items: List[Tuple[str, Dict[str, Any]]] = []
        for t in tpl_list:
            if isinstance(t, dict):
                tid = _template_id(t)
                label = _template_label(t)
                items.append((f"{label} — {tid}", t))

        options = ["(Select)"] + [k for k, _ in items]
        chosen_key = st.selectbox("Select template", options=options, index=0, key="crt_user_tpl_select")

        if chosen_key != "(Select)":
            chosen_tpl = next((tpl for k, tpl in items if k == chosen_key), None)
            if isinstance(chosen_tpl, dict):
                with st.expander("Template preview", expanded=False):
                    st.code(_pretty(chosen_tpl), language="json")

                st.markdown("**Delete template**")
                st.caption("Removes this template from your templates file. This cannot be undone in-app.")

                confirm_del = st.checkbox(
                    "Confirm permanent deletion",
                    value=False,
                    key=f"crt_user_tpl_delete_confirm_{_template_id(chosen_tpl)}",
                )

                if st.button(
                    "🗑️ Delete template",
                    use_container_width=True,
                    disabled=(not confirm_del),
                    key=f"crt_user_tpl_delete_btn_{_template_id(chosen_tpl)}",
                ):
                    try:
                        target_id = _template_id(chosen_tpl)
                        kept: List[Dict[str, Any]] = []
                        removed = False

                        for t in tpl_list:
                            if isinstance(t, dict) and _template_id(t) == target_id and not removed:
                                removed = True
                                continue
                            if isinstance(t, dict):
                                kept.append(t)

                        user_tpl_payload["templates"] = kept
                        if _safe_write_json(USER_TEMPLATES_JSON, user_tpl_payload):
                            st.success("✅ Template deleted.")
                            st.rerun()
                        else:
                            st.error("Unable to save templates file (write error).")
                    except Exception:  # pylint: disable=broad-except
                        st.error("Unable to delete this template.")

    st.divider()

# -------------------------------------------------------------------------------------------------


def main() -> None:
    render_sidebar()
    render_header()
    _inject_manifest_notes_css()

    # -------------------------------------------------------------------------------------------------
    # Info Panel
    # -------------------------------------------------------------------------------------------------
    with st.expander("📖 What is this app about?"):
        render_markdown_file(
            ABOUT_APP_MD,
            fallback=(
                "# 🎛 Programme Builder & AI Export\n\n"
                "This module assembles **programme artefacts** (manifest + bundle) from your selected context and inputs.\n\n"
                "It is designed for **structural, portable outputs** — suitable for review, archiving, and (optionally) AI handoff.\n\n"
                "---\n\n"
                "## What this module does\n\n"
                "- **Select context** from your saved **Org Governance Profiles** and active catalogues.\n"
                "- **Optionally attach lens bundles** (DCR / ASM / IAL / SCES / TSC) as structured inputs.\n"
                "- **Build** a **manifest** (human summary) and a **bundle** (normalised structural container).\n"
                "- Apply **Templates** (built-in or user-defined) to shape the exported output.\n"
                "- **Verify** to generate a clean, export-ready **verified artefact**.\n"
                "- Optionally generate an **AI handoff** (SYSTEM + USER + JSON wrapper) from a verified artefact.\n\n"
                "---\n\n"
                "## Hard boundaries\n\n"
                "- No investment / security advice\n"
                "- No configuration guidance\n"
                "- No assurance or certification\n"
                "- No catalogue editing in this module\n"
                "- No AI calls inside build/verify logic (handoff is packaging only)\n\n"
                "---\n\n"
                "## Where to start\n\n"
                "1) Ensure an **Org Governance Profile** is set and governance catalogues exist (CRT-REQ / CRT-LR).\n"
                "2) (Optional) Save **lens bundles** from the operational lenses (DCR / ASM / IAL / SCES / TSC).\n"
                "3) Use **Task Builder** to assemble the artefact.\n"
                "4) Use **Templates** to format the output.\n"
                "5) Run **Verify** to produce an export-ready artefact.\n\n"
                "---\n\n"
                "## Outputs you will see\n\n"
                "- **Manifest**: compact build summary (human-facing)\n"
                "- **Bundle**: structured container (entities + relationships + metadata)\n"
                "- **Verified artefact**: export-safe copy\n"
                "- **AI handoff**: wrapper used by the AI Observation Console and external tooling\n"
            ),
        )

    tabs = st.tabs(["🎛 Task Builder", "🧱 User Templates", "🔍 Verify", "🧠 AI Prompt & Response", "🧹 Maintenance"])

    with tabs[0]:
        st.markdown("## 🎛 Task Builder")
        st.caption("Build a programme artefact as a compact manifest and a normalised structural bundle.")
        org_profile, org_scope = get_org_profile_and_scope()
        render_context_summary(org_profile, org_scope)

        programme_mode_label = render_programme_mode_selector()

        task_type, anchor_id, anchor_name, manifest_notes, template_selection = render_task_type_selector(programme_mode_label)

        lens_bundles = render_input_bundles_panel(programme_mode_label, task_type)

        render_build_save_handoff(
            programme_mode_label=programme_mode_label,
            task_type=task_type,
            anchor_id=anchor_id,
            anchor_name=anchor_name,
            manifest_notes=manifest_notes,
            template_selection=template_selection,
            org_profile=org_profile,
            org_scope=org_scope,
            lens_bundles=lens_bundles,
        )

        crt_footer()

    with tabs[1]:
        render_user_templates_tab()

    with tabs[2]:
        render_review_tab()

    with tabs[3]:
        render_ai_prompt_response_tab()

    with tabs[4]:
        render_maintenance_tab()


if __name__ == "__main__":
    main()
