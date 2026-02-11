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
📡 Telemetry & Signal Console — Cyber Resilience Toolkit (CRT)

Read-only structural exploration of CRT-T telemetry sources. This module provides a
structural view of what telemetry sources exist today, how they are described, and
(where recorded) how they map to CRT-C controls.

It is not a telemetry configuration tool. It does not score detection quality,
manage lifecycle state, or provide assurance. It shows what is recorded in CRT-T
and lets you optionally export a normalised `bundle_type = "telemetry"` scope
for downstream CRT modules.

Views provided:

- 📊 Catalogue Overview
  - Tabular view of all telemetry sources with lightweight filters
  - Integrated 📈 Coverage & Metrics (descriptive only)
  - Optional per-source inspection panel

- 📦 Optional Telemetry Scope for Tasks
  - Optional, export-only `bundle_type = "telemetry"` context bundle
  - Supports single source, multi-source cluster, and segment scope
  - Download as JSON and/or save to the lens shelf

Lens reuse, curation, templates, and AI handoff are handled exclusively
by 🧠 AI Observation Console.
"""

from __future__ import annotations

# -------------------------------------------------------------------------------------------------
# Standard Library
# -------------------------------------------------------------------------------------------------
import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Any

# -------------------------------------------------------------------------------------------------
# Third-party Libraries
# -------------------------------------------------------------------------------------------------
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------------------------------------
# Core Utilities
# -------------------------------------------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))

from core.helpers import (  # pylint: disable=import-error
    get_named_paths,
    load_markdown_file,
    build_sidebar_links,
)

# Optional bundle pretty-printer (fallback to json.dumps if unavailable)
try:  # pylint: disable=wrong-import-position
    from core.bundle_builder import bundle_to_pretty_json  # type: ignore
except Exception:  # pylint: disable=broad-except, wrong-import-position
    bundle_to_pretty_json = None  # type: ignore

# Optional SIH integration (preferred) — fall back to CSV if not available
try:  # pylint: disable=wrong-import-position
    from core.sih import get_sih  # type: ignore
except Exception:  # pylint: disable=broad-except
    get_sih = None  # type: ignore


# -------------------------------------------------------------------------------------------------
# Resolve Key Paths (for modules under /pages)
# -------------------------------------------------------------------------------------------------
PATHS = get_named_paths(__file__)
PROJECT_PATH = PATHS["level_up_1"]

BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# Optional docs (defensive load)
ABOUT_APP_MD = os.path.join(PROJECT_PATH, "docs", "about_telemetry_signal_console.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")
HELP_VIEW_OVERVIEW_MD = os.path.join(PROJECT_PATH, "docs", "help_telemetry_overview.md")
HELP_VIEW_SCOPE_MD = os.path.join(PROJECT_PATH, "docs", "help_telemetry_scope.md")

# CRT catalogue locations — used only as a fallback if SIH is not available
CATALOGUE_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "crt_catalogues")
CRT_T_CSV = os.path.join(CATALOGUE_DIR, "CRT-T.csv")
CRT_C_CSV = os.path.join(CATALOGUE_DIR, "CRT-C.csv")

# Lens shelf (persisted JSON bundles)
TSC_LENS_SHELF_DIR = os.path.join(
    PROJECT_PATH,
    "apps",
    "data_sources",
    "crt_workspace",
    "lenses",
    "tsc",
    "bundles",
)


# -------------------------------------------------------------------------------------------------
# Generic helpers (aligned with SCES / DCR / ASM / IAL)
# -------------------------------------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")


def _safe_filename(text: str) -> str:
    cleaned: List[str] = []
    for ch in (text or "").strip():
        if ch.isalnum() or ch in ("-", "_"):
            cleaned.append(ch)
        elif ch in (" ", ".", ":", "/"):
            cleaned.append("-")
    out = "".join(cleaned).strip("-")
    return out[:80] if out else "telemetry-scope"


def _save_json_file(path: str, payload: Dict[str, Any]) -> bool:
    try:
        _ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        return True
    except Exception:  # pylint: disable=broad-except
        return False


def render_markdown_file(path: str, fallback: str) -> None:
    content: Optional[str] = load_markdown_file(path)
    if content:
        st.markdown(content, unsafe_allow_html=True)
    else:
        st.markdown(fallback)


def crt_footer() -> None:
    st.divider()
    st.caption(
        "© Blake Media Ltd. | Cyber Resilience Toolkit by Blake Wiltshire — "
        "All content is structural and conceptual; no configuration, advice, or assurance is provided."
    )


# -------------------------------------------------------------------------------------------------
# Data loading (read-only)
# -------------------------------------------------------------------------------------------------
def _safe_read_csv(path: str) -> pd.DataFrame:
    try:
        if not os.path.isfile(path):
            return pd.DataFrame()
        return pd.read_csv(path)
    except Exception:  # pylint: disable=broad-except
        return pd.DataFrame()


def _load_crt_catalogues() -> Dict[str, pd.DataFrame]:
    """
    Load CRT-T and CRT-C catalogues in a read-only manner.

    Preferred path is via SIH; fallback reads CSV directly.
    """
    if get_sih is not None:
        try:
            sih = get_sih()
            return {
                "CRT-T": sih.get_catalogue("CRT-T"),
                "CRT-C": sih.get_catalogue("CRT-C"),
            }
        except Exception:  # pylint: disable=broad-except
            pass

    return {
        "CRT-T": _safe_read_csv(CRT_T_CSV),
        "CRT-C": _safe_read_csv(CRT_C_CSV),
    }


def _first_present_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _split_semicolon_list(value: object) -> List[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    s = str(value).strip()
    if not s:
        return []
    parts = [p.strip() for p in s.replace(",", ";").split(";")]
    return [p for p in parts if p]


# -------------------------------------------------------------------------------------------------
# View preparation
# -------------------------------------------------------------------------------------------------
def _prepare_view(df_t: pd.DataFrame, df_c: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    if df_t.empty:
        return pd.DataFrame(), {}

    df_view = df_t.copy()

    telemetry_id_col = _first_present_column(df_view, ["telemetry_id", "t_id", "id"])
    name_col = _first_present_column(df_view, ["source_name", "name"])
    channel_col = _first_present_column(df_view, ["channel"])
    signal_class_col = _first_present_column(df_view, ["signal_class", "class"])
    retention_col = _first_present_column(df_view, ["retention_days", "retention"])
    parsing_col = _first_present_column(df_view, ["parsing_status", "parsing"])
    zones_col = _first_present_column(df_view, ["linked_zones", "zones"])
    enrichment_col = _first_present_column(df_view, ["enrichment_ready", "enrichment"])
    notes_col = _first_present_column(df_view, ["notes", "description"])
    source_ref_col = _first_present_column(df_view, ["source_ref", "source_reference", "source"])
    mapped_controls_col = _first_present_column(df_view, ["mapped_control_ids", "mapped_controls", "control_ids"])

    if mapped_controls_col:
        df_view["mapped_control_count"] = df_view[mapped_controls_col].apply(lambda v: len(_split_semicolon_list(v)))
    else:
        df_view["mapped_control_count"] = 0

    # Optional: resolve CRT-C control names for inspection convenience
    if mapped_controls_col and not df_c.empty and "control_id" in df_c.columns:
        df_c_lookup = (
            df_c[["control_id", "control_name"]].copy()
            if "control_name" in df_c.columns
            else df_c[["control_id"]].copy()
        )
        if "control_name" not in df_c_lookup.columns:
            df_c_lookup["control_name"] = ""
        df_c_lookup["control_id"] = df_c_lookup["control_id"].astype(str)

        def _resolve_controls(raw: object) -> str:
            ids = _split_semicolon_list(raw)
            if not ids:
                return ""
            names: List[str] = []
            for cid in sorted(set(ids)):
                row = df_c_lookup[df_c_lookup["control_id"] == str(cid)]
                label = None
                if not row.empty:
                    label = row["control_name"].iloc[0] if "control_name" in row.columns else None
                names.append(f"{cid} — {label}" if label else str(cid))
            return "; ".join(names)

        df_view["linked_control_summary"] = df_view[mapped_controls_col].apply(_resolve_controls)
    else:
        df_view["linked_control_summary"] = ""

    colmap: Dict[str, Optional[str]] = {
        "id_col": telemetry_id_col,
        "name_col": name_col,
        "channel_col": channel_col,
        "signal_class_col": signal_class_col,
        "retention_col": retention_col,
        "parsing_col": parsing_col,
        "zones_col": zones_col,
        "enrichment_col": enrichment_col,
        "notes_col": notes_col,
        "source_ref_col": source_ref_col,
        "mapped_controls_col": mapped_controls_col,
    }
    return df_view, colmap


def _build_telemetry_label(row: pd.Series, colmap: Dict[str, Optional[str]]) -> str:
    id_col = colmap.get("id_col")
    name_col = colmap.get("name_col")
    channel_col = colmap.get("channel_col")

    parts: List[str] = []
    if id_col and id_col in row.index and pd.notna(row.get(id_col)):
        parts.append(str(row[id_col]))
    if name_col and name_col in row.index and pd.notna(row.get(name_col)):
        parts.append(f"— {row[name_col]}")
    if channel_col and channel_col in row.index and pd.notna(row.get(channel_col)):
        parts.append(f"({row[channel_col]})")

    out = " ".join(parts).strip()
    return out if out else "Unlabelled telemetry source"


def _compute_coverage(df_scope: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> Dict[str, int]:
    if df_scope.empty:
        return {
            "total_sources_in_scope": 0,
            "distinct_channels_in_scope": 0,
            "distinct_signal_classes_in_scope": 0,
            "sources_with_mapped_controls_in_scope": 0,
            "distinct_parsing_status_in_scope": 0,
        }

    channel_col = colmap.get("channel_col")
    signal_class_col = colmap.get("signal_class_col")
    parsing_col = colmap.get("parsing_col")
    mapped_controls_col = colmap.get("mapped_controls_col")

    total_sources = len(df_scope)

    channel_count = (
        df_scope[channel_col].dropna().astype(str).nunique()
        if channel_col and channel_col in df_scope.columns
        else 0
    )
    class_count = (
        df_scope[signal_class_col].dropna().astype(str).nunique()
        if signal_class_col and signal_class_col in df_scope.columns
        else 0
    )
    parsing_count = (
        df_scope[parsing_col].dropna().astype(str).nunique()
        if parsing_col and parsing_col in df_scope.columns
        else 0
    )

    if mapped_controls_col and mapped_controls_col in df_scope.columns:
        def _has_controls(val: object) -> bool:
            return len(_split_semicolon_list(val)) > 0

        with_controls = int(df_scope[mapped_controls_col].apply(_has_controls).sum())
    else:
        with_controls = 0

    return {
        "total_sources_in_scope": int(total_sources),
        "distinct_channels_in_scope": int(channel_count),
        "distinct_signal_classes_in_scope": int(class_count),
        "sources_with_mapped_controls_in_scope": int(with_controls),
        "distinct_parsing_status_in_scope": int(parsing_count),
    }


def _row_to_telemetry_entity(row: pd.Series, colmap: Dict[str, Optional[str]]) -> Dict[str, Any]:
    id_col = colmap.get("id_col")
    mapped_controls_col = colmap.get("mapped_controls_col")

    entity_id = (
        str(row[id_col])
        if id_col and id_col in row.index and pd.notna(row.get(id_col))
        else _build_telemetry_label(row, colmap)
    )

    entity: Dict[str, Any] = {
        "catalogue": "CRT-T",
        "id": entity_id,
        "raw": row.to_dict(),
    }

    if mapped_controls_col and mapped_controls_col in row.index:
        entity["mapped_controls"] = _split_semicolon_list(row.get(mapped_controls_col))

    return entity


# -------------------------------------------------------------------------------------------------
# View 1 — Catalogue Overview (with inspection)
# -------------------------------------------------------------------------------------------------
def render_view_overview(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📊 Telemetry Catalogue Overview")
    st.markdown(
        """
Use this view to scan the **structure** of CRT-T:

- Which telemetry channels and signal classes are recorded
- How sources distribute across parsing states (where recorded)
- Where mapped CRT-C controls exist (where recorded)

Metrics shown here are **structural and descriptive only**. They do not
score detection quality or provide assurance.
"""
    )

    with st.expander("ℹ️ Help & Guidance — Overview", expanded=False):
        render_markdown_file(
            HELP_VIEW_OVERVIEW_MD,
            fallback=(
                "This overview presents the effective CRT-T catalogue as a table with lightweight filters "
                "and simple descriptive metrics. Use the inspection panel to review a single telemetry source "
                "and any recorded structural control links."
            ),
        )

    if df_view.empty:
        st.warning("No telemetry sources found in CRT-T. Populate CRT-T via the Command Centre.")
        return

    st.markdown("### 📈 Coverage & Metrics (structural, descriptive only)")
    coverage = _compute_coverage(df_view, colmap)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Telemetry Sources", value=coverage["total_sources_in_scope"])
    with m2:
        st.metric("Distinct Channels", value=coverage["distinct_channels_in_scope"])
    with m3:
        st.metric("Distinct Signal Classes", value=coverage["distinct_signal_classes_in_scope"])

    m4, m5, _ = st.columns(3)
    with m4:
        st.metric("Distinct Parsing States", value=coverage["distinct_parsing_status_in_scope"])
    with m5:
        st.metric("Sources with mapped controls (CRT-C)", value=coverage["sources_with_mapped_controls_in_scope"])

    with st.expander("ℹ️ Coverage & Metrics — Detail", expanded=False):
        st.markdown(
            """
These metrics summarise how many telemetry sources exist across channels, signal classes,
and parsing states, and where mapped CRT-C controls appear. They are **purely descriptive**
and do not provide scoring or assurance.
"""
        )

    st.markdown("### 📡 All Telemetry Sources")

    id_col = colmap.get("id_col")
    name_col = colmap.get("name_col")
    channel_col = colmap.get("channel_col")
    signal_class_col = colmap.get("signal_class_col")
    parsing_col = colmap.get("parsing_col")
    zones_col = colmap.get("zones_col")
    enrichment_col = colmap.get("enrichment_col")
    notes_col = colmap.get("notes_col")

    filter_col, table_col = st.columns([1, 3])

    with filter_col:
        st.markdown("#### 🔎 Filters")

        channel_choice = None
        class_choice = None
        parsing_choice = None
        enrichment_choice = None

        if channel_col and channel_col in df_view.columns:
            vals = ["(All channels)"] + sorted(df_view[channel_col].dropna().astype(str).unique().tolist())
            channel_choice = st.selectbox("Channel", vals)

        if signal_class_col and signal_class_col in df_view.columns:
            vals = ["(All signal classes)"] + sorted(df_view[signal_class_col].dropna().astype(str).unique().tolist())
            class_choice = st.selectbox("Signal Class", vals)

        if parsing_col and parsing_col in df_view.columns:
            vals = ["(All parsing states)"] + sorted(df_view[parsing_col].dropna().astype(str).unique().tolist())
            parsing_choice = st.selectbox("Parsing Status", vals)

        if enrichment_col and enrichment_col in df_view.columns:
            vals = ["(Any)"] + sorted(df_view[enrichment_col].dropna().astype(str).unique().tolist())
            enrichment_choice = st.selectbox("Enrichment Ready", vals)

        text_filter = st.text_input("Source name / zones / notes contains", "")
        only_with_mapped_controls = st.checkbox("Only sources with mapped controls (CRT-C)", value=False)

    with table_col:
        df_filtered = df_view.copy()

        if channel_col and channel_choice and channel_choice != "(All channels)":
            df_filtered = df_filtered[df_filtered[channel_col].astype(str) == channel_choice]

        if signal_class_col and class_choice and class_choice != "(All signal classes)":
            df_filtered = df_filtered[df_filtered[signal_class_col].astype(str) == class_choice]

        if parsing_col and parsing_choice and parsing_choice != "(All parsing states)":
            df_filtered = df_filtered[df_filtered[parsing_col].astype(str) == parsing_choice]

        if enrichment_col and enrichment_choice and enrichment_choice != "(Any)":
            df_filtered = df_filtered[df_filtered[enrichment_col].astype(str) == enrichment_choice]

        if text_filter:
            tf = text_filter.lower()
            text_cols: List[str] = []
            for col in (name_col, zones_col, notes_col):
                if col and col in df_filtered.columns:
                    text_cols.append(col)

            if text_cols:
                mask = False
                for col in text_cols:
                    series = df_filtered[col].astype(str).str.lower().str.contains(tf)
                    mask = series if isinstance(mask, bool) else (mask | series)
                if not isinstance(mask, bool):
                    df_filtered = df_filtered[mask]

        if only_with_mapped_controls and "mapped_control_count" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["mapped_control_count"] > 0]

        if df_filtered.empty:
            st.info("No telemetry sources match the selected filters.")
        else:
            cols_to_hide = {"mapped_control_ids", "mapped_control_count", "linked_control_summary"}
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "telemetry_id",
                "source_name",
                "channel",
                "signal_class",
                "retention_days",
                "parsing_status",
                "linked_zones",
                "enrichment_ready",
                "notes",
                "source_ref",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("### 🧬 Inspect a Single Telemetry Source (optional)")

    if df_filtered.empty:
        st.caption("Adjust filters above to enable per-source inspection.")
        return

    if not id_col or id_col not in df_filtered.columns:
        st.warning("No telemetry ID column found (expected `telemetry_id`). Cannot run inspection.")
        return

    df_filtered = df_filtered.reset_index(drop=True)
    labels = [_build_telemetry_label(row, colmap) for _, row in df_filtered.iterrows()]
    inspect_labels = ["(None selected)"] + labels

    selected_label = st.selectbox("Select a telemetry source to inspect", options=inspect_labels, index=0)
    if selected_label == "(None selected)":
        st.caption("Choose a source to see structural details and any mapped control links.")
        return

    idx = labels.index(selected_label)
    entry_row = df_filtered.iloc[[idx]]

    details_col, controls_col = st.columns([2, 2])

    with details_col:
        st.markdown("#### Structural Attributes")

        if id_col in entry_row.columns:
            st.write(f"**Telemetry ID:** {entry_row[id_col].iloc[0]}")
        if name_col and name_col in entry_row.columns:
            st.write(f"**Source Name:** {entry_row[name_col].iloc[0]}")
        if channel_col and channel_col in entry_row.columns:
            st.write(f"**Channel:** {entry_row[channel_col].iloc[0]}")
        if signal_class_col and signal_class_col in entry_row.columns:
            st.write(f"**Signal Class:** {entry_row[signal_class_col].iloc[0]}")
        if colmap.get("retention_col") and colmap["retention_col"] in entry_row.columns:
            st.write(f"**Retention (days):** {entry_row[colmap['retention_col']].iloc[0]}")
        if parsing_col and parsing_col in entry_row.columns:
            st.write(f"**Parsing Status:** {entry_row[parsing_col].iloc[0]}")
        if zones_col and zones_col in entry_row.columns:
            st.write(f"**Linked Zones:** {entry_row[zones_col].iloc[0]}")
        if enrichment_col and enrichment_col in entry_row.columns:
            st.write(f"**Enrichment Ready:** {entry_row[enrichment_col].iloc[0]}")

        if notes_col and notes_col in entry_row.columns:
            val = entry_row[notes_col].iloc[0]
            if pd.notna(val) and str(val).strip():
                st.markdown("**Notes**")
                st.write(str(val))

        src_col = colmap.get("source_ref_col")
        if src_col and src_col in entry_row.columns:
            val = entry_row[src_col].iloc[0]
            if pd.notna(val) and str(val).strip():
                st.markdown("**Source Reference**")
                st.write(str(val))

    with controls_col:
        st.markdown("#### 🧱 Structural Control Links (CRT-C)")

        mapped_controls_col = colmap.get("mapped_controls_col")
        if mapped_controls_col and mapped_controls_col in entry_row.columns:
            raw_links = entry_row[mapped_controls_col].iloc[0]
            summary = entry_row["linked_control_summary"].iloc[0] if "linked_control_summary" in entry_row.columns else ""
            if pd.isna(raw_links) or not str(raw_links).strip():
                st.caption("No mapped CRT-C controls recorded for this telemetry source.")
            else:
                st.markdown("**Mapped controls (CRT-C IDs)**")
                st.code(str(raw_links), language="text")

                if isinstance(summary, str) and summary.strip():
                    st.markdown("**Resolved Control Summary**")
                    st.write(summary)
                else:
                    st.caption("No control names resolved; check `CRT-C.csv` for matching IDs.")
        else:
            st.caption("No `mapped_control_ids` column present in CRT-T.")


# -------------------------------------------------------------------------------------------------
# View 2 — Optional Telemetry Scope for Tasks (export-only)
# -------------------------------------------------------------------------------------------------
def render_view_context_bundles(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📦 Optional Telemetry Scope for Tasks")

    st.markdown(
        """
Most users can **skip this step** and go straight to **🎛 Programmes — Task Builder**.

Use this page only if you want downstream tasks or AI-assisted exploration to focus on a
**specific slice of telemetry** (for example: authentication logs and MFA events, or network
perimeter telemetry).

Whatever you choose here:

- It does **not** configure telemetry or activate collection
- You will see the bundle JSON before exporting it
- Lens maintenance and attachment happens in 🧠 AI Observation Console
"""
    )

    with st.expander("ℹ️ Help & Guidance — Telemetry Scope", expanded=False):
        render_markdown_file(
            HELP_VIEW_SCOPE_MD,
            fallback=(
                "Define a focused telemetry scope when you want exports (or downstream modules) "
                "to reference a subset of CRT-T. This is structural only and export-only."
            ),
        )

    if df_view.empty:
        st.warning("No telemetry sources available — cannot build a context bundle.")
        return

    id_col = colmap.get("id_col")
    if not id_col or id_col not in df_view.columns:
        st.warning("No telemetry ID column found (expected `telemetry_id`). Cannot build a scope bundle.")
        return

    channel_col = colmap.get("channel_col")
    signal_class_col = colmap.get("signal_class_col")
    parsing_col = colmap.get("parsing_col")
    enrichment_col = colmap.get("enrichment_col")
    name_col = colmap.get("name_col")
    zones_col = colmap.get("zones_col")
    notes_col = colmap.get("notes_col")

    st.markdown("### 0️⃣ How should telemetry be handled for this export?")
    scope_activation = st.radio(
        "Choose how to handle telemetry scope:",
        [
            "Don’t define a special telemetry scope (use everything)",
            "Define a focused telemetry scope (optional)",
        ],
        index=0,
        help="If you’re not sure, use the default and come back later.",
    )

    if scope_activation.startswith("Don’t define"):
        st.info(
            "No focused telemetry scope will be built in this view. "
            "You can return later to export a focused scope if needed."
        )
        return

    st.markdown("### 1️⃣ Choose Scope Mode")
    scope_mode = st.radio(
        "Scope mode",
        ["Single telemetry source", "Multi-source cluster", "Segment (filters)"],
        help="Single = one primary source. Cluster = small set. Segment = filter-defined scope.",
    )

    scope_df = pd.DataFrame()
    primary_entity: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}

    st.markdown("### 2️⃣ Select Telemetry Scope")

    # ---------------------------------------------------------------------
    # Single telemetry source (with filters + table, aligned with SCES)
    # ---------------------------------------------------------------------
    if scope_mode == "Single telemetry source":
        fcol, tcol = st.columns([1, 2])

        with fcol:
            channel_choice = None
            class_choice = None
            parsing_choice = None
            enrichment_choice = None

            if channel_col and channel_col in df_view.columns:
                vals = ["(Any channel)"] + sorted(df_view[channel_col].dropna().astype(str).unique().tolist())
                channel_choice = st.selectbox("Channel", vals)

            if signal_class_col and signal_class_col in df_view.columns:
                vals = ["(Any signal class)"] + sorted(df_view[signal_class_col].dropna().astype(str).unique().tolist())
                class_choice = st.selectbox("Signal Class", vals)

            if parsing_col and parsing_col in df_view.columns:
                vals = ["(Any parsing state)"] + sorted(df_view[parsing_col].dropna().astype(str).unique().tolist())
                parsing_choice = st.selectbox("Parsing Status", vals)

            if enrichment_col and enrichment_col in df_view.columns:
                vals = ["(Any)"] + sorted(df_view[enrichment_col].dropna().astype(str).unique().tolist())
                enrichment_choice = st.selectbox("Enrichment Ready", vals)

            text_filter = st.text_input("Source name / zones / notes contains", "")
            only_with_controls = st.checkbox("Only sources with mapped controls (CRT-C)", value=False)

        with tcol:
            df_filtered = df_view.copy()

            if channel_col and channel_choice and channel_choice != "(Any channel)":
                df_filtered = df_filtered[df_filtered[channel_col].astype(str) == channel_choice]
                filters["channel"] = channel_choice

            if signal_class_col and class_choice and class_choice != "(Any signal class)":
                df_filtered = df_filtered[df_filtered[signal_class_col].astype(str) == class_choice]
                filters["signal_class"] = class_choice

            if parsing_col and parsing_choice and parsing_choice != "(Any parsing state)":
                df_filtered = df_filtered[df_filtered[parsing_col].astype(str) == parsing_choice]
                filters["parsing_status"] = parsing_choice

            if enrichment_col and enrichment_choice and enrichment_choice != "(Any)":
                df_filtered = df_filtered[df_filtered[enrichment_col].astype(str) == enrichment_choice]
                filters["enrichment_ready"] = enrichment_choice

            if text_filter:
                tf = text_filter.lower()
                text_cols: List[str] = []
                for col in (name_col, zones_col, notes_col):
                    if col and col in df_filtered.columns:
                        text_cols.append(col)
                if text_cols:
                    mask = False
                    for col in text_cols:
                        series = df_filtered[col].astype(str).str.lower().str.contains(tf)
                        mask = series if isinstance(mask, bool) else (mask | series)
                    if not isinstance(mask, bool):
                        df_filtered = df_filtered[mask]

            if only_with_controls and "mapped_control_count" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["mapped_control_count"] > 0]

            if df_filtered.empty:
                st.info("No telemetry sources match the selected filters.")
                st.stop()

            st.markdown("#### Matching Telemetry Sources")
            cols_to_hide = {"mapped_control_ids", "mapped_control_count", "linked_control_summary"}
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "telemetry_id",
                "source_name",
                "channel",
                "signal_class",
                "retention_days",
                "parsing_status",
                "linked_zones",
                "enrichment_ready",
                "notes",
                "source_ref",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_telemetry_label(row, colmap) for _, row in df_filtered.iterrows()]
        pick = st.selectbox("Telemetry source to use as primary entity", options=labels)
        idx = labels.index(pick)

        scope_df = df_filtered.iloc[[idx]]
        pe_id = str(scope_df[id_col].iloc[0])
        primary_entity = {"type": "telemetry_source", "id": pe_id}

    # ---------------------------------------------------------------------
    # Multi-source cluster (with filters + table, aligned with SCES)
    # ---------------------------------------------------------------------
    elif scope_mode == "Multi-source cluster":
        fcol, tcol = st.columns([1, 2])

        with fcol:
            channel_choice = None
            class_choice = None
            parsing_choice = None

            if channel_col and channel_col in df_view.columns:
                vals = ["(Any channel)"] + sorted(df_view[channel_col].dropna().astype(str).unique().tolist())
                channel_choice = st.selectbox("Channel", vals)

            if signal_class_col and signal_class_col in df_view.columns:
                vals = ["(Any signal class)"] + sorted(df_view[signal_class_col].dropna().astype(str).unique().tolist())
                class_choice = st.selectbox("Signal Class", vals)

            if parsing_col and parsing_col in df_view.columns:
                vals = ["(Any parsing state)"] + sorted(df_view[parsing_col].dropna().astype(str).unique().tolist())
                parsing_choice = st.selectbox("Parsing Status", vals)

            only_with_controls = st.checkbox("Only sources with mapped controls (CRT-C)", value=False)

        with tcol:
            df_filtered = df_view.copy()

            if channel_col and channel_choice and channel_choice != "(Any channel)":
                df_filtered = df_filtered[df_filtered[channel_col].astype(str) == channel_choice]
                filters["channel"] = channel_choice

            if signal_class_col and class_choice and class_choice != "(Any signal class)":
                df_filtered = df_filtered[df_filtered[signal_class_col].astype(str) == class_choice]
                filters["signal_class"] = class_choice

            if parsing_col and parsing_choice and parsing_choice != "(Any parsing state)":
                df_filtered = df_filtered[df_filtered[parsing_col].astype(str) == parsing_choice]
                filters["parsing_status"] = parsing_choice

            if only_with_controls and "mapped_control_count" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["mapped_control_count"] > 0]

            if df_filtered.empty:
                st.info("No telemetry sources match the selected filters.")
                st.stop()

            st.markdown("#### Available Telemetry Sources for Cluster")
            cols_to_hide = {"mapped_control_ids", "mapped_control_count", "linked_control_summary"}
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "telemetry_id",
                "source_name",
                "channel",
                "signal_class",
                "retention_days",
                "parsing_status",
                "linked_zones",
                "enrichment_ready",
                "notes",
                "source_ref",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_telemetry_label(row, colmap) for _, row in df_filtered.iterrows()]
        picks = st.multiselect("Select telemetry sources to include in the cluster", options=labels)

        if not picks:
            st.info("Select at least one source to form a cluster.")
            st.stop()

        indices = [labels.index(lbl) for lbl in picks]
        scope_df = df_filtered.iloc[indices]

        base_ids = sorted(scope_df[id_col].astype(str).tolist())
        cluster_key = ",".join(base_ids)
        cluster_hash = hashlib.sha256(cluster_key.encode("utf-8")).hexdigest()[:8]
        primary_entity = {"type": "telemetry_cluster", "id": f"CRT-T-cluster-{cluster_hash}"}

    # ---------------------------------------------------------------------
    # Segment (filters) — keep as filter-defined, but include preview (aligned)
    # ---------------------------------------------------------------------
    else:
        scope_df = df_view.copy()

        if channel_col and channel_col in scope_df.columns:
            ch = st.selectbox(
                "Channel",
                ["(Any channel)"] + sorted(scope_df[channel_col].dropna().astype(str).unique().tolist()),
            )
            if ch != "(Any channel)":
                scope_df = scope_df[scope_df[channel_col].astype(str) == ch]
                filters["channel"] = ch

        if signal_class_col and signal_class_col in scope_df.columns:
            sc = st.selectbox(
                "Signal Class",
                ["(Any signal class)"] + sorted(scope_df[signal_class_col].dropna().astype(str).unique().tolist()),
            )
            if sc != "(Any signal class)":
                scope_df = scope_df[scope_df[signal_class_col].astype(str) == sc]
                filters["signal_class"] = sc

        if parsing_col and parsing_col in scope_df.columns:
            ps = st.selectbox(
                "Parsing Status",
                ["(Any parsing state)"] + sorted(scope_df[parsing_col].dropna().astype(str).unique().tolist()),
            )
            if ps != "(Any parsing state)":
                scope_df = scope_df[scope_df[parsing_col].astype(str) == ps]
                filters["parsing_status"] = ps

        st.markdown("#### Segment Preview")
        if scope_df.empty:
            st.info("No telemetry sources match this segment definition. The bundle will have an empty telemetry list.")
        else:
            cols_to_hide = {"mapped_control_ids", "mapped_control_count", "linked_control_summary"}
            available_cols = [c for c in scope_df.columns if c not in cols_to_hide]
            st.dataframe(scope_df[available_cols], width="stretch", hide_index=True)

        filter_str = json.dumps(filters, sort_keys=True) if filters else "all"
        seg_hash = hashlib.sha256(filter_str.encode("utf-8")).hexdigest()[:8]
        primary_entity = {"type": "telemetry_segment", "id": f"CRT-T-segment-{seg_hash}", "filters": filters}

    if scope_df is None or primary_entity == {}:
        st.warning("Unable to determine scope or primary entity — please review selections.")
        return

    st.markdown("### 3️⃣ Bundle Summary")
    coverage = _compute_coverage(scope_df, colmap)
    st.write(
        f"- **Scope mode:** `{scope_mode}`  \n"
        f"- **Sources in scope:** `{coverage['total_sources_in_scope']}`  \n"
        f"- **Primary entity:** `{primary_entity.get('type')}` → `{primary_entity.get('id')}`"
    )

    telemetry_entities = [_row_to_telemetry_entity(row, colmap) for _, row in scope_df.iterrows()]

    bundle: Dict[str, Any] = {
        "bundle_type": "telemetry",
        "module": "📡 Telemetry & Signal Console",
        "primary_entity": primary_entity,
        "entities": {
            "assets": [],
            "identities": [],
            "data_domains": [],
            "vendors": [],
            "controls": [],
            "failures": [],
            "telemetry": telemetry_entities,
        },
        "relationships": [],
        "structural_findings": {
            "gaps": [],
            "compensations": [],
            "coverage": coverage,
            "dependency_paths": [],
        },
        "guardrails": {
            "no_advice": True,
            "no_configuration": True,
            "no_assurance": True,
        },
        "lens_meta": {
            "built_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "source": "module",
            "persisted_to_disk": False,
            "shelf_path_hint": None,
        },
    }

    # -------------------------------------------------------------------------------------------------
    # Export — Download or Save (Platinum / Minimal)  ✅ aligned with SCES
    # -------------------------------------------------------------------------------------------------
    st.markdown("### 4️⃣ Export Bundle (JSON)")

    if bundle_to_pretty_json:
        pretty = bundle_to_pretty_json(bundle)  # type: ignore[arg-type]
    else:
        pretty = json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False)

    st.code(pretty, language="json")

    a, b = st.columns([1, 1])

    with a:
        st.download_button(
            "⬇️ Download bundle (JSON)",
            data=pretty.encode("utf-8"),
            file_name="tsc_telemetry_bundle.json",
            mime="application/json",
            use_container_width=True,
        )

    with b:
        if st.button("💾 Save to lens shelf", use_container_width=True):
            _ensure_dir(TSC_LENS_SHELF_DIR)

            pe = primary_entity if isinstance(primary_entity, dict) else {}
            pe_id = pe.get("id") if isinstance(pe, dict) else None

            name_hint = _safe_filename(str(pe_id)) if pe_id else "telemetry-scope"
            filename = f"tsc_{name_hint}_{_utc_stamp()}.json"
            path = os.path.join(TSC_LENS_SHELF_DIR, filename)

            bundle.setdefault("lens_meta", {})
            bundle["lens_meta"]["persisted_to_disk"] = True
            bundle["lens_meta"]["shelf_path_hint"] = f"lenses/tsc/bundles/{filename}"

            ok = _save_json_file(path, bundle)
            if ok:
                st.success(f"Saved to lens shelf: {filename}")
                st.caption("Lens maintenance and attachment happens in 🧠 AI Observation Console.")
            else:
                st.error("Could not save to the lens shelf.")

    st.caption(
        "This lens is **export-only**. It does not configure telemetry, score detection quality, "
        "or provide assurance. Review, attach, combine, or retire lenses in 🧠 AI Observation Console."
    )


# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Telemetry & Signal Console",
    page_icon="📡",
    layout="wide",
)

st.title("📡 Telemetry & Signal Console")
st.caption(
    "Explore telemetry sources, signal classes, and structural control mappings — "
    "read-only exploration of your CRT-T telemetry model."
)

# -------------------------------------------------------------------------------------------------
# Info Panel
# -------------------------------------------------------------------------------------------------
with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "# 📡 Telemetry & Signal Console\n\n"
            "This module surfaces the **effective CRT-T catalogue** in a structured, "
            "non-prescriptive way. It allows you to:\n\n"
            "- Explore telemetry channels and signal classes\n"
            "- Inspect parsing states, zones, and enrichment flags (where recorded)\n"
            "- View structural links to CRT-C controls (where recorded)\n"
            "- Export a normalised `bundle_type = \"telemetry\"` scope bundle (optional)\n\n"
            "It does **not** configure telemetry, score detection quality, or provide assurance."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Load Catalogues
# -------------------------------------------------------------------------------------------------
CATALOGUES = _load_crt_catalogues()
DF_T = CATALOGUES.get("CRT-T", pd.DataFrame())
DF_C = CATALOGUES.get("CRT-C", pd.DataFrame())
DF_VIEW, COLMAP = _prepare_view(DF_T, DF_C)

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
    "Use the view selector below to switch between perspectives within the "
    "Telemetry & Signal Console."
)

st.sidebar.info(
    """
**📡 Telemetry & Signal Console**

Use this module to:

- Examine how telemetry sources are structured in CRT-T
- View channels, signal classes, parsing states, and zones (where recorded)
- Inspect structural links to CRT-C controls (where defined)
- (Optionally) export a normalised `bundle_type = "telemetry"` scope lens

All views are read-only. Catalogue updates and append operations are handled exclusively
via the 📂 Structural Controls & Frameworks — Command Centre and 🛰 Org-Specific Catalogues.
"""
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    [
        "📊 Catalogue Overview",
        "📦 Optional Telemetry Scope for Tasks",
    ],
    index=0,
)

st.sidebar.divider()
with st.sidebar.expander("ℹ️ About & Support"):
    support_md = load_markdown_file(ABOUT_SUPPORT_MD)
    if support_md:
        st.markdown(support_md, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------
# Main View Routing
# -------------------------------------------------------------------------------------------------
if view_mode == "📊 Catalogue Overview":
    render_view_overview(DF_VIEW, COLMAP)
elif view_mode == "📦 Optional Telemetry Scope for Tasks":
    render_view_context_bundles(DF_VIEW, COLMAP)
else:
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
