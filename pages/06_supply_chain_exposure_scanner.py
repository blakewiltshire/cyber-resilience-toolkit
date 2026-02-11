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
🛰 Supply-Chain Exposure Scanner — Cyber Resilience Toolkit (CRT)

Explore vendor and supply-chain dependencies, service types, criticality
tiers, and structural control mappings. This module provides a structural,
read-only view of how supply-chain entries relate to CRT controls.

It is not a risk engine or assessment tool. It shows **what is recorded today**
in CRT-SC and lets you optionally export a normalised
`bundle_type = "supply_chain"` scope for downstream CRT modules.

Views provided:

- 📊 Catalogue Overview
  - Tabular view of all supply-chain entries with lightweight filters
  - Integrated 📈 Coverage & Metrics (descriptive only)
  - Optional per-entry inspection panel

- 📦 Optional Supply-Chain Scope for Tasks
  - Optional, export-only `bundle_type = "supply_chain"` context bundle
  - Supports single entry, multi-entry cluster, and segment scope
  - Download as JSON and/or save to the lens shelf
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
# Ensure we can import from the project root / core / apps when running from /pages
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

ABOUT_APP_MD = os.path.join(PROJECT_PATH, "docs", "about_supply_chain_exposure_scanner.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")

# Optional per-view help docs
HELP_VIEW_OVERVIEW_MD = os.path.join(PROJECT_PATH, "docs", "help_supply_chain_overview.md")
HELP_VIEW_SCOPE_MD = os.path.join(PROJECT_PATH, "docs", "help_supply_chain_scope.md")

BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# CRT catalogue locations — used only as a fallback if SIH is not available
CATALOGUE_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "crt_catalogues")
CRT_SC_CSV = os.path.join(CATALOGUE_DIR, "CRT-SC.csv")  # Supply-chain catalogue
CRT_C_CSV = os.path.join(CATALOGUE_DIR, "CRT-C.csv")    # Controls catalogue (for summaries)

# Lens shelf (persisted JSON bundles)
SCES_LENS_SHELF_DIR = os.path.join(
    PROJECT_PATH,
    "apps",
    "data_sources",
    "crt_workspace",
    "lenses",
    "sces",
    "bundles",
)

# -------------------------------------------------------------------------------------------------
# Generic helpers (aligned with DCR / ASM)
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
    return out[:80] if out else "lens"


def _save_json_file(path: str, payload: Dict[str, Any]) -> bool:
    try:
        _ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        return True
    except Exception:  # pylint: disable=broad-except
        return False


# -------------------------------------------------------------------------------------------------
# Small helper for safe markdown loading
# -------------------------------------------------------------------------------------------------
def render_markdown_file(path: str, fallback: str) -> None:
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
# Data Loading Helpers (read-only)
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
    Load CRT-SC and CRT-C catalogues in a read-only manner.

    Preferred path is via SIH; fallback reads CSV directly.
    """
    if get_sih is not None:
        try:
            sih = get_sih()
            return {
                "CRT-SC": sih.get_catalogue("CRT-SC"),
                "CRT-C": sih.get_catalogue("CRT-C"),
            }
        except Exception:  # pylint: disable=broad-except
            pass

    return {
        "CRT-SC": _safe_read_csv(CRT_SC_CSV),
        "CRT-C": _safe_read_csv(CRT_C_CSV),
    }


def _first_present_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _split_semicolon_list(value: str) -> List[str]:
    if not isinstance(value, str):
        return []
    parts = [p.strip() for p in value.split(";")]
    return [p for p in parts if p]


# -------------------------------------------------------------------------------------------------
# View Preparation
# -------------------------------------------------------------------------------------------------
def _prepare_view(df_sc: pd.DataFrame, df_c: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    if df_sc.empty:
        return pd.DataFrame(), {}

    df_view = df_sc.copy()

    # Typical CRT-SC fields (varies by org):
    # vendor_id, vendor_name, service_type, dependency_type, criticality, contract_tier,
    # data_access_level, vendor_archetype, example_vendors, notes, source_ref, mapped_control_ids
    id_col = _first_present_column(df_view, ["vendor_id", "sc_id", "id"])
    name_col = _first_present_column(df_view, ["vendor_name", "name", "provider_name", "label"])
    service_type_col = _first_present_column(df_view, ["service_type", "vendor_service_type", "service"])
    dependency_type_col = _first_present_column(df_view, ["dependency_type", "relationship_type", "dependency"])
    criticality_col = _first_present_column(df_view, ["criticality", "tier", "impact_tier"])
    contract_tier_col = _first_present_column(df_view, ["contract_tier", "contract_level", "engagement_tier"])
    data_access_level_col = _first_present_column(df_view, ["data_access_level", "data_access", "access_level"])
    vendor_archetype_col = _first_present_column(df_view, ["vendor_archetype", "vendor_type", "provider_type"])
    example_vendors_col = _first_present_column(df_view, ["example_vendors", "examples", "sample_vendors"])
    notes_col = _first_present_column(df_view, ["notes", "description", "summary"])
    source_ref_col = _first_present_column(df_view, ["source_ref", "source", "origin"])

    linked_controls_col = _first_present_column(df_view, ["mapped_control_ids", "linked_controls"])

    # Derived: mapped control count
    if linked_controls_col:
        def _count_controls(raw: object) -> int:
            if pd.isna(raw):
                return 0
            parts = str(raw).replace(";", ",").split(",")
            parts = [p.strip() for p in parts if p.strip()]
            return len(set(parts))

        df_view["mapped_control_count"] = df_view[linked_controls_col].apply(_count_controls)
    else:
        df_view["mapped_control_count"] = 0

    # Optional: join CRT-C to show summary of linked control names
    if linked_controls_col and not df_c.empty and "control_id" in df_c.columns:
        df_c_lookup = df_c[["control_id", "control_name"]].copy() if "control_name" in df_c.columns else df_c[["control_id"]].copy()
        if "control_name" not in df_c_lookup.columns:
            df_c_lookup["control_name"] = ""
        df_c_lookup["control_id"] = df_c_lookup["control_id"].astype(str)

        def _resolve_controls(raw: object) -> str:
            if pd.isna(raw):
                return ""
            parts = str(raw).replace(";", ",").split(",")
            parts = [p.strip() for p in parts if p.strip()]
            ids = sorted(set(parts))
            names: List[str] = []
            for cid in ids:
                row = df_c_lookup[df_c_lookup["control_id"] == cid]
                label = None
                if not row.empty:
                    label = row["control_name"].iloc[0] if "control_name" in row.columns else None
                names.append(f"{cid} — {label}" if label else cid)
            return "; ".join(names)

        df_view["linked_control_summary"] = df_view[linked_controls_col].apply(_resolve_controls)
    else:
        df_view["linked_control_summary"] = ""

    colmap: Dict[str, Optional[str]] = {
        "id_col": id_col,
        "name_col": name_col,
        "service_type_col": service_type_col,
        "dependency_type_col": dependency_type_col,
        "criticality_col": criticality_col,
        "contract_tier_col": contract_tier_col,
        "data_access_level_col": data_access_level_col,
        "vendor_archetype_col": vendor_archetype_col,
        "example_vendors_col": example_vendors_col,
        "notes_col": notes_col,
        "source_ref_col": source_ref_col,
        "linked_controls_col": linked_controls_col,
    }
    return df_view, colmap


def _build_supply_label(row: pd.Series, colmap: Dict[str, Optional[str]]) -> str:
    name_col = colmap.get("name_col")
    service_type_col = colmap.get("service_type_col")
    criticality_col = colmap.get("criticality_col")

    parts: List[str] = []
    if name_col and name_col in row.index and pd.notna(row.get(name_col)):
        parts.append(str(row[name_col]))
    if service_type_col and service_type_col in row.index and pd.notna(row.get(service_type_col)):
        parts.append(f"({row[service_type_col]})")
    if criticality_col and criticality_col in row.index and pd.notna(row.get(criticality_col)):
        parts.append(f"[criticality={row[criticality_col]}]")

    return " ".join(parts) if parts else "Unlabelled supply-chain entry"


def _detect_id_column(df_view: pd.DataFrame) -> Optional[str]:
    return _first_present_column(df_view, ["vendor_id", "sc_id", "id"])


def _row_to_vendor_entity(row: pd.Series, colmap: Dict[str, Optional[str]], id_col: Optional[str]) -> Dict[str, object]:
    if id_col and id_col in row.index and pd.notna(row[id_col]):
        entity_id = str(row[id_col])
    else:
        entity_id = _build_supply_label(row, colmap) or f"row-{row.name}"

    service_type_col = colmap.get("service_type_col")
    dependency_type_col = colmap.get("dependency_type_col")
    criticality_col = colmap.get("criticality_col")
    contract_tier_col = colmap.get("contract_tier_col")
    data_access_level_col = colmap.get("data_access_level_col")
    vendor_archetype_col = colmap.get("vendor_archetype_col")
    example_vendors_col = colmap.get("example_vendors_col")
    notes_col = colmap.get("notes_col")
    source_ref_col = colmap.get("source_ref_col")
    linked_controls_col = colmap.get("linked_controls_col")

    entity: Dict[str, object] = {
        "catalogue": "CRT-SC",
        "id": entity_id,
        "raw": row.to_dict(),
    }

    if service_type_col and service_type_col in row.index:
        entity["service_type"] = row[service_type_col]
    if dependency_type_col and dependency_type_col in row.index:
        entity["dependency_type"] = row[dependency_type_col]
    if criticality_col and criticality_col in row.index:
        entity["criticality"] = row[criticality_col]
    if contract_tier_col and contract_tier_col in row.index:
        entity["contract_tier"] = row[contract_tier_col]
    if data_access_level_col and data_access_level_col in row.index:
        entity["data_access_level"] = row[data_access_level_col]
    if vendor_archetype_col and vendor_archetype_col in row.index:
        entity["vendor_archetype"] = row[vendor_archetype_col]
    if example_vendors_col and example_vendors_col in row.index:
        entity["example_vendors"] = row[example_vendors_col]
    if notes_col and notes_col in row.index:
        entity["notes"] = row[notes_col]
    if source_ref_col and source_ref_col in row.index:
        entity["source_ref"] = row[source_ref_col]

    if linked_controls_col and linked_controls_col in row.index:
        entity["mapped_controls"] = _split_semicolon_list(str(row.get(linked_controls_col, "")))

    return entity


def _compute_coverage(df_scope: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> Dict[str, int]:
    if df_scope.empty:
        return {
            "total_entries_in_scope": 0,
            "distinct_service_types_in_scope": 0,
            "distinct_dependency_types_in_scope": 0,
            "distinct_contract_tiers_in_scope": 0,
            "entries_with_mapped_controls_in_scope": 0,
            "distinct_criticalities_in_scope": 0,
        }

    service_type_col = colmap.get("service_type_col")
    dependency_type_col = colmap.get("dependency_type_col")
    contract_tier_col = colmap.get("contract_tier_col")
    criticality_col = colmap.get("criticality_col")
    linked_controls_col = colmap.get("linked_controls_col")

    total_entries = len(df_scope)

    svc_count = df_scope[service_type_col].dropna().astype(str).nunique() if service_type_col and service_type_col in df_scope.columns else 0
    dep_count = df_scope[dependency_type_col].dropna().astype(str).nunique() if dependency_type_col and dependency_type_col in df_scope.columns else 0
    contract_count = df_scope[contract_tier_col].dropna().astype(str).nunique() if contract_tier_col and contract_tier_col in df_scope.columns else 0
    crit_count = df_scope[criticality_col].dropna().astype(str).nunique() if criticality_col and criticality_col in df_scope.columns else 0

    if linked_controls_col and linked_controls_col in df_scope.columns:
        def _has_controls(val: object) -> bool:
            if pd.isna(val):
                return False
            s = str(val).strip()
            if not s:
                return False
            parts = [p.strip() for p in s.replace(";", ",").split(",")]
            return any(parts)

        with_controls = int(df_scope[linked_controls_col].apply(_has_controls).sum())
    else:
        with_controls = 0

    return {
        "total_entries_in_scope": int(total_entries),
        "distinct_service_types_in_scope": int(svc_count),
        "distinct_dependency_types_in_scope": int(dep_count),
        "distinct_contract_tiers_in_scope": int(contract_count),
        "entries_with_mapped_controls_in_scope": int(with_controls),
        "distinct_criticalities_in_scope": int(crit_count),
    }


# -------------------------------------------------------------------------------------------------
# View 1 — Catalogue Overview (with inspection)
# -------------------------------------------------------------------------------------------------
def render_view_overview(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📊 Supply-Chain Catalogue Overview")
    st.markdown(
        """
Use this view to scan the **structure** of your supply-chain model:

- Which service and dependency types exist
- How entries are distributed across contract tiers and criticality
- How many entries have mapped CRT-C controls

Metrics shown here are **structural and descriptive only**. They do not
score vendor risk or provide assurance.
"""
    )

    with st.expander("ℹ️ Help & Guidance — Overview", expanded=False):
        render_markdown_file(
            HELP_VIEW_OVERVIEW_MD,
            fallback=(
                "This overview presents the effective CRT-SC catalogue as a table with lightweight filters "
                "and simple descriptive metrics. Use the inspection panel to review a single entry "
                "and any recorded structural control links."
            ),
        )

    if df_view.empty:
        st.warning("No supply-chain entries found in CRT-SC. Populate CRT-SC via the Command Centre.")
        return

    st.markdown("### 📈 Coverage & Metrics (structural, descriptive only)")
    coverage = _compute_coverage(df_view, colmap)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Supply-Chain Entries", value=coverage["total_entries_in_scope"])
    with m2:
        st.metric("Distinct Service Types", value=coverage["distinct_service_types_in_scope"])
    with m3:
        st.metric("Distinct Dependency Types", value=coverage["distinct_dependency_types_in_scope"])

    m4, m5, m6 = st.columns(3)
    with m4:
        st.metric("Distinct Contract Tiers", value=coverage["distinct_contract_tiers_in_scope"])
    with m5:
        st.metric("Distinct Criticalities", value=coverage["distinct_criticalities_in_scope"])
    with m6:
        st.metric("Entries with mapped controls (CRT-C)", value=coverage["entries_with_mapped_controls_in_scope"])

    with st.expander("ℹ️ Coverage & Metrics — Detail", expanded=False):
        st.markdown(
            """
These metrics summarise how many entries exist across service types, dependency types,
contract tiers, and criticality, and where mapped CRT-C controls appear. They are **purely
descriptive** and do not provide scoring or assurance.
"""
        )

    st.markdown("### 🧾 All Supply-Chain Entries")

    service_type_col = colmap.get("service_type_col")
    dependency_type_col = colmap.get("dependency_type_col")
    criticality_col = colmap.get("criticality_col")
    contract_tier_col = colmap.get("contract_tier_col")
    data_access_level_col = colmap.get("data_access_level_col")
    vendor_archetype_col = colmap.get("vendor_archetype_col")
    example_vendors_col = colmap.get("example_vendors_col")
    notes_col = colmap.get("notes_col")

    filter_col, table_col = st.columns([1, 3])

    with filter_col:
        st.markdown("#### 🔎 Filters")

        svc_choice = None
        dep_choice = None
        crit_choice = None
        contract_choice = None
        access_choice = None

        if service_type_col and service_type_col in df_view.columns:
            vals = ["(All service types)"] + sorted(df_view[service_type_col].dropna().astype(str).unique().tolist())
            svc_choice = st.selectbox("Service Type", vals)

        if dependency_type_col and dependency_type_col in df_view.columns:
            vals = ["(All dependency types)"] + sorted(df_view[dependency_type_col].dropna().astype(str).unique().tolist())
            dep_choice = st.selectbox("Dependency Type", vals)

        if criticality_col and criticality_col in df_view.columns:
            vals = ["(All criticalities)"] + sorted(df_view[criticality_col].dropna().astype(str).unique().tolist())
            crit_choice = st.selectbox("Criticality", vals)

        if contract_tier_col and contract_tier_col in df_view.columns:
            vals = ["(All contract tiers)"] + sorted(df_view[contract_tier_col].dropna().astype(str).unique().tolist())
            contract_choice = st.selectbox("Contract Tier", vals)

        if data_access_level_col and data_access_level_col in df_view.columns:
            vals = ["(All access levels)"] + sorted(df_view[data_access_level_col].dropna().astype(str).unique().tolist())
            access_choice = st.selectbox("Data Access Level", vals)

        text_filter = st.text_input("Notes / archetype / examples contain", "")
        only_with_controls = st.checkbox("Only entries with mapped controls (CRT-C)", value=False)

    with table_col:
        df_filtered = df_view.copy()

        if service_type_col and svc_choice and svc_choice != "(All service types)":
            df_filtered = df_filtered[df_filtered[service_type_col].astype(str) == svc_choice]

        if dependency_type_col and dep_choice and dep_choice != "(All dependency types)":
            df_filtered = df_filtered[df_filtered[dependency_type_col].astype(str) == dep_choice]

        if criticality_col and crit_choice and crit_choice != "(All criticalities)":
            df_filtered = df_filtered[df_filtered[criticality_col].astype(str) == crit_choice]

        if contract_tier_col and contract_choice and contract_choice != "(All contract tiers)":
            df_filtered = df_filtered[df_filtered[contract_tier_col].astype(str) == contract_choice]

        if data_access_level_col and access_choice and access_choice != "(All access levels)":
            df_filtered = df_filtered[df_filtered[data_access_level_col].astype(str) == access_choice]

        if text_filter:
            tf = text_filter.lower()
            text_cols: List[str] = []
            for col in (notes_col, vendor_archetype_col, example_vendors_col):
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
            st.info("No supply-chain entries match the selected filters.")
        else:
            cols_to_hide = {
                "mapped_control_ids",
                "mapped_control_count",
                "linked_control_summary",
            }
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "vendor_id",
                "vendor_name",
                "service_type",
                "dependency_type",
                "criticality",
                "contract_tier",
                "data_access_level",
                "vendor_archetype",
                "example_vendors",
                "notes",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("### 🧬 Inspect a Single Supply-Chain Entry (optional)")

    if df_filtered.empty:
        st.caption("Adjust filters above to enable per-entry inspection.")
        return

    df_filtered = df_filtered.reset_index(drop=True)
    labels = [_build_supply_label(row, colmap) for _, row in df_filtered.iterrows()]
    inspect_labels = ["(None selected)"] + labels

    selected_label = st.selectbox("Select an entry to inspect", options=inspect_labels, index=0)
    if selected_label == "(None selected)":
        st.caption("Choose an entry to see structural details and mapped controls.")
        return

    idx = labels.index(selected_label)
    entry_row = df_filtered.iloc[[idx]]

    linked_controls_col = colmap.get("linked_controls_col")
    name_col = colmap.get("name_col")

    details_col, controls_col = st.columns([2, 2])

    with details_col:
        st.markdown("#### Structural Attributes")

        if name_col and name_col in entry_row.columns:
            st.write(f"**Name:** {entry_row[name_col].iloc[0]}")
        if service_type_col and service_type_col in entry_row.columns:
            st.write(f"**Service Type:** {entry_row[service_type_col].iloc[0]}")
        if dependency_type_col and dependency_type_col in entry_row.columns:
            st.write(f"**Dependency Type:** {entry_row[dependency_type_col].iloc[0]}")
        if criticality_col and criticality_col in entry_row.columns:
            st.write(f"**Criticality:** {entry_row[criticality_col].iloc[0]}")
        if contract_tier_col and contract_tier_col in entry_row.columns:
            st.write(f"**Contract Tier:** {entry_row[contract_tier_col].iloc[0]}")
        if data_access_level_col and data_access_level_col in entry_row.columns:
            st.write(f"**Data Access Level:** {entry_row[data_access_level_col].iloc[0]}")

        if vendor_archetype_col and vendor_archetype_col in entry_row.columns:
            val = entry_row[vendor_archetype_col].iloc[0]
            if pd.notna(val) and str(val).strip():
                st.markdown("**Vendor Archetype**")
                st.write(str(val))

        if example_vendors_col and example_vendors_col in entry_row.columns:
            val = entry_row[example_vendors_col].iloc[0]
            if pd.notna(val) and str(val).strip():
                st.markdown("**Example Vendors**")
                st.write(str(val))

        if notes_col and notes_col in entry_row.columns:
            val = entry_row[notes_col].iloc[0]
            if pd.notna(val) and str(val).strip():
                st.markdown("**Notes**")
                st.write(str(val))

    with controls_col:
        st.markdown("#### 🧱 Structural Control Links (CRT-C)")

        if linked_controls_col and linked_controls_col in entry_row.columns:
            raw_links = entry_row[linked_controls_col].iloc[0]
            summary = entry_row["linked_control_summary"].iloc[0] if "linked_control_summary" in entry_row.columns else ""
            if pd.isna(raw_links) or not str(raw_links).strip():
                st.caption("No mapped CRT-C controls recorded for this entry.")
            else:
                st.markdown("**Mapped controls (CRT-C IDs)**")
                st.code(str(raw_links), language="text")

                if isinstance(summary, str) and summary.strip():
                    st.markdown("**Resolved Control Summary**")
                    st.write(summary)
                else:
                    st.caption("No control names resolved; check `CRT-C.csv` for matching IDs.")
        else:
            st.caption("No `mapped_control_ids` / `linked_controls` column present in the supply-chain catalogue.")


# -------------------------------------------------------------------------------------------------
# View 2 — Optional Supply-Chain Scope for Tasks (export-only)
# -------------------------------------------------------------------------------------------------
def render_view_context_bundles(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📦 Optional Supply-Chain Scope for Tasks")

    st.markdown(
        """
Most users can **skip this step** and go straight to **🎛 Programmes — Task Builder**.

Use this page only if you want downstream tasks or AI-assisted exploration to focus on a
**specific patch of your supply-chain landscape** (for example: direct, high-critical SaaS
vendors with access to sensitive data domains).

Whatever you choose here:

- It does **not** edit CRT-SC or configure controls
- You will see the bundle JSON before exporting it
- Lens maintenance and attachment happens in 🧠 AI Observation Console
"""
    )

    with st.expander("ℹ️ Help & Guidance — Supply-Chain Scope", expanded=False):
        render_markdown_file(
            HELP_VIEW_SCOPE_MD,
            fallback=(
                "Define a focused supply-chain scope when you want exports (or downstream modules) "
                "to reference a subset of CRT-SC. This is structural only and export-only."
            ),
        )

    if df_view.empty:
        st.warning("No supply-chain entries available — cannot build a context bundle.")
        return

    id_col = _detect_id_column(df_view)

    service_type_col = colmap.get("service_type_col")
    dependency_type_col = colmap.get("dependency_type_col")
    criticality_col = colmap.get("criticality_col")
    contract_tier_col = colmap.get("contract_tier_col")
    data_access_level_col = colmap.get("data_access_level_col")
    notes_col = colmap.get("notes_col")

    st.markdown("### 0️⃣ How should supply-chain entries be handled for this session?")

    scope_activation = st.radio(
        "Choose how to handle supply-chain scope for this export:",
        [
            "Don’t define a special supply-chain scope (use everything)",
            "Define a focused supply-chain scope (optional)",
        ],
        index=0,
        help="If you’re not sure, use the default and come back later.",
    )

    if scope_activation.startswith("Don’t define"):
        st.info(
            "No focused supply-chain scope will be built in this view. "
            "You can return later to export a focused scope if needed."
        )
        return

    st.markdown("### 1️⃣ Choose Scope Mode")

    scope_mode = st.radio(
        "Scope mode",
        [
            "Single supply-chain entry",
            "Multi-entry cluster",
            "Segment (filters)",
        ],
        help="Single = one primary entry. Cluster = small set. Segment = filter-defined scope.",
    )

    scope_df = pd.DataFrame()
    primary_entity: Dict[str, object] = {}
    filters: Dict[str, object] = {}

    st.markdown("### 2️⃣ Select Supply-Chain Scope")

    # ---------------------------------------------------------------------
    # Single entry
    # ---------------------------------------------------------------------
    if scope_mode == "Single supply-chain entry":
        fcol, tcol = st.columns([1, 2])

        with fcol:
            svc_choice = None
            dep_choice = None
            crit_choice = None
            contract_choice = None
            access_choice = None

            if service_type_col and service_type_col in df_view.columns:
                vals = ["(Any service type)"] + sorted(df_view[service_type_col].dropna().astype(str).unique().tolist())
                svc_choice = st.selectbox("Service Type", vals)

            if dependency_type_col and dependency_type_col in df_view.columns:
                vals = ["(Any dependency type)"] + sorted(df_view[dependency_type_col].dropna().astype(str).unique().tolist())
                dep_choice = st.selectbox("Dependency Type", vals)

            if criticality_col and criticality_col in df_view.columns:
                vals = ["(Any criticality)"] + sorted(df_view[criticality_col].dropna().astype(str).unique().tolist())
                crit_choice = st.selectbox("Criticality", vals)

            if contract_tier_col and contract_tier_col in df_view.columns:
                vals = ["(Any contract tier)"] + sorted(df_view[contract_tier_col].dropna().astype(str).unique().tolist())
                contract_choice = st.selectbox("Contract Tier", vals)

            if data_access_level_col and data_access_level_col in df_view.columns:
                vals = ["(Any access level)"] + sorted(df_view[data_access_level_col].dropna().astype(str).unique().tolist())
                access_choice = st.selectbox("Data Access Level", vals)

            text_filter = st.text_input("Notes contain", "")

        with tcol:
            df_filtered = df_view.copy()

            if service_type_col and svc_choice and svc_choice != "(Any service type)":
                df_filtered = df_filtered[df_filtered[service_type_col].astype(str) == svc_choice]
                filters["service_type"] = svc_choice

            if dependency_type_col and dep_choice and dep_choice != "(Any dependency type)":
                df_filtered = df_filtered[df_filtered[dependency_type_col].astype(str) == dep_choice]
                filters["dependency_type"] = dep_choice

            if criticality_col and crit_choice and crit_choice != "(Any criticality)":
                df_filtered = df_filtered[df_filtered[criticality_col].astype(str) == crit_choice]
                filters["criticality"] = crit_choice

            if contract_tier_col and contract_choice and contract_choice != "(Any contract tier)":
                df_filtered = df_filtered[df_filtered[contract_tier_col].astype(str) == contract_choice]
                filters["contract_tier"] = contract_choice

            if data_access_level_col and access_choice and access_choice != "(Any access level)":
                df_filtered = df_filtered[df_filtered[data_access_level_col].astype(str) == access_choice]
                filters["data_access_level"] = access_choice

            if text_filter and notes_col and notes_col in df_filtered.columns:
                tf = text_filter.lower()
                df_filtered = df_filtered[df_filtered[notes_col].astype(str).str.lower().str.contains(tf)]

            if df_filtered.empty:
                st.info("No supply-chain entries match the selected filters.")
                st.stop()

            st.markdown("#### Matching Entries")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_supply_label(row, colmap) for _, row in df_filtered.iterrows()]
        selected_label = st.selectbox("Entry to use as primary entity", options=labels)
        idx = labels.index(selected_label)

        scope_df = df_filtered.iloc[[idx]]
        row = scope_df.iloc[0]
        primary_id = (
            str(row[id_col])
            if id_col and id_col in row.index and pd.notna(row[id_col])
            else (_build_supply_label(row, colmap) or f"row-{row.name}")
        )
        primary_entity = {"type": "supply_chain_entry", "id": primary_id}

    # ---------------------------------------------------------------------
    # Multi-entry cluster
    # ---------------------------------------------------------------------
    elif scope_mode == "Multi-entry cluster":
        fcol, tcol = st.columns([1, 2])

        with fcol:
            svc_choice = None
            dep_choice = None
            crit_choice = None
            contract_choice = None

            if service_type_col and service_type_col in df_view.columns:
                vals = ["(Any service type)"] + sorted(df_view[service_type_col].dropna().astype(str).unique().tolist())
                svc_choice = st.selectbox("Service Type", vals)

            if dependency_type_col and dependency_type_col in df_view.columns:
                vals = ["(Any dependency type)"] + sorted(df_view[dependency_type_col].dropna().astype(str).unique().tolist())
                dep_choice = st.selectbox("Dependency Type", vals)

            if criticality_col and criticality_col in df_view.columns:
                vals = ["(Any criticality)"] + sorted(df_view[criticality_col].dropna().astype(str).unique().tolist())
                crit_choice = st.selectbox("Criticality", vals)

            if contract_tier_col and contract_tier_col in df_view.columns:
                vals = ["(Any contract tier)"] + sorted(df_view[contract_tier_col].dropna().astype(str).unique().tolist())
                contract_choice = st.selectbox("Contract Tier", vals)

        with tcol:
            df_filtered = df_view.copy()

            if service_type_col and svc_choice and svc_choice != "(Any service type)":
                df_filtered = df_filtered[df_filtered[service_type_col].astype(str) == svc_choice]
                filters["service_type"] = svc_choice

            if dependency_type_col and dep_choice and dep_choice != "(Any dependency type)":
                df_filtered = df_filtered[df_filtered[dependency_type_col].astype(str) == dep_choice]
                filters["dependency_type"] = dep_choice

            if criticality_col and crit_choice and crit_choice != "(Any criticality)":
                df_filtered = df_filtered[df_filtered[criticality_col].astype(str) == crit_choice]
                filters["criticality"] = crit_choice

            if contract_tier_col and contract_choice and contract_choice != "(Any contract tier)":
                df_filtered = df_filtered[df_filtered[contract_tier_col].astype(str) == contract_choice]
                filters["contract_tier"] = contract_choice

            if df_filtered.empty:
                st.info("No supply-chain entries match the selected filters.")
                st.stop()

            st.markdown("#### Available Entries for Cluster")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_supply_label(row, colmap) for _, row in df_filtered.iterrows()]

        cluster_labels = st.multiselect("Select entries to include in the cluster", options=labels)

        if not cluster_labels:
            st.info("Select at least one entry to form a cluster.")
            st.stop()

        indices = [labels.index(lbl) for lbl in cluster_labels]
        scope_df = df_filtered.iloc[indices]

        base_ids: List[str] = []
        for _, r in scope_df.iterrows():
            if id_col and id_col in r.index and pd.notna(r[id_col]):
                base_ids.append(str(r[id_col]))
            else:
                base_ids.append(_build_supply_label(r, colmap) or f"row-{r.name}")

        cluster_key = ",".join(sorted(base_ids))
        cluster_id = f"CRT-SC-cluster-{hashlib.sha256(cluster_key.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "supply_chain_cluster", "id": cluster_id}

    # ---------------------------------------------------------------------
    # Segment (filters)
    # ---------------------------------------------------------------------
    else:
        st.markdown("#### Define Segment Filters")

        svc_choice = None
        dep_choice = None
        crit_choice = None
        contract_choice = None
        access_choice = None

        if service_type_col and service_type_col in df_view.columns:
            vals = ["(Any service type)"] + sorted(df_view[service_type_col].dropna().astype(str).unique().tolist())
            svc_choice = st.selectbox("Service Type", vals)

        if dependency_type_col and dependency_type_col in df_view.columns:
            vals = ["(Any dependency type)"] + sorted(df_view[dependency_type_col].dropna().astype(str).unique().tolist())
            dep_choice = st.selectbox("Dependency Type", vals)

        if criticality_col and criticality_col in df_view.columns:
            vals = ["(Any criticality)"] + sorted(df_view[criticality_col].dropna().astype(str).unique().tolist())
            crit_choice = st.selectbox("Criticality", vals)

        if contract_tier_col and contract_tier_col in df_view.columns:
            vals = ["(Any contract tier)"] + sorted(df_view[contract_tier_col].dropna().astype(str).unique().tolist())
            contract_choice = st.selectbox("Contract Tier", vals)

        if data_access_level_col and data_access_level_col in df_view.columns:
            vals = ["(Any access level)"] + sorted(df_view[data_access_level_col].dropna().astype(str).unique().tolist())
            access_choice = st.selectbox("Data Access Level", vals)

        scope_df = df_view.copy()

        if service_type_col and svc_choice and svc_choice != "(Any service type)":
            scope_df = scope_df[scope_df[service_type_col].astype(str) == svc_choice]
            filters["service_type"] = svc_choice

        if dependency_type_col and dep_choice and dep_choice != "(Any dependency type)":
            scope_df = scope_df[scope_df[dependency_type_col].astype(str) == dep_choice]
            filters["dependency_type"] = dep_choice

        if criticality_col and crit_choice and crit_choice != "(Any criticality)":
            scope_df = scope_df[scope_df[criticality_col].astype(str) == crit_choice]
            filters["criticality"] = crit_choice

        if contract_tier_col and contract_choice and contract_choice != "(Any contract tier)":
            scope_df = scope_df[scope_df[contract_tier_col].astype(str) == contract_choice]
            filters["contract_tier"] = contract_choice

        if data_access_level_col and access_choice and access_choice != "(Any access level)":
            scope_df = scope_df[scope_df[data_access_level_col].astype(str) == access_choice]
            filters["data_access_level"] = access_choice

        st.markdown("#### Segment Preview")
        if scope_df.empty:
            st.info("No entries match this segment definition. The bundle will have an empty vendors list.")
        else:
            st.dataframe(scope_df, width="stretch", hide_index=True)

        filter_str = json.dumps(filters, sort_keys=True) if filters else "all"
        segment_id = f"CRT-SC-segment-{hashlib.sha256(filter_str.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "supply_chain_segment", "id": segment_id, "filters": filters}

    if scope_df is None or primary_entity == {}:
        st.warning("Unable to determine scope or primary entity — please review selections.")
        return

    st.markdown("### 3️⃣ Bundle Summary")

    coverage = _compute_coverage(scope_df, colmap)
    st.write(
        f"- **Scope mode:** `{scope_mode}`  \n"
        f"- **Entries in scope:** `{coverage['total_entries_in_scope']}`  \n"
        f"- **Primary entity:** `{primary_entity.get('type')}` → `{primary_entity.get('id')}`"
    )

    vendor_entities = [_row_to_vendor_entity(row, colmap, id_col) for _, row in scope_df.iterrows()]

    bundle: Dict[str, Any] = {
        "bundle_type": "supply_chain",
        "module": "🛰 Supply-Chain Exposure Scanner",
        "primary_entity": primary_entity,
        "entities": {
            "assets": [],
            "identities": [],
            "data_domains": [],
            "vendors": vendor_entities,
            "controls": [],
            "failures": [],
            "telemetry": [],
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
    # Export — Download or Save (Platinum / Minimal)  ✅ aligned with ASM
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
            file_name="sces_supply_chain_bundle.json",
            mime="application/json",
            use_container_width=True,
        )

    with b:
        if st.button("💾 Save to lens shelf", use_container_width=True):
            _ensure_dir(SCES_LENS_SHELF_DIR)

            pe = primary_entity if isinstance(primary_entity, dict) else {}
            pe_id = pe.get("id") if isinstance(pe, dict) else None

            name_hint = _safe_filename(str(pe_id)) if pe_id else "sces-scope"
            filename = f"sces_{name_hint}_{_utc_stamp()}.json"
            path = os.path.join(SCES_LENS_SHELF_DIR, filename)

            bundle["lens_meta"]["persisted_to_disk"] = True
            bundle["lens_meta"]["shelf_path_hint"] = f"lenses/sces/bundles/{filename}"

            ok = _save_json_file(path, bundle)
            if ok:
                st.success(f"Saved to lens shelf: {filename}")
                st.caption("Lens maintenance and attachment happens in 🧠 AI Observation Console.")
            else:
                st.error("Could not save to the lens shelf.")

    st.caption(
        "This lens is **export-only**. It does not configure controls, score maturity, "
        "or provide assurance. Review, attach, combine, or retire lenses in "
        "🧠 AI Observation Console."
    )


# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Supply-Chain Exposure Scanner",
    page_icon="🛰",
    layout="wide",
)

st.title("🛰 Supply-Chain Exposure Scanner")
st.caption(
    "Explore vendor and supply-chain dependencies, service types, and criticality tiers — "
    "read-only structural view of your CRT-SC supply-chain model."
)

with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "# 🛰 Supply-Chain Exposure Scanner\n\n"
            "This module surfaces the **effective CRT-SC catalogue** in a structured, "
            "non-prescriptive way.\n\n"
            "- Explore service types, dependency types, criticality, and contract tiers\n"
            "- Inspect a single vendor/dependency entry and what is recorded\n"
            "- View structural links to CRT-C controls (where defined)\n"
            "- Export a normalised `bundle_type = \"supply_chain\"` context bundle\n\n"
            "It does **not** configure controls, score maturity, or provide assurance."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Load Catalogues
# -------------------------------------------------------------------------------------------------
CATALOGUES = _load_crt_catalogues()
DF_SC = CATALOGUES.get("CRT-SC", pd.DataFrame())
DF_C = CATALOGUES.get("CRT-C", pd.DataFrame())
DF_VIEW, COLMAP = _prepare_view(DF_SC, DF_C)

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
st.sidebar.caption("Use the view selector below to switch between perspectives within the Supply-Chain Exposure Scanner.")

st.sidebar.info(
    """
**🛰 Supply-Chain Exposure Scanner**

Use this module to:

- Examine how vendor and supply-chain entries are defined
- See how service types, dependency types, and tiers distribute across the catalogue
- Inspect structural links to CRT-C controls (where recorded)
- Export a normalised `bundle_type = "supply_chain"` context bundle

All views are read-only. Catalogue updates and append operations are handled
exclusively via the 📂 Structural Controls & Frameworks — Command Centre and
🛰 Org-Specific Catalogues.
"""
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    ["📊 Catalogue Overview", "📦 Optional Supply-Chain Scope for Tasks"],
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
elif view_mode == "📦 Optional Supply-Chain Scope for Tasks":
    render_view_context_bundles(DF_VIEW, COLMAP)
else:
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
