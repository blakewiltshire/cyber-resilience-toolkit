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
📚 Reference Data & Trusted Sources — Cyber Resilience Toolkit (CRT)

Read-only reference layer for the CRT ecosystem.

This module provides a structured, non-prescriptive way to explore:

1) 🌐 Cyber Resilience Reference Directory
   - External frameworks, standards, supervisory material, and authoritative
     reference sources that inform cyber, technology, and operational resilience.

2) 🧠 AI Persona Reference
   - Role-aligned interpretive framings for cyber, operational, and governance
     contexts. Designed as scaffolding for AI-augmented exploration, not as
     advisory content.

3) 🗂️ Index & Controls Viewer
   - A concept index (A–Z) and structural views into CRT technical control
     families.

This app is strictly read-only and structural:
- It does not configure controls, score maturity, or provide assurance.
- It surfaces references and structural anchors to support downstream
  decision-support and AI exploration.
"""

from __future__ import annotations

# -------------------------------------------------------------------------------------------------
# Standard Library
# -------------------------------------------------------------------------------------------------
import os
import sys
import string
from typing import Optional, List, Dict, Any

# -------------------------------------------------------------------------------------------------
# Third-party Libraries
# -------------------------------------------------------------------------------------------------
import streamlit as st
import yaml

# -------------------------------------------------------------------------------------------------
# Core Utilities
# -------------------------------------------------------------------------------------------------
# Ensure we can import from the project root / core / apps when running from /pages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))

from core.helpers import (  # pylint: disable=import-error
    get_named_paths,
    load_markdown_file,
    build_sidebar_links,
)

# -------------------------------------------------------------------------------------------------
# Resolve Key Paths (for modules under /pages)
# -------------------------------------------------------------------------------------------------
PATHS = get_named_paths(__file__)
PROJECT_PATH = PATHS["level_up_1"]

ABOUT_APP_MD = os.path.join(
    PROJECT_PATH, "docs", "about_reference_data_trusted_sources.md"
)
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")
BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# YAML-backed catalogues
CONFIG_DIR = os.path.join(PROJECT_PATH, "apps", "config")
CYBER_REFERENCES_YAML = os.path.join(CONFIG_DIR, "cyber_references.yaml")
AI_PERSONAS_YAML = os.path.join(CONFIG_DIR, "ai_personas.yaml")
CONCEPT_YAML = os.path.join(CONFIG_DIR, "index_glossary_cyber.yaml")
TECH_YAML = os.path.join(CONFIG_DIR, "technical_controls_index.yaml")


# -------------------------------------------------------------------------------------------------
# Helper for safe markdown loading
# -------------------------------------------------------------------------------------------------
def render_markdown_file(path: str, fallback: str) -> None:
    """
    Render markdown from a file if present; otherwise show a simple fallback.

    This mirrors the defensive pattern from the Structural Controls & Frameworks module
    without assuming that docs are always present.
    """
    content: Optional[str] = load_markdown_file(path)
    if content:
        st.markdown(content, unsafe_allow_html=True)
    else:
        st.markdown(fallback)

# -------------------------------------------------------------------------------------------------
# Helper for footer
# -------------------------------------------------------------------------------------------------
def crt_footer():
    st.caption(
        "© Blake Media Ltd. | Cyber Resilience Toolkit by Blake Wiltshire — "
        "All content is structural and conceptual; no configuration, advice, or assurance is provided."
    )

# -------------------------------------------------------------------------------------------------
# Reference Directory Data Helpers (from 01_🌐_cyber_reference_directory.py)
# -------------------------------------------------------------------------------------------------
def load_reference_data(yaml_path: str) -> List[Dict[str, Any]]:
    """
    Load the cyber references catalogue from YAML.

    Expected structure: list of entries, each with:
    - id
    - group_key
    - group_label
    - sort_order
    - name
    - url
    - description
    - is_core
    - tags
    """
    if not os.path.exists(yaml_path):
        return []

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
            if isinstance(data, list):
                return data
            # If a mapping is returned, fall back to list under a known key if needed
            return data.get("items", [])
    except Exception:  # pylint: disable=broad-except
        return []


def render_reference_group(data: List[Dict[str, Any]], group_key: str) -> None:
    """
    Render a bullet list for a given group_key from the reference catalogue.
    """
    if not data:
        st.markdown(
            "_No reference entries are currently loaded from the YAML catalogue. "
            "Check `apps/config/cyber_references.yaml` for configuration._"
        )
        return

    entries = [e for e in data if e.get("group_key") == group_key]
    if not entries:
        st.markdown(
            "_No entries found for this category in `cyber_references.yaml`._"
        )
        return

    entries = sorted(entries, key=lambda x: x.get("sort_order", 0))

    lines = []
    for entry in entries:
        name = entry.get("name", "").strip()
        url = entry.get("url", "").strip()
        description = entry.get("description", "").strip()

        if not name or not url:
            # Skip malformed entries silently to avoid breaking the UI
            continue

        if description:
            lines.append(f"- [**{name}**]({url}) —  {description}")
        else:
            lines.append(f"- [**{name}**]({url})")

    if lines:
        st.markdown("\n\n".join(lines))
    else:
        st.markdown(
            "_No valid reference entries available for this category._"
        )


# Load cyber-reference catalogue once at module import (shared by the view)
REFERENCE_DATA = load_reference_data(CYBER_REFERENCES_YAML)


# -------------------------------------------------------------------------------------------------
# AI Persona Reference Helpers (from 03_🧠_ai_persona_reference.py)
# -------------------------------------------------------------------------------------------------
SAMPLE_PERSONAS: Dict[str, Dict[str, Any]] = {
    "Cyber Risk Strategist by Blake Wiltshire": {
        "definition": (
            "Examines how interdependencies, regulatory structures, and organisational design "
            "shape cyber and operational resilience across the environment."
        ),
        "focus": [
            "Systemic exposure",
            "Interdependencies",
            "Regulatory context",
            "Organisational design",
        ],
        "related": [
            "Systemic Risk",
            "Dependency Mapping",
            "Regulatory Expectations",
        ],
        "perspective_frame": (
            "As a Cyber Risk Strategist, interpret the scenario as a set of interacting risk "
            "surfaces rather than isolated issues. Emphasise how dependencies, regulatory drivers, "
            "and organisational decisions combine to influence resilience."
        ),
    },
    "Security Architect by Blake Wiltshire": {
        "definition": (
            "Assesses how technical controls, network design, and trust boundaries align with "
            "the organisation's stated objectives and resilience posture."
        ),
        "focus": [
            "Layered defence",
            "Control inheritance",
            "Network and trust architecture",
            "Adaptive design",
        ],
        "related": [
            "Zero Trust",
            "Segmentation",
            "Security Controls",
        ],
        "perspective_frame": (
            "As a Security Architect, interpret the scenario in terms of boundaries, control placement, "
            "and inheritance. Emphasise design clarity, adaptability, and how technical layers support "
            "or constrain resilience."
        ),
    },
    "Threat Intelligence Analyst by Blake Wiltshire": {
        "definition": (
            "Considers how adversary behaviours, attack chains, and external telemetry relate to the "
            "organisation’s current posture and monitoring approach."
        ),
        "focus": [
            "Threat actor motivations",
            "Tactics, techniques, and procedures",
            "Environmental indicators",
            "Scenario context",
        ],
        "related": [
            "MITRE ATT&CK",
            "Threat Modelling",
            "Detection Engineering",
        ],
        "perspective_frame": (
            "As a Threat Intelligence Analyst, interpret the context through likely attacker objectives, "
            "techniques, and environmental signals. Emphasise how scenarios connect to monitoring coverage "
            "and interpretation."
        ),
    },
    "Governance and Compliance Advisor by Blake Wiltshire": {
        "definition": (
            "Interprets how frameworks such as ISO/IEC 27001, NIST CSF, and DORA map into oversight, "
            "accountability, and evidence expectations within the organisation."
        ),
        "focus": [
            "Governance structures",
            "Policy and oversight",
            "Regulatory alignment",
            "Evidence and assurance",
        ],
        "related": [
            "ISO/IEC 27001",
            "NIST CSF",
            "DORA",
        ],
        "perspective_frame": (
            "As a Governance and Compliance Advisor, interpret the scenario through oversight, accountability, "
            "and proportional alignment to frameworks. Emphasise clarity of roles and robustness of evidence."
        ),
    },
    "Resilience Engineer by Blake Wiltshire": {
        "definition": (
            "Evaluates redundancy, recovery paths, and the organisation’s capacity to operate through "
            "disruption and adapt after events."
        ),
        "focus": [
            "Business continuity",
            "Recovery design",
            "Adaptive capacity",
            "Dependency mapping",
        ],
        "related": [
            "ISO 22301",
            "Incident Scenarios",
            "Dependency Graphs",
        ],
        "perspective_frame": (
            "As a Resilience Engineer, interpret the scenario through continuity, recovery, and adaptation. "
            "Emphasise realistic conditions, dependency clarity, and learning."
        ),
    },
    "Incident Response Analyst by Blake Wiltshire": {
        "definition": (
            "Focuses on how incidents are detected, triaged, contained, and reviewed, with attention "
            "to coordination and learning rather than blame."
        ),
        "focus": [
            "Detection effectiveness",
            "Containment strategies",
            "Response coordination",
            "Post-incident learning",
        ],
        "related": [
            "Playbooks",
            "CSIRTs",
            "Detection Engineering",
        ],
        "perspective_frame": (
            "As an Incident Response Analyst, interpret scenarios as timelines of signals and decisions. "
            "Emphasise detection clarity, coordination, and the conditions for effective learning."
        ),
    },
    "AI Systems Auditor by Blake Wiltshire": {
        "definition": (
            "Frames risk at the intersection of AI assurance, data quality, model behaviour, "
            "and cybersecurity controls."
        ),
        "focus": [
            "AI assurance",
            "Data and model integrity",
            "Robustness and resilience",
            "Oversight structures",
        ],
        "related": [
            "Model Risk",
            "Data Governance",
            "AI Governance",
        ],
        "perspective_frame": (
            "As an AI Systems Auditor, interpret the scenario at the intersection of AI, data, and security. "
            "Emphasise traceability, robustness, and the alignment between AI behaviour and control structures."
        ),
    },
    "Supply-Chain Risk Analyst by Blake Wiltshire": {
        "definition": (
            "Evaluates systemic exposure arising from vendors, APIs, cloud platforms, and other external "
            "service layers."
        ),
        "focus": [
            "Third-party dependencies",
            "Supply-chain propagation",
            "Cloud and platform reliance",
            "Contractual and operational boundaries",
        ],
        "related": [
            "Vendor Management",
            "DORA ICT Providers",
            "Dependency Graphs",
        ],
        "perspective_frame": (
            "As a Supply-Chain Risk Analyst, interpret the scenario as a set of interconnected providers and "
            "services. Emphasise shared dependencies, concentration points, and transparency."
        ),
    },
    "Systemic Governance Architect by Blake Wiltshire": {
        "definition": (
            "Designs decision-support scaffolds that link governance, control architectures, "
            "and organisational structures across the enterprise."
        ),
        "focus": [
            "Systemic governance",
            "Control architecture integration",
            "Decision-support scaffolds",
            "Organisational alignment",
        ],
        "related": [
            "Operating Models",
            "Control Catalogues",
            "Risk Governance",
        ],
        "perspective_frame": (
            "As a Systemic Governance Architect, interpret the scenario through the alignment between "
            "governance layers, control architectures, and day-to-day operation."
        ),
    },
    "Behavioural Resilience Specialist by Blake Wiltshire": {
        "definition": (
            "Assesses how behaviours, incentives, and everyday practices influence the reliability "
            "of defences and incident response."
        ),
        "focus": [
            "Human factors",
            "Insider risk",
            "Culture and communication",
            "Training and rehearsal",
        ],
        "related": [
            "Security Culture",
            "Awareness Campaigns",
            "Insider Threat",
        ],
        "perspective_frame": (
            "As a Behavioural Resilience Specialist, interpret the scenario through human behaviour, "
            "incentives, and culture. Emphasise how everyday practices influence the reliability "
            "of controls and response."
        ),
    },
}


def _chip_html(text: str) -> str:
    """Return inert 'chip' HTML (neutral, non-clickable)."""
    safe = str(text).replace("|", "¦")
    return (
        "<span style='display:inline-block;padding:4px 8px;margin:2px;"
        "border:1px solid #e5e7eb;border-radius:9999px;font-size:12px;"
        "color:#374151;background:#ffffff;'>"
        f"{safe}</span>"
    )


def load_personas_yaml(path: str) -> Dict[str, Any]:
    """Load AI personas YAML file if available and valid, else return empty dict."""
    if not yaml:
        return {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                return data
        except Exception:  # pylint: disable=broad-except
            return {}
    return {}


def build_registry() -> List[Dict[str, Any]]:
    """
    Produce a unified list of persona dicts with a superset schema:
    - name, icon, short_description, definition, focus, related
    - behaviour, avoid, starters, gpt, prompt_template_key, perspective_frame (optional)
    """
    data = load_personas_yaml(AI_PERSONAS_YAML)
    if "personas" in data and isinstance(data["personas"], list):
        return data["personas"]

    # Fallback to SAMPLE_PERSONAS → normalise to the superset schema
    registry: List[Dict[str, Any]] = []
    for name, payload in SAMPLE_PERSONAS.items():
        registry.append(
            {
                "name": name,
                "icon": payload.get("icon", ""),
                "short_description": payload.get("short_description", ""),
                "definition": payload.get("definition", ""),
                "focus": payload.get("focus", []),
                "related": payload.get("related", []),
                "behaviour": payload.get("behaviour", ""),
                "avoid": payload.get("avoid", []),
                "starters": payload.get("starters", []),
                "gpt": payload.get("gpt", {}),
                "prompt_template_key": payload.get("prompt_template_key", name),
                "perspective_frame": payload.get("perspective_frame", ""),
            }
        )
    return registry


REGISTRY: List[Dict[str, Any]] = build_registry()


def render_persona(card: Dict[str, Any]) -> None:
    """Render a single persona card with neutral, non-leading presentation."""
    name = card.get("name", "Unnamed Persona")
    icon = card.get("icon", "")
    short_desc = card.get("short_description", "")
    definition = card.get("definition", "")
    focus = card.get("focus", []) or []
    related = card.get("related", []) or []
    behaviour = (card.get("behaviour") or "").strip()
    avoid = card.get("avoid", []) or []
    starters = card.get("starters", []) or []
    gpt_meta = card.get("gpt", {}) or {}

    st.markdown(f"#### {icon} **{name}**" if icon else f"#### **{name}**")
    if short_desc:
        st.write(short_desc)
    if definition:
        st.caption(definition)

    if focus:
        st.markdown("**Focus Areas:**")
        st.markdown(" ".join(_chip_html(x) for x in focus), unsafe_allow_html=True)

    if related:
        st.markdown("**Related:**")
        st.markdown(" ".join(_chip_html(x) for x in related), unsafe_allow_html=True)

    if behaviour:
        st.markdown("**How this perspective behaves**")
        st.write(behaviour)

    if avoid:
        st.markdown("**Avoid**")
        st.markdown("- " + "\n- ".join(str(a) for a in avoid))

    if starters:
        with st.expander("Conversation starters"):
            for s in starters:
                st.markdown(f"- {s}")

    # Optional: show perspective frame if present (read-only)
    op_prompt = (card.get("perspective_frame") or "").strip()
    if op_prompt:
        with st.expander("Perspective frame (optional)"):
            st.code(op_prompt, language="text")

    if gpt_meta:
        with st.expander("GPT metadata"):
            st.json(gpt_meta)

    st.divider()


def filter_registry(query: str, initial: str) -> List[Dict[str, Any]]:
    """Return filtered & sorted persona list by search and initial."""
    def matches(p: Dict[str, Any]) -> bool:
        if not query:
            return True
        hay = " ".join(
            [
                p.get("name", ""),
                p.get("short_description", ""),
                p.get("definition", ""),
                " ".join(p.get("focus", []) or []),
                " ".join(p.get("related", []) or []),
            ]
        ).lower()
        return query.lower().strip() in hay

    items = REGISTRY[:]
    if initial and initial in string.ascii_uppercase:
        items = [
            p
            for p in items
            if p.get("name", "").upper().startswith(initial.upper())
        ]
    items = [p for p in items if matches(p)]
    return sorted(items, key=lambda x: x.get("name", "").lower())


# -------------------------------------------------------------------------------------------------
# Index & Controls Helpers (from 04_🗂️_index_controls_viewer.py)
# -------------------------------------------------------------------------------------------------
def load_concept_index(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the concept index (Appendix F) from YAML.

    Expected schema:
    {
      "Term": {
        "definition": str,
        "chapters": [str, ...],
        "related": [str, ...]
      },
      ...
    }
    """
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if isinstance(data, dict):
            return data
    except Exception:  # pragma: no cover
        return {}
    return {}


def load_technical_controls(path: str) -> List[Dict[str, Any]]:
    """
    Load the technical controls index (Appendix E) from YAML.

    Expected schema:
    {
      "controls": [
        {
          "name": str,
          "description": str,
          "note": str,
          "linked_controls": [str, ...],
          "linked_series": [str, ...],
          "linked_modules": [str, ...],
          "tags": [str, ...]
        },
        ...
      ]
    }
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        items = data.get("controls", [])
        return items if isinstance(items, list) else []
    except Exception:  # pragma: no cover
        return []


CONCEPT_INDEX = load_concept_index(CONCEPT_YAML)
TECH_CONTROLS = load_technical_controls(TECH_YAML)

CONCEPT_INDEX_NORMALISED: Dict[str, Dict[str, Any]] = {
    (term or "").strip(): payload or {}
    for term, payload in CONCEPT_INDEX.items()
}


def render_concept(term: str, payload: Dict[str, Any]) -> None:
    """Render a single concept entry (Appendix F style)."""
    definition = (payload.get("definition") or "").strip()
    chapters = payload.get("chapters") or []
    related = payload.get("related") or []

    st.markdown(f"#### **{term}**")
    if definition:
        st.write(definition)

    if chapters:
        st.markdown(
            " ".join(_chip_html(ch) for ch in chapters),
            unsafe_allow_html=True,
        )

    if related:
        st.caption("Related:")
        st.markdown(
            " ".join(_chip_html(r) for r in related),
            unsafe_allow_html=True,
        )

    st.divider()


def filter_concepts(query: str, initial: str) -> List[str]:
    """Filter concept index by query and initial letter.

    Safely handles chapters/related as strings, dicts, or mixed lists by
    normalising each element to a string before building the search haystack.
    """
    keys = list(CONCEPT_INDEX_NORMALISED.keys())

    # Optional first-letter filter
    if initial and initial in string.ascii_uppercase:
        keys = [k for k in keys if str(k).upper().startswith(initial.upper())]

    if query:
        q = query.strip().lower()
        filtered: List[str] = []

        for k in keys:
            payload = CONCEPT_INDEX_NORMALISED.get(k, {}) or {}

            # Normalise chapters / related to strings to avoid TypeError when joining
            chapters_raw = payload.get("chapters") or []
            related_raw = payload.get("related") or []

            chapters_text = " ".join(str(ch) for ch in chapters_raw)
            related_text = " ".join(str(r) for r in related_raw)

            hay = " ".join(
                [
                    str(k),
                    str(payload.get("definition") or ""),
                    chapters_text,
                    related_text,
                ]
            ).lower()

            if q in hay:
                filtered.append(k)

        keys = filtered

    # Be defensive in case keys are not all plain strings
    return sorted(keys, key=lambda s: str(s).lower())

def render_technical_control(control: Dict[str, Any]) -> None:
    """Render a single technical control family card (Appendix E style)."""
    name = control.get("name", "Unnamed Control Family")
    description = (control.get("description") or "").strip()
    note = (control.get("note") or "").strip()
    linked_controls = control.get("linked_controls") or []
    linked_series = control.get("linked_series") or []
    linked_modules = control.get("linked_modules") or []
    tags = control.get("tags") or []

    st.markdown(f"#### **{name}**")
    if description:
        st.write(description)

    if note:
        st.caption(f"📌 {note}")

    chips_line = []

    if linked_controls:
        chips_line.append(
            "**CRT Controls:** "
            + " ".join(_chip_html(c) for c in linked_controls)
        )

    if linked_series:
        chips_line.append(
            "**Control Families / Series:** "
            + " ".join(_chip_html(s) for s in linked_series)
        )

    if linked_modules:
        chips_line.append(
            "**CRT Modules (illustrative touchpoints):** "
            + " ".join(_chip_html(m) for m in linked_modules)
        )

    if chips_line:
        st.markdown("<br>".join(chips_line), unsafe_allow_html=True)

    if tags:
        st.caption("Tags:")
        st.markdown(
            " ".join(_chip_html(t) for t in tags),
            unsafe_allow_html=True,
        )

    st.divider()


def filter_technical_controls(query: str, initial: str) -> List[Dict[str, Any]]:
    """Filter technical controls by query and initial letter."""
    items = TECH_CONTROLS[:]

    if initial and initial in string.ascii_uppercase:
        items = [
            c
            for c in items
            if str(c.get("name", "")).upper().startswith(initial.upper())
        ]

    if query:
        q = query.strip().lower()

        def matches(c: Dict[str, Any]) -> bool:
            hay = " ".join(
                [
                    str(c.get("name", "")),
                    str(c.get("description", "")),
                    str(c.get("note", "")),
                    " ".join(c.get("linked_controls") or []),
                    " ".join(c.get("linked_series") or []),
                    " ".join(c.get("linked_modules") or []),
                    " ".join(c.get("tags") or []),
                ]
            ).lower()
            return q in hay

        items = [c for c in items if matches(c)]

    return sorted(items, key=lambda x: str(x.get("name", "")).lower())


# -------------------------------------------------------------------------------------------------
# Sub-View Renderers
# -------------------------------------------------------------------------------------------------
def render_reference_directory() -> None:
    """
    🌐 Cyber Resilience Reference Directory

    High-level directory of external frameworks, standards, and authoritative references,
    backed by `apps/config/cyber_references.yaml`.
    """
    st.header("🌐 Cyber Resilience Reference Directory")
    st.caption(
        "Central hub for accessing key cybersecurity frameworks, resilience regulations, "
        "research portals, and structural reference systems used across the Cyber "
        "Resilience Toolkit (CRT)."
    )

    # Optional: view-level warning if YAML not found or empty
    if not REFERENCE_DATA:
        st.warning(
            "No entries loaded from `apps/config/cyber_references.yaml`. "
            "Update the YAML file to populate this directory."
        )

    st.markdown(
        """
This view provides a non-prescriptive index of external reference material that
can influence a cyber resilience programme.

Use this as a directory of where reference material lives, not as a checklist.
Any mapping into CRT catalogues occurs in the structural modules
(e.g. 📂 Structural Controls & Frameworks).
"""
    )

    # --- Section 1: Cybersecurity Standards & Control Frameworks ---
    with st.expander("🧱 Cybersecurity Standards and Control Frameworks"):
        st.markdown(
            """
Core frameworks defining the structural logic of security controls, layered defence,
and governance alignment.
"""
        )
        render_reference_group(REFERENCE_DATA, "standards")

    # --- Section 2: Regulatory and Supervisory Authorities ---
    with st.expander("⚖️ Regulatory and Supervisory Authorities"):
        st.markdown(
            """
Regional and global authorities issuing cybersecurity and operational resilience mandates.
"""
        )
        render_reference_group(REFERENCE_DATA, "regulators")

    # --- Section 3: Operational Resilience & Continuity Frameworks ---
    with st.expander("🏛️ Operational Resilience and Continuity Frameworks"):
        st.markdown(
            """
Reference systems emphasising systemic resilience, continuity, and critical
infrastructure protection.
"""
        )
        render_reference_group(REFERENCE_DATA, "continuity")

    # --- Section 4: Industry Reports and Research Portals ---
    with st.expander("📊 Industry Reports and Research Portals"):
        st.markdown(
            """
Research hubs, think tanks, and public–private alliances advancing understanding
of cyber risk and resilience.
"""
        )
        render_reference_group(REFERENCE_DATA, "research")

    # --- Section 5: International Organisations & Multilateral Initiatives ---
    with st.expander("🌐 International Organisations and Multilateral Initiatives"):
        st.markdown(
            """
Bodies establishing shared policy, resilience cooperation, and cross-border standards.
"""
        )
        render_reference_group(REFERENCE_DATA, "international")

    # --- Section 6: Taxonomies, Classifications & Identifier Systems ---
    with st.expander("🧩 Taxonomies, Classifications, and Identifier Systems"):
        st.markdown(
            """
Common reference systems ensuring consistent terminology and traceability across
resilience frameworks.
"""
        )
        render_reference_group(REFERENCE_DATA, "taxonomies")

    # --- Section 7: Vulnerability, Exposure & Threat Reference Systems ---
    with st.expander("🔍 Vulnerability, Exposure, and Threat Reference Systems"):
        st.markdown(
            """
Public reference systems providing canonical identifiers and shared terminology
for vulnerabilities, exposures, and observed threat conditions.

These entries are included as reference layers for identification, correlation,
and traceability. They do not represent implementation guidance.
"""
        )
        render_reference_group(REFERENCE_DATA, "vulnerability_refs")

    # --- Section 8: National Cybersecurity Centres & CSIRTs (Supplementary) ---
    with st.expander("🇺🇳 National Cybersecurity Centres & CSIRTs (Supplementary)"):
        st.markdown(
            """
Additional reference points for national-level cybersecurity centres and incident
response networks.
"""
        )
        render_reference_group(REFERENCE_DATA, "csirts")

    # --- Section 9: Application Security & Best-Practice Communities (Supplementary) ---
    with st.expander(
        "🛠️ Application Security & Best-Practice Communities (Supplementary)"
    ):
        st.markdown(
            """
Communities and reference projects that inform secure design, testing, and
application-level resilience.
"""
        )
        render_reference_group(REFERENCE_DATA, "appsec")

    st.divider()

def render_ai_persona_reference() -> None:
    """
    🧠 AI Persona Reference

    Read-only role lenses for structured exploration.
    These profiles describe how different roles tend to frame CRT structures.
    """
    st.header("🧠 AI Persona Reference")
    st.markdown(
        """
This view provides **reference profiles** for role-based lenses used across the CRT ecosystem.

They support:
- Scenario interpretation and structured inquiry
- Cross-checking assumptions from different organisational perspectives
- Interpreting CRT controls, failures, compensations, and obligations through different frames

These personas are **not** predictive agents, advisers, or substitutes for human judgment.
They are **framing metadata** designed to keep exploration consistent and non-prescriptive.

If you use personas in an external AI workflow, treat them as **optional lenses** applied to an artefact —
not as required inputs for generating the artefact.
"""
    )


    st.markdown("---")

    # Controls (search + letter filter)
    col1, col2 = st.columns([3, 2])
    with col1:
        query = st.text_input(
            "🔎 Search personas or definitions",
            placeholder="e.g., ‘Cyber Risk Strategist’, ‘Incident Response’",
        )
    with col2:
        letters = ["All"] + list(string.ascii_uppercase)
        selected = st.selectbox(
            "Filter by letter",
            letters,
            index=0,
            key="persona_filter_letter_select",
        )
        initial = "" if selected == "All" else selected

    st.markdown("---")

    # Results
    results = filter_registry(query, initial)
    if not results:
        st.info(
            "No matching personas. Try a different letter or refine your search."
        )
        return

    st.caption(
        f"Showing {len(results)} persona{'s' if len(results) != 1 else ''}"
    )
    for card in results:
        render_persona(card)

def render_index_and_controls_viewer() -> None:
    """
    🗂️ Index & Controls Viewer

    Concept index (A–Z) and structural views of CRT technical control families.
    Backed by `index_glossary_cyber.yaml` and `technical_controls_index.yaml`.
    """
    st.header("🗂️ Index & Controls Viewer")
    st.caption(
        "Concept index and technical control families underpinning the Cyber Resilience Toolkit (CRT)."
    )

    st.markdown(
        """
This view provides two complementary reference layers:

1. Concept Index
   Terminology and structural themes aligned with the Cyber Resilience in the Information Age guide.
   Entries reference chapters and related concepts.

2. Technical Controls Index
   Structural overview of control families and mechanisms underpinning cyber-resilience architecture.
   Entries can map to CRT-C / CRT-F / CRT-N catalogue elements and CRT modules.

Both layers are read-only and serve as a structural reference, not an implementation checklist.
"""
    )

    st.markdown("---")

    # Choose sub-view (Concept vs Technical) – local to this panel
    sub_view = st.radio(
        "Select reference layer",
        ["📘 Concept Index", "🧰 Technical Controls Index"],
        index=0,
        horizontal=True,
        key="index_controls_layer_radio",
    )

    # Shared search + A–Z filter, but contextualised by sub_view
    col1, col2 = st.columns([3, 2])
    with col1:
        if sub_view == "📘 Concept Index":
            query = st.text_input(
                "🔎 Search concepts, definitions, or related terms",
                placeholder="e.g., ‘Adaptive Resilience’, ‘Zero-Trust Architecture’",
                key="index_concept_search",
            )
        else:
            query = st.text_input(
                "🔎 Search control families, notes, or CRT references",
                placeholder="e.g., ‘Identity’, ‘CRT-C-0020’, ‘telemetry’",
                key="index_controls_search",
            )
    with col2:
        letters = ["All"] + list(string.ascii_uppercase)
        selected = st.selectbox(
            "Filter by starting letter",
            letters,
            index=0,
            key="crt_index_letter_select",
        )
        initial = "" if selected == "All" else selected

    st.markdown("---")

    # Results
    if sub_view == "📘 Concept Index":
        results = filter_concepts(query, initial)
        if not results:
            st.info(
                "No matching concept entries. Try a different letter or search term."
            )
        else:
            st.caption(
                f"Showing {len(results)} concept entr{'y' if len(results) == 1 else 'ies'}"
            )
            for term in results:
                render_concept(term, CONCEPT_INDEX_NORMALISED.get(term, {}))
    else:
        results_controls = filter_technical_controls(query, initial)
        if not results_controls:
            st.info(
                "No matching control families. Try a different letter or search term."
            )
        else:
            st.caption(
                f"Showing {len(results_controls)} control famil{'y' if len(results_controls) == 1 else 'ies'}"
            )
            for ctrl in results_controls:
                render_technical_control(ctrl)

# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------------------------------------------
st.set_page_config(page_title="Reference Data & Trusted Sources", layout="wide")

st.title("📚 Reference Data & Trusted Sources — Insight Directory")
st.caption(
    "Read-only reference layer for external frameworks, AI personas, and CRT index & control "
    "families. All content is structural and conceptual; no configuration, advice, or "
    "assurance is provided."
)

# -------------------------------------------------------------------------------------------------
# Info Panel
# -------------------------------------------------------------------------------------------------
with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "This module provides a structured, non-prescriptive directory of reference "
            "material that underpins the Cyber Resilience Toolkit (CRT). It surfaces:\n\n"
            "- External frameworks and trusted sources\n"
            "- AI persona reference profiles\n"
            "- A concept index and CRT control-family viewer\n\n"
            "It does not configure controls, set policy, or perform assessments. "
            "Use it as a navigation and context layer to support downstream modules and "
            "AI-augmented exploration."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------------------------------------------
st.sidebar.title("📂 Navigation Menu")
st.sidebar.page_link("app.py", label="CRT Portal")
for path, label in build_sidebar_links():
    st.sidebar.page_link(path, label=label)
st.sidebar.divider()
st.logo(BRAND_LOGO_PATH)  # pylint: disable=no-member

# Sidebar — Getting Started / Context
st.sidebar.markdown("### 🚀 Getting Started")
st.sidebar.caption(
    "Follow the flow:\n\n"
    "1. Cyber Resilience Reference Directory — browse external frameworks, standards, "
    "and trusted sources.\n"
    "2. AI Persona Reference — inspect role-aligned reference profiles used for "
    "AI-augmented exploration.\n"
    "3. Index & Controls Viewer — explore CRT concepts and control families via an A–Z index.\n"
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    [
        "🌐 Cyber Resilience Reference Directory",
        "🧠 AI Persona Reference",
        "🗂️ Index & Controls Viewer",
    ],
    index=0,
)

# -------------------------------------------------------------------------------------------------
# About & Support
# -------------------------------------------------------------------------------------------------
st.sidebar.divider()
with st.sidebar.expander("ℹ️ About & Support"):
    support_md = load_markdown_file(ABOUT_SUPPORT_MD)
    if support_md:
        st.markdown(support_md, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------
# Main View Routing
# -------------------------------------------------------------------------------------------------
if view_mode == "🌐 Cyber Resilience Reference Directory":
    render_reference_directory()
elif view_mode == "🧠 AI Persona Reference":
    render_ai_persona_reference()
elif view_mode == "🗂️ Index & Controls Viewer":
    render_index_and_controls_viewer()
else:
    # Defensive fallback — should not occur given the fixed radio options.
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
