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
🧩 Attack Surface Mapper — Cyber Resilience Toolkit (CRT)

This view shows how your attack-surface assets appear across environments,
boundaries, vendors, and recorded links to CRT-D data classes and CRT-C controls.

It is a simple, read-only lens. It does not score maturity, assess exposure,
or perform any form of risk or security analysis. It presents the structure
that exists today and lets you export a normalised `bundle_type = "attack_surface"`
for downstream CRT modules.

Most users scan the overview, inspect a few assets, and only build a small
optional scope when they want AI-driven tasks to talk about a specific patch
of the attack surface. All changes to catalogues happen in the Command Centre
and Org-Specific Catalogues.
"""

from __future__ import annotations

# -------------------------------------------------------------------------------------------------
# Standard Library
# -------------------------------------------------------------------------------------------------
import os
import sys
import json
import hashlib
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timezone

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
# Shared “Lens Publishing Contract” (Session + Disk Shelf)
# -------------------------------------------------------------------------------------------------
CRT_PUBLISHED_LENSES_KEY = "crt_published_lens_bundles"


# -------------------------------------------------------------------------------------------------
# Resolve Key Paths (for modules under /pages)
# -------------------------------------------------------------------------------------------------
PATHS = get_named_paths(__file__)
PROJECT_PATH = PATHS["level_up_1"]

ABOUT_APP_MD = os.path.join(PROJECT_PATH, "docs", "about_attack_surface_mapper.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")

# Optional per-view help docs
HELP_VIEW_OVERVIEW_MD = os.path.join(PROJECT_PATH, "docs", "help_attack_surface_overview.md")
HELP_VIEW_METRICS_MD = os.path.join(PROJECT_PATH, "docs", "help_attack_surface_metrics.md")

BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# CRT catalogue locations — used only as a fallback if SIH is not available
CATALOGUE_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "crt_catalogues")
CRT_AS_CSV = os.path.join(CATALOGUE_DIR, "CRT-AS.csv")  # Attack surface catalogue
CRT_D_CSV = os.path.join(CATALOGUE_DIR, "CRT-D.csv")   # Data classification catalogue
CRT_C_CSV = os.path.join(CATALOGUE_DIR, "CRT-C.csv")   # Controls catalogue

# Workspace shelf for lens snapshots (disk persistence)
ASM_LENS_SHELF_DIR = os.path.join(
    PROJECT_PATH, "apps", "data_sources", "crt_workspace", "lenses", "asm", "bundles"
)


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
# Lens shelf helpers (Disk persistence) — timezone-aware UTC
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
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

# -------------------------------------------------------------------------------------------------
# Data Loading Helpers (read-only)
# -------------------------------------------------------------------------------------------------
def _safe_read_csv(path: str) -> pd.DataFrame:
    """Safely read a CSV file; return empty DataFrame on error."""
    try:
        if not os.path.isfile(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        return df
    except Exception:  # pylint: disable=broad-except
        return pd.DataFrame()


def _load_crt_catalogues() -> Dict[str, pd.DataFrame]:
    """
    Load CRT-AS, CRT-D, and CRT-C catalogues in a read-only manner.

    Preferred path is via the System Integrator Hub (SIH), which enforces
    backbone vs append-only rules and centralises catalogue behaviour.

    If SIH is not available (e.g. during incremental upgrades), the module
    falls back to direct CSV read — still read-only.
    """
    # Preferred: SIH
    if get_sih is not None:
        try:
            sih = get_sih()
            return {
                "CRT-AS": sih.get_catalogue("CRT-AS"),
                "CRT-D": sih.get_catalogue("CRT-D"),
                "CRT-C": sih.get_catalogue("CRT-C"),
            }
        except Exception:  # pylint: disable=broad-except
            pass

    # Fallback: direct CSV read (still read-only)
    return {
        "CRT-AS": _safe_read_csv(CRT_AS_CSV),
        "CRT-D": _safe_read_csv(CRT_D_CSV),
        "CRT-C": _safe_read_csv(CRT_C_CSV),
    }


def _first_present_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return the first column name from `candidates` that exists in `df`."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _prepare_view(
    df_as: pd.DataFrame,
    df_d: pd.DataFrame,
    df_c: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    """
    Prepare the attack-surface view and identify key columns dynamically.
    """
    if df_as.empty:
        return pd.DataFrame(), {}

    df_view = df_as.copy()

    # Identify key semantic columns
    asset_id_col = _first_present_column(df_view, ["asset_id", "as_id", "id"])
    asset_name_col = _first_present_column(df_view, ["asset_name", "name"])
    asset_type_col = _first_present_column(df_view, ["asset_type", "type"])
    env_col = _first_present_column(df_view, ["environment", "env", "zone", "context"])
    boundary_col = _first_present_column(df_view, ["trust_boundary", "boundary", "exposure_type"])
    vendor_col = _first_present_column(df_view, ["vendor", "provider", "supplier"])
    description_col = _first_present_column(df_view, ["description", "summary", "asset_description"])
    notes_col = _first_present_column(df_view, ["notes", "comments"])
    entry_points_col = _first_present_column(df_view, ["entry_points", "ingress"])
    logical_data_col = _first_present_column(
        df_view,
        ["logical_data_classes", "logical_data", "data_classes", "data_domains"],
    )

    mapped_controls_col = _first_present_column(df_view, ["mapped_control_ids", "linked_controls"])
    mapped_data_col = _first_present_column(df_view, ["mapped_data_class_ids", "mapped_data_ids"])

    # Derived columns: mapped control count & mapped data class count
    if mapped_controls_col:

        def _count_controls(raw) -> int:
            if pd.isna(raw):
                return 0
            parts = str(raw).replace(";", ",").split(",")
            parts = [p.strip() for p in parts if p.strip()]
            return len(set(parts))

        df_view["mapped_control_count"] = df_view[mapped_controls_col].apply(_count_controls)
    else:
        df_view["mapped_control_count"] = 0

    if mapped_data_col:

        def _count_data_classes(raw) -> int:
            if pd.isna(raw):
                return 0
            parts = str(raw).replace(";", ",").split(",")
            parts = [p.strip() for p in parts if p.strip()]
            return len(set(parts))

        df_view["mapped_data_class_count"] = df_view[mapped_data_col].apply(_count_data_classes)
    else:
        df_view["mapped_data_class_count"] = 0

    # Flag for entry points present
    if entry_points_col:
        df_view["has_entry_points"] = df_view[entry_points_col].fillna("").astype(str).str.len() > 0
    else:
        df_view["has_entry_points"] = False

    # Optional: join CRT-C to show summary of linked control names
    if mapped_controls_col and not df_c.empty and "control_id" in df_c.columns:
        df_c_lookup = df_c[["control_id", "control_name"]].copy()
        df_c_lookup["control_id"] = df_c_lookup["control_id"].astype(str)

        def _resolve_controls(raw) -> str:
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
                    label = df_c_lookup.loc[df_c_lookup["control_id"] == cid, "control_name"].iloc[0]
                if label:
                    names.append(f"{cid} — {label}")
                else:
                    names.append(cid)
            return "; ".join(names)

        df_view["linked_control_summary"] = df_view[mapped_controls_col].apply(_resolve_controls)
    else:
        df_view["linked_control_summary"] = ""

    # Optional: join CRT-D to show summary of linked data class names
    if mapped_data_col and not df_d.empty:
        data_id_column = _first_present_column(df_d, ["data_id", "d_id", "id"])
        data_name_column = _first_present_column(df_d, ["data_name", "name"])
        if data_id_column:
            cols = [data_id_column] + ([data_name_column] if data_name_column else [])
            df_d_lookup = df_d[cols].copy()
            df_d_lookup[data_id_column] = df_d_lookup[data_id_column].astype(str)

            def _resolve_data_classes(raw) -> str:
                if pd.isna(raw):
                    return ""
                parts = str(raw).replace(";", ",").split(",")
                parts = [p.strip() for p in parts if p.strip()]
                ids = sorted(set(parts))
                names: List[str] = []
                for did in ids:
                    row = df_d_lookup[df_d_lookup[data_id_column] == did]
                    label = None
                    if not row.empty and data_name_column:
                        label = df_d_lookup.loc[df_d_lookup[data_id_column] == did, data_name_column].iloc[0]
                    if label:
                        names.append(f"{did} — {label}")
                    else:
                        names.append(did)
                return "; ".join(names)

            df_view["linked_data_class_summary"] = df_view[mapped_data_col].apply(_resolve_data_classes)
        else:
            df_view["linked_data_class_summary"] = ""
    else:
        df_view["linked_data_class_summary"] = ""

    colmap: Dict[str, Optional[str]] = {
        "asset_id_col": asset_id_col,
        "asset_name_col": asset_name_col,
        "asset_type_col": asset_type_col,
        "env_col": env_col,
        "boundary_col": boundary_col,
        "vendor_col": vendor_col,
        "description_col": description_col,
        "notes_col": notes_col,
        "entry_points_col": entry_points_col,
        "logical_data_col": logical_data_col,
        "mapped_controls_col": mapped_controls_col,
        "mapped_data_col": mapped_data_col,
    }

    return df_view, colmap


def _build_asset_label(row: pd.Series, colmap: Dict[str, Optional[str]]) -> str:
    """Build a human-readable label for an asset using Name / Type / Environment / Boundary."""
    name_col = colmap.get("asset_name_col")
    type_col = colmap.get("asset_type_col")
    env_col = colmap.get("env_col")
    boundary_col = colmap.get("boundary_col")

    parts: List[str] = []
    if name_col and name_col in row.index and pd.notna(row.get(name_col)):
        parts.append(str(row[name_col]))
    if type_col and type_col in row.index and pd.notna(row.get(type_col)):
        parts.append(f"({row[type_col]})")
    if env_col and env_col in row.index and pd.notna(row.get(env_col)):
        parts.append(f"[{row[env_col]}]")
    if boundary_col and boundary_col in row.index and pd.notna(row.get(boundary_col)):
        parts.append(f"⟂ {row[boundary_col]}")

    return " ".join(parts) if parts else "Unlabelled asset"


def _detect_id_column(df_view: pd.DataFrame) -> Optional[str]:
    """Detect a likely primary identifier column for CRT-AS entries."""
    return _first_present_column(df_view, ["asset_id", "as_id", "id"])


def _row_to_asset_entity(
    row: pd.Series,
    colmap: Dict[str, Optional[str]],
    id_col: Optional[str],
) -> Dict[str, object]:
    """Convert a CRT-AS row into a normalised asset entity for context bundles (structural only)."""
    if id_col and id_col in row.index and pd.notna(row[id_col]):
        entity_id = str(row[id_col])
    else:
        entity_id = _build_asset_label(row, colmap) or f"row-{row.name}"

    name_col = colmap.get("asset_name_col")
    type_col = colmap.get("asset_type_col")
    env_col = colmap.get("env_col")
    boundary_col = colmap.get("boundary_col")
    vendor_col = colmap.get("vendor_col")

    entity: Dict[str, object] = {
        "catalogue": "CRT-AS",
        "id": entity_id,
        "raw": row.to_dict(),
    }

    if name_col and name_col in row.index:
        entity["name"] = row[name_col]
    if type_col and type_col in row.index:
        entity["asset_type"] = row[type_col]
    if env_col and env_col in row.index:
        entity["environment"] = row[env_col]
    if boundary_col and boundary_col in row.index:
        entity["trust_boundary"] = row[boundary_col]
    if vendor_col and vendor_col in row.index:
        entity["vendor"] = row[vendor_col]

    return entity


def _compute_coverage(df_scope: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> Dict[str, int]:
    """Compute simple, descriptive coverage metrics for a given scope of assets."""
    if df_scope.empty:
        return {
            "total_assets_in_scope": 0,
            "distinct_asset_types_in_scope": 0,
            "distinct_environments_in_scope": 0,
            "distinct_boundaries_in_scope": 0,
            "assets_with_mapped_data_in_scope": 0,
            "assets_with_mapped_controls_in_scope": 0,
        }

    asset_type_col = colmap.get("asset_type_col")
    env_col = colmap.get("env_col")
    boundary_col = colmap.get("boundary_col")
    mapped_controls_col = colmap.get("mapped_controls_col")
    mapped_data_col = colmap.get("mapped_data_col")

    total_assets = len(df_scope)
    atype_count = df_scope[asset_type_col].dropna().astype(str).nunique() if asset_type_col and asset_type_col in df_scope.columns else 0
    env_count = df_scope[env_col].dropna().astype(str).nunique() if env_col and env_col in df_scope.columns else 0
    boundary_count = df_scope[boundary_col].dropna().astype(str).nunique() if boundary_col and boundary_col in df_scope.columns else 0

    def _has_any_ids(val: object) -> bool:
        if pd.isna(val):
            return False
        s = str(val).strip()
        if not s:
            return False
        parts = [p.strip() for p in s.replace(";", ",").split(",")]
        return any(parts)

    with_mapped_data = int(df_scope[mapped_data_col].apply(_has_any_ids).sum()) if mapped_data_col and mapped_data_col in df_scope.columns else 0
    with_mapped_controls = int(df_scope[mapped_controls_col].apply(_has_any_ids).sum()) if mapped_controls_col and mapped_controls_col in df_scope.columns else 0

    return {
        "total_assets_in_scope": int(total_assets),
        "distinct_asset_types_in_scope": int(atype_count),
        "distinct_environments_in_scope": int(env_count),
        "distinct_boundaries_in_scope": int(boundary_count),
        "assets_with_mapped_data_in_scope": int(with_mapped_data),
        "assets_with_mapped_controls_in_scope": int(with_mapped_controls),
    }


def _build_relationships_from_scope(
    df_scope: pd.DataFrame,
    colmap: Dict[str, Optional[str]],
    id_col: Optional[str],
) -> List[Dict[str, str]]:
    """Build simple structural relationships from scoped assets to data classes and controls (ID-level only)."""
    relationships: List[Dict[str, str]] = []

    mapped_controls_col = colmap.get("mapped_controls_col")
    mapped_data_col = colmap.get("mapped_data_col")

    if df_scope.empty or (not mapped_controls_col and not mapped_data_col):
        return relationships

    for _, row in df_scope.iterrows():
        if id_col and id_col in row.index and pd.notna(row[id_col]):
            asset_id = str(row[id_col])
        else:
            asset_id = _build_asset_label(row, colmap) or f"row-{row.name}"

        if mapped_data_col and mapped_data_col in row.index and not pd.isna(row[mapped_data_col]):
            parts = str(row[mapped_data_col]).replace(";", ",").split(",")
            for did in [p.strip() for p in parts if p.strip()]:
                relationships.append({"type": "asset_to_data_class", "from_asset": asset_id, "to_data_class": did})

        if mapped_controls_col and mapped_controls_col in row.index and not pd.isna(row[mapped_controls_col]):
            parts = str(row[mapped_controls_col]).replace(";", ",").split(",")
            for cid in [p.strip() for p in parts if p.strip()]:
                relationships.append({"type": "asset_to_control", "from_asset": asset_id, "to_control": cid})

    return relationships


# -------------------------------------------------------------------------------------------------
# View 1 — Catalogue Overview (with inspection)
# -------------------------------------------------------------------------------------------------
def render_view_overview(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    """High-level view across all attack-surface assets with lightweight filters + descriptive metrics."""
    st.header("📊 Attack Surface Catalogue Overview")
    st.markdown(
        """
Use this view to explore the **structure** of your attack surface:

- How assets are distributed across environments and boundaries
- Which vendors and service zones appear
- Where data-class and control mappings have been recorded

The metrics are **descriptive only**. They do not assess exposure, quality,
coverage, or assurance. They simply reflect what is present in your catalogue.
"""
    )

    with st.expander("ℹ️ Help & Guidance — Overview", expanded=False):
        render_markdown_file(
            HELP_VIEW_OVERVIEW_MD,
            fallback=(
                "This overview shows the effective CRT-AS catalogue in a simple table, "
                "alongside descriptive metrics about environments, boundaries, and recorded "
                "links to data classes and controls. It does not interpret these links. "
                "Any updates are made in the Command Centre and Org-Specific Catalogues."
            ),
        )

    if df_view.empty:
        st.warning("No assets found in CRT-AS. Populate CRT-AS via the Command Centre.")
        return

    st.markdown("### 📈 Coverage & Metrics (structural, descriptive only)")
    coverage = _compute_coverage(df_view, colmap)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Assets", value=coverage["total_assets_in_scope"])
    with m2:
        st.metric("Distinct Asset Types", value=coverage["distinct_asset_types_in_scope"])
    with m3:
        st.metric("Distinct Environments", value=coverage["distinct_environments_in_scope"])

    m4, m5, m6 = st.columns(3)
    with m4:
        st.metric("Distinct Trust Boundaries", value=coverage["distinct_boundaries_in_scope"])
    with m5:
        st.metric("Assets with mapped data classes (CRT-D)", value=coverage["assets_with_mapped_data_in_scope"])
    with m6:
        st.metric("Assets with mapped controls (CRT-C)", value=coverage["assets_with_mapped_controls_in_scope"])

    with st.expander("ℹ️ Coverage & Metrics — Detail", expanded=False):
        render_markdown_file(
            HELP_VIEW_METRICS_MD,
            fallback=(
                "These metrics summarise how many assets exist across environments, "
                "asset types, and trust boundaries, and where mappings to CRT-D data "
                "classes and CRT-C controls are recorded. They are **purely descriptive**."
            ),
        )

    st.markdown("### 🧩 All Attack-Surface Assets")

    asset_type_col = colmap.get("asset_type_col")
    env_col = colmap.get("env_col")
    boundary_col = colmap.get("boundary_col")
    vendor_col = colmap.get("vendor_col")
    description_col = colmap.get("description_col")
    logical_data_col = colmap.get("logical_data_col")
    entry_points_col = colmap.get("entry_points_col")

    filter_col, table_col = st.columns([1, 3])

    with filter_col:
        st.markdown("#### 🔎 Filters")

        atype_choice = None
        env_choice = None
        boundary_choice = None
        vendor_choice = None

        if asset_type_col and asset_type_col in df_view.columns:
            atypes = ["(All asset types)"] + sorted(df_view[asset_type_col].dropna().astype(str).unique().tolist())
            atype_choice = st.selectbox("Asset Type", atypes)

        if env_col and env_col in df_view.columns:
            envs = ["(All environments)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
            env_choice = st.selectbox("Environment / Zone", envs)

        if boundary_col and boundary_col in df_view.columns:
            bnds = ["(All boundaries)"] + sorted(df_view[boundary_col].dropna().astype(str).unique().tolist())
            boundary_choice = st.selectbox("Trust / Exposure Boundary", bnds)

        if vendor_col and vendor_col in df_view.columns:
            vnds = ["(All vendors)"] + sorted(df_view[vendor_col].dropna().astype(str).unique().tolist())
            vendor_choice = st.selectbox("Vendor", vnds)

        text_filter = st.text_input("Description / data classes / entry points contain", "")

        only_with_data = st.checkbox("Only assets with mapped data classes (CRT-D)", value=False)
        only_with_controls = st.checkbox("Only assets with mapped controls (CRT-C)", value=False)

    with table_col:
        df_filtered = df_view.copy()

        if asset_type_col and atype_choice and atype_choice != "(All asset types)":
            df_filtered = df_filtered[df_filtered[asset_type_col].astype(str) == atype_choice]
        if env_col and env_choice and env_choice != "(All environments)":
            df_filtered = df_filtered[df_filtered[env_col].astype(str) == env_choice]
        if boundary_col and boundary_choice and boundary_choice != "(All boundaries)":
            df_filtered = df_filtered[df_filtered[boundary_col].astype(str) == boundary_choice]
        if vendor_col and vendor_choice and vendor_choice != "(All vendors)":
            df_filtered = df_filtered[df_filtered[vendor_col].astype(str) == vendor_choice]

        if text_filter:
            text_filter_lower = text_filter.lower()
            text_cols: List[str] = []
            for col in (description_col, logical_data_col, entry_points_col):
                if col and col in df_filtered.columns:
                    text_cols.append(col)

            if text_cols:
                mask = False
                for col in text_cols:
                    series = df_filtered[col].astype(str).str.lower().str.contains(text_filter_lower)
                    mask = series if isinstance(mask, bool) else (mask | series)
                if not isinstance(mask, bool):
                    df_filtered = df_filtered[mask]

        if only_with_data and "mapped_data_class_count" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["mapped_data_class_count"] > 0]
        if only_with_controls and "mapped_control_count" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["mapped_control_count"] > 0]

        if df_filtered.empty:
            st.info("No assets match the selected filters.")
        else:
            cols_to_hide = {
                "mapped_data_class_ids",
                "mapped_control_ids",
                "mapped_data_class_count",
                "mapped_control_count",
                "has_entry_points",
                "linked_control_summary",
                "linked_data_class_summary",
            }
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "asset_id",
                "asset_name",
                "asset_type",
                "environment",
                "trust_boundary",
                "vendor",
                "exposure_type",
                "entry_points",
                "logical_data_classes",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("### 🧬 Inspect a Single Asset (optional)")

    if df_filtered.empty:
        st.caption("Adjust filters above to enable per-asset inspection.")
        return

    df_filtered = df_filtered.reset_index(drop=True)
    labels = [_build_asset_label(row, colmap) for _, row in df_filtered.iterrows()]
    selected_label = st.selectbox("Select an asset to inspect", options=["(None selected)"] + labels, index=0)

    if selected_label == "(None selected)":
        st.caption("Choose an asset to see the recorded structural details and any data/control references.")
        return

    idx = labels.index(selected_label)
    asset_row = df_filtered.iloc[[idx]]

    mapped_data_col = colmap.get("mapped_data_col")
    mapped_controls_col = colmap.get("mapped_controls_col")

    details_col, col_mappings = st.columns([2, 2])

    with details_col:
        st.markdown("#### Structural Attributes")

        name_col = colmap.get("asset_name_col")
        asset_type_col = colmap.get("asset_type_col")
        env_col = colmap.get("env_col")
        boundary_col = colmap.get("boundary_col")
        vendor_col = colmap.get("vendor_col")
        description_col = colmap.get("description_col")
        logical_data_col = colmap.get("logical_data_col")
        entry_points_col = colmap.get("entry_points_col")
        notes_col = colmap.get("notes_col")

        if name_col and name_col in asset_row.columns:
            st.write(f"**Asset name:** {asset_row[name_col].iloc[0]}")
        if asset_type_col and asset_type_col in asset_row.columns:
            st.write(f"**Asset type:** {asset_row[asset_type_col].iloc[0]}")
        if env_col and env_col in asset_row.columns:
            st.write(f"**Environment / Zone:** {asset_row[env_col].iloc[0]}")
        if boundary_col and boundary_col in asset_row.columns:
            st.write(f"**Trust / Exposure boundary:** {asset_row[boundary_col].iloc[0]}")
        if vendor_col and vendor_col in asset_row.columns:
            st.write(f"**Vendor:** {asset_row[vendor_col].iloc[0]}")

        if description_col and description_col in asset_row.columns:
            desc_val = asset_row[description_col].iloc[0]
            if pd.notna(desc_val) and str(desc_val).strip():
                st.markdown("**Description**")
                st.write(str(desc_val))

        if logical_data_col and logical_data_col in asset_row.columns:
            ld_val = asset_row[logical_data_col].iloc[0]
            if pd.notna(ld_val) and str(ld_val).strip():
                st.markdown("**Logical data classes (free-form)**")
                st.write(str(ld_val))

        if entry_points_col and entry_points_col in asset_row.columns:
            ep_val = asset_row[entry_points_col].iloc[0]
            st.markdown("**Entry points**")
            if pd.isna(ep_val) or not str(ep_val).strip():
                st.caption("No entry points recorded for this asset.")
            else:
                st.code(str(ep_val), language="text")

        if notes_col and notes_col in asset_row.columns:
            notes_val = asset_row[notes_col].iloc[0]
            if pd.notna(notes_val) and str(notes_val).strip():
                st.markdown("**Notes**")
                st.write(str(notes_val))

    with col_mappings:
        st.markdown("#### 🔗 Recorded Links")

        if mapped_data_col and mapped_data_col in asset_row.columns:
            raw_data_links = asset_row[mapped_data_col].iloc[0]
            data_summary = asset_row["linked_data_class_summary"].iloc[0]
            st.markdown("**Recorded data-class references (CRT-D)**")
            if pd.isna(raw_data_links) or not str(raw_data_links).strip():
                st.caption("No mapped CRT-D data classes recorded for this asset.")
            else:
                st.code(str(raw_data_links), language="text")
                if isinstance(data_summary, str) and data_summary.strip():
                    st.markdown("**Resolved data class summary**")
                    st.write(data_summary)

        st.markdown("---")

        if mapped_controls_col and mapped_controls_col in asset_row.columns:
            raw_ctrl_links = asset_row[mapped_controls_col].iloc[0]
            ctrl_summary = asset_row["linked_control_summary"].iloc[0]
            st.markdown("**Recorded control references (CRT-C)**")
            if pd.isna(raw_ctrl_links) or not str(raw_ctrl_links).strip():
                st.caption("No mapped CRT-C controls recorded for this asset.")
            else:
                st.code(str(raw_ctrl_links), language="text")
                if isinstance(ctrl_summary, str) and ctrl_summary.strip():
                    st.markdown("**Resolved control summary**")
                    st.write(ctrl_summary)


# -------------------------------------------------------------------------------------------------
# View 2 — Optional Asset Scope for Tasks (export-only + session publish + disk shelf)
# -------------------------------------------------------------------------------------------------
def render_view_context_bundles(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📦 Optional Asset Scope for Tasks")

    st.markdown(
        """
Most users can skip this step and go straight to **🎛 Programmes — Task Builder**.

Use this page **only if you want AI-driven tasks to talk about a specific patch of data**
of your attack surface.

Whatever you choose here:

- It does **not** edit CRT-AS, CRT-D, or configure controls
- You will see the bundle JSON before using it
- You can review and adjust scope again in **🧠 AI Observation Console**
  before anything is sent to an external AI model
"""
    )

    if df_view.empty:
        st.warning("No assets available — cannot build a context bundle.")
        return

    st.markdown("### 0️⃣ How should assets be handled for this session?")

    scope_activation = st.radio(
        "Choose how to handle assets for tasks built from this session:",
        [
            "Don’t define a special asset scope (use everything)",
            "Define a focused asset scope (optional)",
        ],
        index=0,
    )

    if scope_activation.startswith("Don’t define"):
        st.info(
            "Downstream tools will treat your **entire CRT-AS catalogue** as available. "
            "Use this default when exploring."
        )
        return

    id_col = _detect_id_column(df_view)

    env_col = colmap.get("env_col")
    boundary_col = colmap.get("boundary_col")
    asset_type_col = colmap.get("asset_type_col")
    vendor_col = colmap.get("vendor_col")

    st.markdown("### 1️⃣ Choose Scope Mode")
    scope_mode = st.radio(
        "Scope mode",
        ["Single asset", "Multi-asset cluster", "Boundary / segment scope"],
    )

    scope_df = pd.DataFrame()
    primary_entity: Dict[str, object] = {}
    filters: Dict[str, object] = {}

    st.markdown("### 2️⃣ Select Asset Scope")

    # Pattern A — Single asset
    if scope_mode == "Single asset":
        filter_col, table_col = st.columns([1, 2])

        with filter_col:
            atype_choice = None
            env_choice = None
            boundary_choice = None
            vendor_choice = None

            if asset_type_col and asset_type_col in df_view.columns:
                atypes = ["(Any asset type)"] + sorted(df_view[asset_type_col].dropna().astype(str).unique().tolist())
                atype_choice = st.selectbox("Asset Type", atypes)

            if env_col and env_col in df_view.columns:
                envs = ["(Any environment)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
                env_choice = st.selectbox("Environment / Zone", envs)

            if boundary_col and boundary_col in df_view.columns:
                bnds = ["(Any boundary)"] + sorted(df_view[boundary_col].dropna().astype(str).unique().tolist())
                boundary_choice = st.selectbox("Trust / Exposure Boundary", bnds)

            if vendor_col and vendor_col in df_view.columns:
                vnds = ["(Any vendor)"] + sorted(df_view[vendor_col].dropna().astype(str).unique().tolist())
                vendor_choice = st.selectbox("Vendor", vnds)

            text_filter = st.text_input("Description / logical data / entry points contain", "")

        with table_col:
            df_filtered = df_view.copy()

            if asset_type_col and atype_choice and atype_choice != "(Any asset type)":
                df_filtered = df_filtered[df_filtered[asset_type_col].astype(str) == atype_choice]
            if env_col and env_choice and env_choice != "(Any environment)":
                df_filtered = df_filtered[df_filtered[env_col].astype(str) == env_choice]
            if boundary_col and boundary_choice and boundary_choice != "(Any boundary)":
                df_filtered = df_filtered[df_filtered[boundary_col].astype(str) == boundary_choice]
            if vendor_col and vendor_choice and vendor_choice != "(Any vendor)":
                df_filtered = df_filtered[df_filtered[vendor_col].astype(str) == vendor_choice]

            if text_filter:
                text_filter_lower = text_filter.lower()
                text_cols: List[str] = []
                for col in (colmap.get("description_col"), colmap.get("logical_data_col"), colmap.get("entry_points_col")):
                    if col and col in df_filtered.columns:
                        text_cols.append(col)
                if text_cols:
                    mask = False
                    for col in text_cols:
                        series = df_filtered[col].astype(str).str.lower().str.contains(text_filter_lower)
                        mask = series if isinstance(mask, bool) else (mask | series)
                    if not isinstance(mask, bool):
                        df_filtered = df_filtered[mask]

            if df_filtered.empty:
                st.info("No assets match the selected filters.")
                st.stop()

            st.markdown("#### Matching Assets")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_asset_label(row, colmap) for _, row in df_filtered.iterrows()]
        selected_label = st.selectbox("Asset to use as primary entity", options=labels)
        idx = labels.index(selected_label)

        scope_df = df_filtered.iloc[[idx]]
        row = scope_df.iloc[0]
        primary_id = str(row[id_col]) if id_col and id_col in row.index and pd.notna(row[id_col]) else (_build_asset_label(row, colmap) or f"row-{row.name}")
        primary_entity = {"type": "asset", "id": primary_id}

    # Pattern B — Cluster
    elif scope_mode == "Multi-asset cluster":
        filter_col, table_col = st.columns([1, 2])

        with filter_col:
            atype_choice = None
            env_choice = None
            boundary_choice = None
            vendor_choice = None

            if asset_type_col and asset_type_col in df_view.columns:
                atypes = ["(Any asset type)"] + sorted(df_view[asset_type_col].dropna().astype(str).unique().tolist())
                atype_choice = st.selectbox("Asset Type", atypes)

            if env_col and env_col in df_view.columns:
                envs = ["(Any environment)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
                env_choice = st.selectbox("Environment / Zone", envs)

            if boundary_col and boundary_col in df_view.columns:
                bnds = ["(Any boundary)"] + sorted(df_view[boundary_col].dropna().astype(str).unique().tolist())
                boundary_choice = st.selectbox("Trust / Exposure Boundary", bnds)

            if vendor_col and vendor_col in df_view.columns:
                vnds = ["(Any vendor)"] + sorted(df_view[vendor_col].dropna().astype(str).unique().tolist())
                vendor_choice = st.selectbox("Vendor", vnds)

        with table_col:
            df_filtered = df_view.copy()

            if asset_type_col and atype_choice and atype_choice != "(Any asset type)":
                df_filtered = df_filtered[df_filtered[asset_type_col].astype(str) == atype_choice]
            if env_col and env_choice and env_choice != "(Any environment)":
                df_filtered = df_filtered[df_filtered[env_col].astype(str) == env_choice]
            if boundary_col and boundary_choice and boundary_choice != "(Any boundary)":
                df_filtered = df_filtered[df_filtered[boundary_col].astype(str) == boundary_choice]
            if vendor_col and vendor_choice and vendor_choice != "(Any vendor)":
                df_filtered = df_filtered[df_filtered[vendor_col].astype(str) == vendor_choice]

            if df_filtered.empty:
                st.info("No assets match the selected filters.")
                st.stop()

            st.markdown("#### Available Assets for Cluster")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_asset_label(row, colmap) for _, row in df_filtered.iterrows()]
        cluster_labels = st.multiselect("Select assets to include in the cluster", options=labels)

        if not cluster_labels:
            st.info("Select at least one asset to form a cluster.")
            st.stop()

        indices = [labels.index(lbl) for lbl in cluster_labels]
        scope_df = df_filtered.iloc[indices]

        base_ids: List[str] = []
        for _, r in scope_df.iterrows():
            if id_col and id_col in r.index and pd.notna(r[id_col]):
                base_ids.append(str(r[id_col]))
            else:
                base_ids.append(_build_asset_label(r, colmap) or f"row-{r.name}")

        cluster_key = ",".join(sorted(base_ids))
        cluster_id = f"CRT-AS-cluster-{hashlib.sha256(cluster_key.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "asset_cluster", "id": cluster_id}

    # Pattern C — Segment
    else:
        st.markdown("#### Define Segment Filters")

        atype_choice = None
        env_choice = None
        boundary_choice = None
        vendor_choice = None

        if asset_type_col and asset_type_col in df_view.columns:
            atypes = ["(Any asset type)"] + sorted(df_view[asset_type_col].dropna().astype(str).unique().tolist())
            atype_choice = st.selectbox("Asset Type", atypes)

        if env_col and env_col in df_view.columns:
            envs = ["(Any environment)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
            env_choice = st.selectbox("Environment / Zone", envs)

        if boundary_col and boundary_col in df_view.columns:
            bnds = ["(Any boundary)"] + sorted(df_view[boundary_col].dropna().astype(str).unique().tolist())
            boundary_choice = st.selectbox("Trust / Exposure Boundary", bnds)

        if vendor_col and vendor_col in df_view.columns:
            vnds = ["(Any vendor)"] + sorted(df_view[vendor_col].dropna().astype(str).unique().tolist())
            vendor_choice = st.selectbox("Vendor", vnds)

        scope_df = df_view.copy()

        if asset_type_col and atype_choice and atype_choice != "(Any asset type)":
            scope_df = scope_df[scope_df[asset_type_col].astype(str) == atype_choice]
            filters["asset_type"] = atype_choice
        if env_col and env_choice and env_choice != "(Any environment)":
            scope_df = scope_df[scope_df[env_col].astype(str) == env_choice]
            filters["environment"] = env_choice
        if boundary_col and boundary_choice and boundary_choice != "(Any boundary)":
            scope_df = scope_df[scope_df[boundary_col].astype(str) == boundary_choice]
            filters["trust_boundary"] = boundary_choice
        if vendor_col and vendor_choice and vendor_choice != "(Any vendor)":
            scope_df = scope_df[scope_df[vendor_col].astype(str) == vendor_choice]
            filters["vendor"] = vendor_choice

        st.markdown("#### Segment Preview")
        if scope_df.empty:
            st.info("No assets match this segment definition. The bundle will have an empty assets list.")
        else:
            st.dataframe(scope_df, width="stretch", hide_index=True)

        filter_str = json.dumps(filters, sort_keys=True) if filters else "all"
        segment_id = f"CRT-AS-segment-{hashlib.sha256(filter_str.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "asset_segment", "id": segment_id, "filters": filters}

    if scope_df is None or not primary_entity:
        st.warning("Unable to determine scope or primary entity — please review selections.")
        return

    st.markdown("### 3️⃣ Bundle Summary")

    coverage = _compute_coverage(scope_df, colmap)
    st.write(
        f"- **Scope mode:** `{scope_mode}`  \n"
        f"- **Assets in scope:** `{coverage['total_assets_in_scope']}`  \n"
        f"- **Primary entity:** `{primary_entity.get('type')}` → `{primary_entity.get('id')}`"
    )

    asset_entities = [_row_to_asset_entity(r, colmap, id_col) for _, r in scope_df.iterrows()]
    relationships = _build_relationships_from_scope(scope_df, colmap, id_col)

    bundle: Dict[str, Any] = {
        "bundle_type": "attack_surface",
        "module": "🧩 Attack Surface Mapper",
        "primary_entity": primary_entity,
        "entities": {
            "assets": asset_entities,
            "identities": [],
            "data_domains": [],
            "vendors": [],
            "controls": [],
            "failures": [],
            "telemetry": [],
        },
        "relationships": relationships,
        "structural_findings": {
            "gaps": [],
            "compensations": [],
            "coverage": coverage,
            "exposure_paths": [],
        },
        "guardrails": {
            "no_advice": True,
            "no_configuration": True,
            "no_assurance": True,
        },
        "lens_meta": {
            "built_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "source": "module",
        },
    }

    # -------------------------------------------------------------------------------------------------
    # Export — Download or Save (Platinum / Minimal)
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
            file_name="asm_attack_surface_bundle.json",
            mime="application/json",
            use_container_width=True,
        )

    with b:
        if st.button("💾 Save to lens shelf", use_container_width=True):
            _ensure_dir(ASM_LENS_SHELF_DIR)

            pe = primary_entity if isinstance(primary_entity, dict) else {}
            pe_id = pe.get("id") if isinstance(pe, dict) else None

            name_hint = _safe_filename(str(pe_id)) if pe_id else "asm-scope"
            filename = f"asm_{name_hint}_{_utc_stamp()}.json"
            path = os.path.join(ASM_LENS_SHELF_DIR, filename)

            bundle.setdefault("lens_meta", {})
            bundle["lens_meta"]["persisted_to_disk"] = True
            bundle["lens_meta"]["shelf_path_hint"] = f"lenses/asm/bundles/{filename}"

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
    page_title="Attack Surface Mapper",
    page_icon="🧩",
    layout="wide",
)

st.title("🧩 Attack Surface Mapper")
st.caption(
    "A simple, read-only view of your CRT-AS assets — how they are arranged "
    "across environments, boundaries, vendors, and recorded data/control links."
)

# -------------------------------------------------------------------------------------------------
# Info Panel
# -------------------------------------------------------------------------------------------------
with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "# 🧩 Attack Surface Mapper\n\n"
            "Use this module to explore how assets are arranged across environments, "
            "boundaries, vendors, and any recorded references to CRT-D data classes "
            "or CRT-C controls.\n\n"
            "It is a simple, read-only structural view. It does not evaluate exposure, "
            "risk, coverage, or posture. Any updates to catalogues happen in the "
            "Command Centre and Org-Specific Catalogues.\n\n"
            "You can also define an **optional asset scope** and export a normalised "
            "`bundle_type = \"attack_surface\"` context bundle for use in downstream "
            "CRT modules."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Load Catalogues
# -------------------------------------------------------------------------------------------------
CATALOGUES = _load_crt_catalogues()
DF_AS = CATALOGUES.get("CRT-AS", pd.DataFrame())
DF_D = CATALOGUES.get("CRT-D", pd.DataFrame())
DF_C = CATALOGUES.get("CRT-C", pd.DataFrame())
DF_VIEW, COLMAP = _prepare_view(DF_AS, DF_D, DF_C)

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
st.sidebar.caption("Use the view selector below to switch between perspectives within the Attack Surface Mapper.")

st.sidebar.info(
    """
**🧩 Attack Surface Mapper**

Explore how assets appear across environments, boundaries, vendors, and any
recorded links to CRT-D data classes and CRT-C controls.

- Read-only
- Structural
- No risk scoring
- No configuration

All catalogue updates happen in the 📂 Structural Controls & Frameworks —
Command Centre and 🛰 Org-Specific Catalogues.
"""
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    ["📊 Catalogue Overview", "📦 Optional Asset Scope for Tasks"],
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
elif view_mode == "📦 Optional Asset Scope for Tasks":
    render_view_context_bundles(DF_VIEW, COLMAP)
else:
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
