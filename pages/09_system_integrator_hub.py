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
🔄 System Integrator Hub — Cyber Resilience Toolkit (CRT)

The System Integrator Hub (SIH) is the **single point of truth** for CRT catalogues.

This module provides a **read-only console** to:
- Inspect catalogue load state via SIH (backbone vs append-only)
- Review basic schema / row counts for each catalogue
- Explore catalogue content safely through SIH
- Optionally probe structural relationships for a single entity (if supported)

All operations in this UI are **read-only**. The SIH runtime:
- Loads and validates CRT catalogues
- Enforces backbone vs append-only rules
- Exposes a thin internal API (e.g., get_catalogue, resolve_entity, build_relationships)
"""

from __future__ import annotations

# -------------------------------------------------------------------------------------------------
# Standard Library
# -------------------------------------------------------------------------------------------------
import os
import sys
from typing import Dict, List, Optional, Any

# -------------------------------------------------------------------------------------------------
# Third-party Libraries
# -------------------------------------------------------------------------------------------------
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------------------------------------
# Core Utilities
# -------------------------------------------------------------------------------------------------
# Ensure we can import from the project root / core / apps when running from /pages
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "apps"))
sys.path.append(os.path.join(PROJECT_ROOT, "core"))

from core.helpers import (  # pylint: disable=import-error
    load_markdown_file,
    build_sidebar_links,
)

# SIH runtime — required for this module to function
try:  # pylint: disable=wrong-import-position
    from core.sih import get_sih  # type: ignore
except Exception:  # pylint: disable=broad-except
    get_sih = None  # type: ignore

# -------------------------------------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------------------------------------
ABOUT_APP_MD = os.path.join(
    PROJECT_ROOT, "docs", "about_system_integrator_hub.md"
)
ABOUT_SUPPORT_MD = os.path.join(PROJECT_ROOT, "docs", "about_and_support.md")
BRAND_LOGO_PATH = os.path.join(PROJECT_ROOT, "brand", "blake_logo.png")

# IMPORTANT:
# Base path for SIH must be the folder that directly contains CRT-*.csv
BASE_CATALOGUE_PATH = os.path.join(
    PROJECT_ROOT, "apps", "data_sources", "crt_catalogues"
)

# -------------------------------------------------------------------------------------------------
# Catalogue configuration (from locked spec)
# -------------------------------------------------------------------------------------------------
BACKBONE_CATALOGUES: List[str] = [
    "CRT-C",   # Controls
    "CRT-F",   # Failures
    "CRT-N",   # Compensations
    "CRT-POL", # Policies
    "CRT-STD", # Standards
]

APPEND_ONLY_CATALOGUES: List[str] = [
    "CRT-LR",  # Legal / Regulatory requirements
    "CRT-REQ", # Requirements (internal / external)
    "CRT-D",   # Data & Classification
    "CRT-AS",  # Assets & Surface
    "CRT-I",   # Identity & Trust Anchors
    "CRT-SC",  # Supply-Chain & Vendors
    "CRT-T",   # Telemetry & Signal Sources
    "CRT-G",   # Control Groups / Domains
]

ALL_CATALOGUES: List[str] = BACKBONE_CATALOGUES + APPEND_ONLY_CATALOGUES


# -------------------------------------------------------------------------------------------------
# Small helper for safe markdown loading
# -------------------------------------------------------------------------------------------------
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
# Helper for footer
# -------------------------------------------------------------------------------------------------
def crt_footer() -> None:
    st.divider()
    st.caption(
        "© Blake Media Ltd. | Cyber Resilience Toolkit by Blake Wiltshire — "
        "All content is structural and conceptual; no configuration, advice, or assurance is provided."
    )


# -------------------------------------------------------------------------------------------------
# SIH integration helpers
# -------------------------------------------------------------------------------------------------
def _get_sih_instance() -> Optional[Any]:
    """
    Obtain a SIH instance from core.sih.

    If SIH is unavailable or initialisation fails, return None and let the caller
    handle the error gracefully in the UI.
    """
    if get_sih is None:
        st.error("core.sih.get_sih could not be imported. Check your core/sih.py module.")
        return None

    # Optional: show the base path in a tiny caption for debugging
    st.caption(f"🔧 SIH base path: `{BASE_CATALOGUE_PATH}`")

    try:
        sih = get_sih(BASE_CATALOGUE_PATH)
        return sih
    except Exception as exc:  # pylint: disable=broad-except
        st.error("An exception occurred while initialising SIH. See details below.")
        st.exception(exc)
        return None


def _load_catalogues_via_sih(sih: Any) -> Dict[str, pd.DataFrame]:
    """
    Use SIH to load all catalogues defined in ALL_CATALOGUES.

    This function is strictly read-only and does not attempt to read CSV files
    directly; it relies on SIH to enforce backbone vs append-only rules.
    """
    catalogues: Dict[str, pd.DataFrame] = {}
    for name in ALL_CATALOGUES:
        try:
            df = sih.get_catalogue(name)
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame()
        except Exception:  # pylint: disable=broad-except
            df = pd.DataFrame()
        catalogues[name] = df
    return catalogues


def _guess_id_columns(df: pd.DataFrame) -> List[str]:
    """
    Heuristic to suggest likely identifier columns for a catalogue.
    Purely for display / debugging.

    Extended to handle CRT-REQ's requirement_set_id / requirement_id pattern.
    """
    candidates = [
        # Core CRT backbones
        "control_id", "failure_id", "n_id",
        "policy_id", "standard_id", "lr_id",
        # Requirements (CRT-REQ)
        "requirement_id", "requirement_set_id", "req_id",
        # Structural catalogues
        "d_id", "data_id",
        "as_id", "asset_id",
        "i_id", "identity_id",
        "sc_id", "vendor_id",
        "telemetry_id", "t_id",
        "group_id", "id",
    ]
    return [c for c in candidates if c in df.columns]


def _summarise_catalogue(name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build a simple summary for a catalogue: row count, column count, likely ID columns.
    """
    row_count = int(len(df))
    col_count = int(len(df.columns))
    id_cols = _guess_id_columns(df)
    is_backbone = name in BACKBONE_CATALOGUES
    is_append = name in APPEND_ONLY_CATALOGUES

    return {
        "catalogue": name,
        "type": "Backbone" if is_backbone else "Append-only" if is_append else "Unknown",
        "rows": row_count,
        "columns": col_count,
        "likely_id_columns": ", ".join(id_cols) if id_cols else "",
        "empty": row_count == 0,
    }


# -------------------------------------------------------------------------------------------------
# View 1 — Catalogue Health Overview
# -------------------------------------------------------------------------------------------------
def render_view_catalogue_health(catalogues: Dict[str, pd.DataFrame]) -> None:
    """
    View 1 — Catalogue Health Overview

    Shows a consolidated summary for all catalogues loaded via SIH,
    including backbone vs append-only, row counts, and likely identifier columns.
    """
    st.header("📊 Catalogue Health Overview")

    st.markdown(
        """
Use this view to confirm that the **System Integrator Hub** (SIH) has loaded
all CRT catalogues correctly, and that the backbone vs append-only distinction
is applied as expected.

- Backbone catalogues are **not modified** by the program.
- Append-only catalogues may be extended via 📂 Structural Controls & Frameworks.
- All modules must read catalogue data through SIH.
"""
    )

    summaries = [_summarise_catalogue(name, df) for name, df in catalogues.items()]
    df_summary = pd.DataFrame(summaries)

    if df_summary.empty:
        st.error("No catalogue data is available via SIH. Check SIH initialisation.")
        return

    # Order by type (Backbone first), then name
    type_order = {"Backbone": 0, "Append-only": 1, "Unknown": 2}
    df_summary["type_sort"] = df_summary["type"].map(type_order).fillna(99)
    df_summary = df_summary.sort_values(by=["type_sort", "catalogue"]).drop(columns=["type_sort"])

    st.markdown("### 🔎 High-Level Status")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Backbone catalogues", int((df_summary["type"] == "Backbone").sum()))
    with c2:
        st.metric("Append-only catalogues", int((df_summary["type"] == "Append-only").sum()))
    with c3:
        st.metric("Empty catalogues", int(df_summary["empty"].sum()))

    st.markdown("### 📋 Catalogue Summary (via SIH)")
    display_cols = ["catalogue", "type", "rows", "columns", "likely_id_columns", "empty"]
    st.dataframe(
        df_summary[display_cols],
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "All figures above reflect catalogues as exposed by SIH. "
        "If any backbone catalogue appears empty or missing, investigate SIH configuration "
        "and your underlying CRT CSVs."
    )


# -------------------------------------------------------------------------------------------------
# View 2 — Catalogue Explorer
# -------------------------------------------------------------------------------------------------
def render_view_catalogue_explorer(catalogues: Dict[str, pd.DataFrame]) -> None:
    """
    View 2 — Catalogue Explorer

    Allows the user to inspect the schema and sample content of a single catalogue,
    purely via SIH, without reading CSV files directly.
    """
    st.header("🗂️ Catalogue Explorer")

    st.markdown(
        """
Use this view to **explore the content** of a single catalogue as exposed by SIH.

This is helpful for:
- Verifying that append-only extensions have been loaded
- Checking schema consistency for each catalogue
- Understanding what fields are available to Structural Lenses and AI-context modules
"""
    )

    available_catalogues = [name for name in ALL_CATALOGUES if name in catalogues]
    if not available_catalogues:
        st.warning("No catalogues are available via SIH.")
        return

    selected_catalogue = st.selectbox(
        "Choose a catalogue to explore",
        options=available_catalogues,
        index=0,
    )

    df = catalogues.get(selected_catalogue, pd.DataFrame())
    if df.empty:
        st.info(f"`{selected_catalogue}` is currently empty or not loaded.")
        return

    st.markdown(f"### 📁 {selected_catalogue} — Schema & Sample Rows")

    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown("#### Schema")
        st.write(f"**Rows:** {len(df)}")
        st.write(f"**Columns:** {len(df.columns)}")

        id_cols = _guess_id_columns(df)
        if id_cols:
            st.write("**Likely ID columns:**")
            for col in id_cols:
                st.code(col)
        else:
            st.write("**Likely ID columns:** _none detected_")

        st.markdown("**Column names:**")
        st.code(", ".join(df.columns.tolist()), language="text")

    with c2:
        st.markdown("#### Sample (first 50 rows)")
        st.dataframe(df.head(50), width="stretch", hide_index=True)

    st.caption(
        "This view is strictly read-only and reflects whatever SIH has loaded "
        "from your CRT catalogue files."
    )


# -------------------------------------------------------------------------------------------------
# View 3 — Entity & Relationship Probe (improved UX)
# -------------------------------------------------------------------------------------------------
def render_view_entity_probe(sih: Any, catalogues: Dict[str, pd.DataFrame]) -> None:
    """
    View 3 — Entity & Relationship Probe

    This view allows the user to:
    - Look up a single entity via SIH (catalogue + ID)
    - Optionally inspect structural relationships if supported by SIH

    To avoid having to flip between pages, this view also offers:
    - A dropdown of IDs from the chosen catalogue (top N rows)
    """

    st.header("🧪 Entity & Relationship Probe")

    st.markdown(
        """
Use this view to **inspect a single entity** as seen by SIH, and (optionally)
its structural relationships.

You can either:
- Type an ID manually, or
- Pick one from the catalogue using the dropdown below.
"""
    )

    cat = st.selectbox(
        "Catalogue",
        options=ALL_CATALOGUES,
        index=0,
        help="Choose the catalogue that the entity belongs to.",
    )

    # Try to provide some IDs to choose from
    df = catalogues.get(cat, pd.DataFrame())
    suggested_entity_id: Optional[str] = None

    if not df.empty:
        id_cols = _guess_id_columns(df)
        key_col: Optional[str] = None

        if id_cols:
            key_col = id_cols[0]
        elif "id" in df.columns:
            key_col = "id"

        if key_col:
            st.markdown("#### Optional: Pick an ID from the catalogue")
            # Limit to first 200 unique IDs for usability
            options = (
                df[key_col]
                .dropna()
                .astype(str)
                .drop_duplicates()
                .head(200)
                .tolist()
            )
            if options:
                picked = st.selectbox(
                    f"Choose an ID from `{key_col}` (optional)",
                    options=["(none)"] + options,
                    index=0,
                )
                if picked != "(none)":
                    suggested_entity_id = picked

    # Manual entry (typed) always wins if provided
    entity_id = st.text_input(
        "Entity ID",
        value=suggested_entity_id or "",
        help="Enter the identifier as stored in the relevant CRT catalogue.",
    )

    if not entity_id:
        st.info("Enter an entity ID above or pick one from the dropdown to probe.")
        return

    st.markdown("### 1️⃣ Entity Lookup")

    if not hasattr(sih, "resolve_entity"):
        st.warning("The SIH implementation does not expose `resolve_entity(...)` yet.")
        return

    try:
        entity = sih.resolve_entity(cat, entity_id)  # type: ignore[attr-defined]
    except Exception as exc:  # pylint: disable=broad-except
        st.error(f"Error while resolving entity: {exc}")
        return

    if not entity:
        st.info(f"No entity found in `{cat}` with ID `{entity_id}`.")
        return

    st.json(entity)

    st.markdown("### 2️⃣ Structural Relationships (if available)")

    if not hasattr(sih, "build_relationships"):
        st.info("The SIH implementation does not expose `build_relationships(...)` yet.")
        return

    try:
        relationships = sih.build_relationships(entity)  # type: ignore[attr-defined]
    except Exception as exc:  # pylint: disable=broad-except
        st.error(f"Error while building relationships: {exc}")
        return

    if not relationships:
        st.caption("No structural relationships were returned for this entity.")
    else:
        st.json(relationships)


# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="🔄 System Integrator Hub",
    page_icon="🔄",
    layout="wide",
)

st.title("🔄 System Integrator Hub")
st.caption(
    "Catalogue health, schema visibility, and structural probing via the CRT System Integrator Hub (SIH)."
)

# -------------------------------------------------------------------------------------------------
# Info Panel
# -------------------------------------------------------------------------------------------------
with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "# 🔄 System Integrator Hub\n\n"
            "This module provides a **read-only console** for the System Integrator Hub (SIH). "
            "It allows you to:\n\n"
            "- Verify that backbone and append-only catalogues are loaded\n"
            "- Inspect catalogue schemas and sample rows via SIH\n"
            "- Optionally probe entities and their structural relationships (if supported)\n\n"
            "No catalogue updates are performed here. All append-only changes are made via "
            "📂 Structural Controls & Frameworks. All other modules consume catalogue data "
            "via this hub."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Obtain SIH instance & catalogues
# -------------------------------------------------------------------------------------------------
SIH_INSTANCE = _get_sih_instance()

if SIH_INSTANCE is None:
    st.error(
        "The System Integrator Hub (SIH) runtime could not be initialised. "
        "Ensure `core/sih.py` exposes `get_sih(base_path: str)` and that "
        f"`BASE_CATALOGUE_PATH` exists: `{BASE_CATALOGUE_PATH}`"
    )
    crt_footer()
    st.stop()

CATALOGUES = _load_catalogues_via_sih(SIH_INSTANCE)

# -------------------------------------------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------------------------------------------
st.sidebar.title("📂 Navigation Menu")
st.sidebar.page_link("app.py", label="CRT Portal")
for path, label in build_sidebar_links():
    st.sidebar.page_link(path, label=label)
st.sidebar.divider()
st.logo(BRAND_LOGO_PATH)  # pylint: disable=no-member

st.sidebar.markdown("### 🚀 Getting Started")
st.sidebar.caption(
    "Use the view selector below to switch between SIH perspectives.\n\n"
    "- **Catalogue Health** for a quick status check\n"
    "- **Catalogue Explorer** to inspect a single catalogue\n"
    "- **Entity Probe** to debug a specific item and its relationships"
)

# Sidebar — contextual info
st.sidebar.info(
    """
**🔄 System Integrator Hub**

This module shows:

- Backbone vs append-only catalogue status
- Row counts and schema for all catalogues
- Optional entity-level relationship probing

All data shown is read-only and reflects whatever SIH has loaded from your CRT CSVs.
"""
)

# About & Support
st.sidebar.divider()
with st.sidebar.expander("ℹ️ About & Support"):
    support_md = load_markdown_file(ABOUT_SUPPORT_MD)
    if support_md:
        st.markdown(support_md, unsafe_allow_html=True)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    [
        "📊 Catalogue Health",
        "🗂️ Catalogue Explorer",
        "🧪 Entity & Relationship Probe",
    ],
    index=0,
)

# -------------------------------------------------------------------------------------------------
# Main View Routing
# -------------------------------------------------------------------------------------------------
if view_mode == "📊 Catalogue Health":
    render_view_catalogue_health(CATALOGUES)
elif view_mode == "🗂️ Catalogue Explorer":
    render_view_catalogue_explorer(CATALOGUES)
elif view_mode == "🧪 Entity & Relationship Probe":
    render_view_entity_probe(SIH_INSTANCE, CATALOGUES)
else:
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
