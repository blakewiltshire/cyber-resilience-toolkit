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
📂 Structural Controls & Frameworks — Cyber Resilience Toolkit (CRT)

Command Centre for CRT catalogues.

This module provides:
- Read-only browsing of all CRT catalogues (core, operational, governance).
- Centralised management of catalogue CSVs for governance and operational layers:
  - Upload overwrites the ACTIVE working CSV (e.g., CRT-LR.csv)
  - CRT creates a timestamped backup of the prior active file in /backup
  - CRT regenerates the matching JSON view in /json
- A read-only Mapping Explorer for viewing relationships between:
  - User controls (CRT-UC)
  - CRT Series controls (CRT-C)
  - Policies (CRT-POL)
  - Standards (CRT-STD)
  - Obligations (CRT-LR)

Core CRT Series catalogues (CRT-G/C/F/N) are treated as a locked backbone.
They are visible for browsing but not editable via this interface, to avoid
breaking downstream modules and mappings.

Navigation:

1) CRT Defaults Browser (read-only CRT backbone + shipped catalogues)
2) Governance Setup (Framework Onboarding) — CRT-UC / CRT-POL / CRT-LR / CRT-STD
3) Operational Extensions (Org-Specific) — CRT-AS / CRT-D / CRT-I / CRT-SC / CRT-T
4) Mapping Explorer — structural views once governance catalogues exist
"""

from __future__ import annotations

# -------------------------------------------------------------------------------------------------
# Standard Library
# -------------------------------------------------------------------------------------------------
import re
import os
import sys
import json
import shutil
import glob
from datetime import datetime
from io import StringIO
from typing import List, Optional, Tuple, Dict, Any

# -------------------------------------------------------------------------------------------------
# Path Setup
# -------------------------------------------------------------------------------------------------
# Ensure we can import from the project root / core / apps when running from /pages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))

# -------------------------------------------------------------------------------------------------
# Third-party Libraries
# -------------------------------------------------------------------------------------------------
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------------------------------------
# Core Utilities
# -------------------------------------------------------------------------------------------------
from core.helpers import (  # pylint: disable=import-error
    get_named_paths,
    load_markdown_file,
    build_sidebar_links,
)

# -------------------------------------------------------------------------------------------------
# Resolve Key Paths (for modules under /pages)
# -------------------------------------------------------------------------------------------------
PATHS = get_named_paths(__file__)
# For files in /pages, level_up_1 is the project root: /cyber-resilience-tools
PROJECT_PATH = PATHS["level_up_1"]

ABOUT_APP_MD = os.path.join(PROJECT_PATH, "docs", "about_structural_controls_frameworks.md")
HELP_STC_MD = os.path.join(PROJECT_PATH, "docs", "help_structural_controls_frameworks.md")
HELP_OS_MD = os.path.join(PROJECT_PATH, "docs", "help_operational_extensions.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")
BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# CRT catalogue / samples CSV directory
CRT_CATALOGUE_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "crt_catalogues")
CRT_CATALOGUES_JSON_DIR = os.path.join(CRT_CATALOGUE_DIR, "json")

SAMPLES_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "samples")

# -------------------------------------------------------------------------------------------------
# Catalogue Configuration
# -------------------------------------------------------------------------------------------------
CATALOGUES_CONFIG: Dict[str, Dict[str, Optional[str]]] = {
    # Core CRT Series (locked backbone)
    "CRT-G": {
        "filename": "CRT-G.csv",
# supported if edited manually, but not via UI
        "id_column": "group_id",
        "label": "📘 CRT-G — Group Domains",
        "group": "Core CRT Series",
        "description": (
            "Domain groupings used to organise CRT controls, failures, and compensations."
        ),
    },
    "CRT-C": {
        "filename": "CRT-C.csv",
"id_column": "control_id",
        "label": "🧱 CRT-C — Control Reference Catalogue",
        "group": "Core CRT Series",
        "description": (
            "Structural control coordinates for identity, data, monitoring, containment, "
            "governance, and more."
        ),
    },
    "CRT-F": {
        "filename": "CRT-F.csv",
"id_column": "failure_id",
        "label": "⚠️ CRT-F — Failure-Mode Dictionary",
        "group": "Core CRT Series",
        "description": (
            "Failure modes describing how systems degrade or collapse under stress."
        ),
    },
    "CRT-N": {
        "filename": "CRT-N.csv",
"id_column": "n_id",
        "label": "🧩 CRT-N — Compensating Controls Registry",
        "group": "Core CRT Series",
        "description": (
            "Compensating controls and adaptive mechanisms using NIST CSF 2.0–aligned \
            categorisation for portability and cross-framework traceability. CSF tags \
            are informational only."
        ),
    },

    # Operational Structure (organisation-specific extension surface)
    "CRT-AS": {
        "filename": "CRT-AS.csv",
"id_column": "asset_id",
        "label": "🛰 CRT-AS — Asset Surface Catalogue",
        "group": "Operational Structure",
        "description": (
            "Assets, exposure types, boundaries, and linked controls supporting the "
            "Attack Surface Mapper."
        ),
    },
    "CRT-D": {
        "filename": "CRT-D.csv",
"id_column": "data_id",
        "label": "📦 CRT-D — Data & Classification Catalogue",
        "group": "Operational Structure",
        "description": (
            "Data domains, classifications, regulatory flags, and lineage mappings across "
            "assets, identity, vendors, and telemetry."
        ),
    },
    "CRT-I": {
        "filename": "CRT-I.csv",
"id_column": "identity_id",
        "label": "🔐 CRT-I — Identity & Trust Anchors",
        "group": "Operational Structure",
        "description": (
            "Identity zones, trust anchors, privilege tiers, and structural mappings back "
            "to CRT controls."
        ),
    },
    "CRT-SC": {
        "filename": "CRT-SC.csv",
"id_column": "vendor_id",
        "label": "🚢 CRT-SC — Supply-Chain & Vendor Catalogue",
        "group": "Operational Structure",
        "description": (
            "Vendors, suppliers, and transitive dependencies, including obligations and "
            "control mappings."
        ),
    },
    "CRT-T": {
        "filename": "CRT-T.csv",
"id_column": "telemetry_id",
        "label": "📡 CRT-T — Telemetry & Signal Sources",
        "group": "Operational Structure",
        "description": (
            "Telemetry sources, log streams, and monitoring signals used by CRT modules."
        ),
    },
    # Governance catalogues (organisation-level frameworks & obligations)
    "CRT-UC": {
        "filename": "CRT-UC.csv",
"id_column": "user_control_id",
        "label": "🧭 CRT-UC — User Control Catalogue",
        "group": "Governance",
        "description": (
            "Organisation-specific control statements, including external frameworks such "
            "as ISO/SoGP/PCI mapped into CRT."
        ),
    },
    "CRT-REQ": {
        "filename": "CRT-REQ.csv",
"id_column": "requirement_id",
        "label": "📋 CRT-REQ — Requirements Catalogue",
        "group": "Governance",
        "description": (
            "Requirements across regulatory, standards-based, internal governance "
            "and synthetic frameworks, all mapped structurally to CRT-C controls."
        ),
    },
    "CRT-POL": {
        "filename": "CRT-POL.csv",
"id_column": "policy_id",
        "label": "📜 CRT-POL — Policy Catalogue",
        "group": "Governance",
        "description": (
            "High-level policy statements structuring governance intent and linkage to "
            "user controls and obligations."
        ),
    },
    "CRT-LR": {
        "filename": "CRT-LR.csv",
"id_column": "lr_id",
        "label": "⚖️ CRT-LR — Legal & Regulatory Obligations",
        "group": "Governance",
        "description": (
            "Legal, regulatory, and contractual obligations that influence control and "
            "policy design."
        ),
    },
    "CRT-STD": {
        "filename": "CRT-STD.csv",
"id_column": "standard_id",
        "label": "📏 CRT-STD — Standard Catalogue",
        "group": "Governance",
        "description": (
            "Standards that operationalise policies and link to detailed user controls."
        ),
    },
}

# Locked backbone: CRT-G/C/F/N cannot be edited via UI
LOCKED_CATALOGUES: List[str] = ["CRT-G", "CRT-C", "CRT-F", "CRT-N"]

# Operational and Governance catalogues can be edited as active working files
OPERATIONAL_CATALOGUES: List[str] = ["CRT-AS", "CRT-D", "CRT-I", "CRT-SC", "CRT-T"]
GOVERNANCE_CATALOGUES: List[str] = ["CRT-UC", "CRT-POL", "CRT-LR", "CRT-STD"]

# -------------------------------------------------------------------------------------------------
# CSV Reading Helpers (UTF-8 + Fallback)
# -------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------
# Small path helper
# -------------------------------------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    """Create directory if it does not exist (safe no-op if already present)."""
    if not path:
        return
    os.makedirs(path, exist_ok=True)

def read_csv_with_fallback(path: str) -> pd.DataFrame:
    """
    Safely read a CSV file, trying UTF-8 / UTF-8-SIG first, then Latin-1 as a fallback.

    This avoids UnicodeDecodeError when catalogues include extended characters or
    have been saved with a non-UTF-8 codepage via Excel or similar tools.
    """
    if not os.path.isfile(path):
        return pd.DataFrame()

    encodings = ("utf-8", "utf-8-sig", "latin1")
    last_error: Optional[Exception] = None

    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as exc:  # pragma: no cover - defensive
            last_error = exc
            continue
        except Exception as exc:  # pragma: no cover - defensive
            last_error = exc
            continue

    # Final, very defensive fallback: decode bytes as UTF-8 with replacement
    # so we never completely fail on encoding issues.
    try:
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        return pd.read_csv(StringIO(text))
    except Exception:
        # If even this fails, return empty but avoid crashing the app.
        return pd.DataFrame()


# -------------------------------------------------------------------------------------------------
# Data Loading Utilities (Platinum Simple Active + Defaults)
# -------------------------------------------------------------------------------------------------
def load_catalogue(name: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load ACTIVE working CSV and SHIPPED DEFAULT CSV for a given catalogue name.

    Returns:
        (df_effective, df_default, df_active)

    Behaviour (Platinum Simple):
    - Active working file is always: crt_catalogues/{filename}  (e.g., CRT-LR.csv)
    - Shipped default is always: apps/data_sources/defaults/{filename}
    - Effective = active if present else default
    - No *.user.csv layer exists.
    """
    if name not in CATALOGUES_CONFIG:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    cfg = CATALOGUES_CONFIG[name]
    filename = cfg.get("filename") or f"{name}.csv"

    active_path = os.path.join(CRT_CATALOGUE_DIR, filename)
    default_path = os.path.join(PROJECT_PATH, "apps", "data_sources", "defaults", filename)

    df_default = pd.DataFrame()
    df_active = pd.DataFrame()

    if os.path.isfile(default_path):
        df_default = read_csv_with_fallback(default_path).fillna("")

    if os.path.isfile(active_path):
        df_active = read_csv_with_fallback(active_path).fillna("")

    # Effective preference: active > default
    if not df_active.empty:
        df_effective = df_active.copy()
    else:
        df_effective = df_default.copy()

    return df_effective.fillna(""), df_default.fillna(""), df_active.fillna("")


def load_all_catalogues() -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict[str, pd.DataFrame]]]:
    """
    Load all catalogues (effective, plus raw active/default) according to CATALOGUES_CONFIG.

    Returns:
    - catalogues_effective: {name -> df_effective}
    - catalogues_raw: {name -> {"default": df_default, "active": df_active}}
    """
    catalogues_effective: Dict[str, pd.DataFrame] = {}
    catalogues_raw: Dict[str, Dict[str, pd.DataFrame]] = {}

    for name in CATALOGUES_CONFIG:
        df_effective, df_default, df_active = load_catalogue(name)
        catalogues_effective[name] = df_effective
        catalogues_raw[name] = {"default": df_default, "active": df_active}

    return catalogues_effective, catalogues_raw



# -------------------------------------------------------------------------------------------------
# Utility Functions for ID Handling
# -------------------------------------------------------------------------------------------------
def parse_id_list(value: str) -> List[str]:
    """
    Parse a delimited ID string into a list of IDs.

    Supports semicolons, commas, and newlines as separators so that both
    "FM-001;FM-002" and "FM-001, FM-002" styles work.
    """
    if not isinstance(value, str) or not value.strip():
        return []

    # Split on semicolons, commas, or newlines, then strip whitespace.
    parts = re.split(r"[;,\n]", value)
    return [p.strip() for p in parts if p.strip()]


def explode_mapped_ids(
    df: pd.DataFrame,
    source_col: str,
    target_col: str,
) -> pd.DataFrame:
    """
    Explode a delimited ID column into multiple rows.

    The source column may use semicolons, commas, or newlines as separators.
    Example:
        df_exploded = explode_mapped_ids(pol_df, "mapped_user_controls", "_user_control_id")
    """
    if df.empty or source_col not in df.columns:
        return pd.DataFrame()

    df_exploded = df.copy()
    # Use the same parser everywhere so commas/semicolons/newlines all work.
    df_exploded[target_col] = df_exploded[source_col].fillna("").apply(
        lambda v: parse_id_list(str(v))
    )
    df_exploded = df_exploded.explode(target_col)
    df_exploded = df_exploded[df_exploded[target_col].astype(str).str.strip() != ""]
    df_exploded[target_col] = df_exploded[target_col].astype(str).str.strip()
    return df_exploded

def get_catalogue_paths(name: str) -> Tuple[str, str]:
    """
    Resolve ACTIVE working path and SHIPPED DEFAULT path for a given catalogue.

    Returns:
        (active_path, default_path)
    """
    cfg = CATALOGUES_CONFIG[name]
    filename = cfg.get("filename") or f"{name}.csv"

    active_path = os.path.join(CRT_CATALOGUE_DIR, filename)
    default_path = os.path.join(PROJECT_PATH, "apps", "data_sources", "defaults", filename)
    return active_path, default_path


def load_catalogue_active_or_default(catalogue_key: str) -> Tuple[pd.DataFrame, str, str]:
    """
    Load a catalogue using the ACTIVE file when it exists, otherwise fall back
    to the SHIPPED DEFAULT.

    Returns:
      (df, active_path, default_path)
    """
    active_path, default_path = get_catalogue_paths(catalogue_key)

    if os.path.exists(active_path):
        df = read_csv_with_fallback(active_path)
    else:
        df = read_csv_with_fallback(default_path)

    return df, active_path, default_path


def overwrite_catalogue_with_backup(catalogue_key: str, uploaded_file) -> str:
    """
    Overwrite the ACTIVE working CSV for a catalogue and create a timestamped backup first.

    Behaviour:
    - Reads uploaded CSV
    - Backs up current ACTIVE file (if it exists) to:
        CRT_CATALOGUE_DIR/backup/{CATALOGUE}.{YYYYMMDD_HHMMSS}.csv
    - Overwrites ACTIVE file:
        CRT_CATALOGUE_DIR/{CATALOGUE}.csv
    - Returns the active_path written
    """
    if catalogue_key not in CATALOGUES_CONFIG:
        raise ValueError(f"Unknown catalogue key: {catalogue_key}")

    # Paths
    active_path, default_path = get_catalogue_paths(catalogue_key)
    backup_dir = os.path.join(CRT_CATALOGUE_DIR, "backup")
    _ensure_dir(backup_dir)

    # Read upload
    try:
        uploaded_df = pd.read_csv(uploaded_file)
    except Exception as exc:
        raise ValueError(f"Could not parse uploaded CSV — {exc}") from exc

    uploaded_df.columns = [str(c).strip() for c in uploaded_df.columns]

    # Backup current active (if present)
    if os.path.exists(active_path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{catalogue_key}.{ts}.csv"
        backup_path = os.path.join(backup_dir, backup_name)
        try:
            shutil.copy2(active_path, backup_path)
        except Exception as exc:
            raise ValueError(f"Could not create backup in /backup — {exc}") from exc

    # Overwrite active
    try:
        uploaded_df.to_csv(active_path, index=False, encoding="utf-8")
    except Exception as exc:
        raise ValueError(f"Could not write active catalogue CSV — {exc}") from exc

    return active_path



def load_catalogue_with_user_override(catalogue_key: str) -> Tuple[pd.DataFrame, str, str]:
    """Load a catalogue, preferring the active working file, falling back to shipped default.

    Returns:
      (effective_df, active_csv_path, default_csv_path)

    Notes:
    - CRT edits overwrite the active working file (e.g. CRT-LR.csv).
    - Shipped defaults in /defaults are restore references only.
    """
    active_csv_path, default_csv_path = get_catalogue_paths(catalogue_key)

    if os.path.exists(active_csv_path):
        df = read_csv_with_fallback(active_csv_path)
    else:
        df = read_csv_with_fallback(default_csv_path)

    return df, active_csv_path, default_csv_path


def get_latest_backup_path(catalogue_key: str) -> Optional[str]:
    """Return the most recent timestamped backup for a catalogue, if any."""
    backup_dir = os.path.join(CRT_CATALOGUE_DIR, "backup")
    pattern = os.path.join(backup_dir, f"{catalogue_key}.*.csv")
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else None


def write_catalogue_json_view(catalogue_key: str, df_effective: pd.DataFrame) -> str:
    """Persist a normalised JSON view of the effective catalogue.

    This is a reference model used across CRT for read-only inspection and bundle assembly.
    """
    _ensure_dir(CRT_CATALOGUES_JSON_DIR)

    out_path = os.path.join(CRT_CATALOGUES_JSON_DIR, f"{catalogue_key}.json")

    # Convert dataframe to list-of-records, ensuring NaNs become empty strings
    records = df_effective.fillna("").to_dict(orient="records")

    payload = {
        "catalogue": catalogue_key,
        "generated_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "rows": records,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return out_path

def rebuild_all_catalogue_json_views() -> Dict[str, str]:
    """Regenerate JSON views for all configured catalogues (including locked backbone)."""
    results: Dict[str, str] = {}
    for n in sorted(CATALOGUES_CONFIG.keys()):
        eff_df, _, _ = load_catalogue_with_user_override(n)
        results[n] = write_catalogue_json_view(n, eff_df)
    return results


def build_controls_failure_comp_views(
    control_ids: List[str],
    c_df: pd.DataFrame,
    f_df: pd.DataFrame,
    n_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Given a list of CRT-C control_ids, return:
    - controls_view: filtered CRT-C rows
    - failures_view: CRT-F rows referenced by those controls
    - comps_view: CRT-N rows referenced by those controls

    Column-name tolerant:
    - Any column whose name starts with 'mapped_fail' is treated as listing failure IDs.
    - Any column whose name starts with 'mapped_comp' is treated as listing compensating IDs.
    - For CRT-F, we accept 'failure_id' or 'failure_mode_id' as the ID column.
    - For CRT-N, we accept 'n_id', 'compensating_id', or 'compensating_control_id'
    as the ID column, but normalise to `n_id` for downstream use.
    """
    if not control_ids or c_df.empty or "control_id" not in c_df.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    controls_view = c_df[c_df["control_id"].isin(control_ids)].copy()
    if controls_view.empty:
        return controls_view, pd.DataFrame(), pd.DataFrame()

    # Find all relevant mapping columns on CRT-C
    failure_cols = [col for col in controls_view.columns if col.lower().startswith("mapped_fail")]
    comp_cols = [col for col in controls_view.columns if col.lower().startswith("mapped_comp")]

    all_failure_ids: List[str] = []
    all_comp_ids: List[str] = []

    for _, row in controls_view.iterrows():
        for col in failure_cols:
            all_failure_ids.extend(parse_id_list(str(row.get(col, ""))))
        for col in comp_cols:
            all_comp_ids.extend(parse_id_list(str(row.get(col, ""))))

    all_failure_ids = sorted(set(all_failure_ids))
    all_comp_ids = sorted(set(all_comp_ids))

    failures_view = pd.DataFrame()
    comps_view = pd.DataFrame()

    # ----- CRT-F (failures) -----
    if not f_df.empty and all_failure_ids:
        failure_id_col = None
        if "failure_id" in f_df.columns:
            failure_id_col = "failure_id"
        elif "failure_mode_id" in f_df.columns:
            failure_id_col = "failure_mode_id"

        if failure_id_col:
            failures_view = f_df[f_df[failure_id_col].isin(all_failure_ids)].copy()
            # Normalise to 'failure_id' so downstream code is consistent
            if failure_id_col != "failure_id":
                failures_view = failures_view.rename(columns={failure_id_col: "failure_id"})

    # ----- CRT-N (compensating controls) -----
    if not n_df.empty and all_comp_ids:
        comp_id_col = None
        if "n_id" in n_df.columns:
            comp_id_col = "n_id"
        elif "compensating_id" in n_df.columns:
            comp_id_col = "compensating_id"
        elif "compensating_control_id" in n_df.columns:
            comp_id_col = "compensating_control_id"

        if comp_id_col:
            comps_view = n_df[n_df[comp_id_col].isin(all_comp_ids)].copy()
            # Normalise to 'n_id'
            if comp_id_col != "n_id":
                comps_view = comps_view.rename(columns={comp_id_col: "n_id"})

    return controls_view, failures_view, comps_view


# -------------------------------------------------------------------------------------------------
# Generic Renderers
# -------------------------------------------------------------------------------------------------
def render_generic_catalogue(name: str, df: pd.DataFrame) -> None:
    """
    Generic browser for CRT-AS, CRT-D, CRT-I, CRT-SC, CRT-T.

    Provides:
    - Simple filters
    - Download CSV
    - Dataframe view
    """
    cfg = CATALOGUES_CONFIG[name]
    st.subheader(cfg["label"])
    st.markdown(cfg["description"])

    if df.empty:
        st.info("No data found for this catalogue yet.")
        return

    id_col = cfg["id_column"]
    cols = st.columns(2)
    with cols[0]:
        id_filter = st.text_input(
            f"Filter by {id_col} (contains)",
            key=f"{name.lower()}_id_filter",
        )
    with cols[1]:
        text_filter = st.text_input(
            "Filter by text (name/description contains)",
            key=f"{name.lower()}_text_filter",
        )

    df_view = df.copy()

    if id_filter and id_col in df_view.columns:
        df_view = df_view[df_view[id_col].astype(str).str.contains(id_filter, case=False)]

    if text_filter:
        mask = False
        for col in df_view.columns:
            if df_view[col].dtype == object:
                series = df_view[col].astype(str).str.contains(text_filter, case=False)
                mask = series if isinstance(mask, bool) else (mask | series)
        if not isinstance(mask, bool):
            df_view = df_view[mask]

    if not df_view.empty:
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"⬇️ Download {name} (CSV)",
            data=csv_bytes,
            file_name=f"{name.lower()}_filtered.csv",
            mime="text/csv",
        )

    st.dataframe(df_view, width="stretch")


# -------------------------------------------------------------------------------------------------
# Core CRT Series Renderers
# -------------------------------------------------------------------------------------------------
def render_crt_g(df: pd.DataFrame) -> None:
    """Render CRT-G domain groups."""
    st.subheader("📘 CRT-G — Group Domains")
    cfg = CATALOGUES_CONFIG["CRT-G"]
    st.markdown(cfg["description"])

    if df.empty:
        st.warning("No CRT-G data found. Ensure CRT-G.csv is available under crt_catalogues.")
        return

    cols = st.columns(2)
    with cols[0]:
        group_id_filter = st.text_input(
            "Filter by Group ID (e.g., CRT-G-01)",
            key="crt_g_group_id_filter",
        )
    with cols[1]:
        text_filter = st.text_input(
            "Filter by domain / description (contains)",
            key="crt_g_text_filter",
        )

    df_view = df.copy()
    if group_id_filter and "group_id" in df_view.columns:
        df_view = df_view[df_view["group_id"].astype(str).str.contains(group_id_filter, case=False)]
    if text_filter:
        mask = False
        for col in ["group_domain", "description"]:
            if col in df_view.columns:
                series = df_view[col].astype(str).str.contains(text_filter, case=False)
                mask = series if isinstance(mask, bool) else (mask | series)
        if not isinstance(mask, bool):
            df_view = df_view[mask]

    if not df_view.empty:
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CRT-G Domains (CSV)",
            data=csv_bytes,
            file_name="crt_g_domains.csv",
            mime="text/csv",
        )

    st.dataframe(df_view, width="stretch")


def render_crt_c(df: pd.DataFrame, df_g: pd.DataFrame) -> None:
    """Render CRT-C controls with group context."""
    st.subheader("🧱 CRT-C — Control Reference Catalogue")
    cfg = CATALOGUES_CONFIG["CRT-C"]
    st.markdown(cfg["description"])

    if df.empty:
        st.warning("No CRT-C data found. Ensure CRT-C.csv is available under crt_catalogues.")
        return

    cols = st.columns(3)
    with cols[0]:
        control_id_filter = st.text_input(
            "Filter by Control ID (e.g., C-001)",
            key="crt_c_control_id_filter",
        )
    with cols[1]:
        group_id_filter = st.text_input(
            "Filter by Group ID (e.g., CRT-G-01)",
            key="crt_c_group_id_filter",
        )
    with cols[2]:
        text_filter = st.text_input(
            "Filter by text (name/description contains)",
            key="crt_c_text_filter",
        )

    df_view = df.copy()
    if control_id_filter and "control_id" in df_view.columns:
        df_view = df_view[
            df_view["control_id"].astype(str).str.contains(control_id_filter, case=False)
        ]
    if group_id_filter and "group_id" in df_view.columns:
        df_view = df_view[
            df_view["group_id"].astype(str).str.contains(group_id_filter, case=False)
        ]
    if text_filter:
        mask = False
        # Be tolerant: scan across text-like columns
        for col in df_view.columns:
            if df_view[col].dtype == object and col not in ["control_id", "group_id"]:
                series = df_view[col].astype(str).str.contains(text_filter, case=False)
                mask = series if isinstance(mask, bool) else (mask | series)
        if not isinstance(mask, bool):
            df_view = df_view[mask]

    # Optional: join group domains
    if not df_g.empty and "group_id" in df_view.columns and "group_id" in df_g.columns:
        df_view = df_view.merge(
            df_g[["group_id", "group_domain"]],
            on="group_id",
            how="left",
            suffixes=("", "_group"),
        )

    if not df_view.empty:
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CRT-C Controls (CSV)",
            data=csv_bytes,
            file_name="crt_c_controls.csv",
            mime="text/csv",
        )

    st.dataframe(df_view, width="stretch")


def render_crt_f(df: pd.DataFrame) -> None:
    """Render CRT-F failure modes."""
    st.subheader("⚠️ CRT-F — Failure-Mode Dictionary")
    cfg = CATALOGUES_CONFIG["CRT-F"]
    st.markdown(cfg["description"])

    if df.empty:
        st.warning("No CRT-F data found. Ensure CRT-F.csv is available under crt_catalogues.")
        return

    cols = st.columns(2)
    with cols[0]:
        failure_id_filter = st.text_input(
            "Filter by Failure ID (e.g., F-001)",
            key="crt_f_failure_id_filter",
        )
    with cols[1]:
        text_filter = st.text_input(
            "Filter by text (name/description contains)",
            key="crt_f_text_filter",
        )

    df_view = df.copy()
    if failure_id_filter and "failure_id" in df_view.columns:
        df_view = df_view[
            df_view["failure_id"].astype(str).str.contains(failure_id_filter, case=False)
        ]
    if text_filter:
        mask = False
        # Be tolerant: scan all text-like columns except the ID
        for col in df_view.columns:
            if col == "failure_id":
                continue
            if df_view[col].dtype == object:
                series = df_view[col].astype(str).str.contains(text_filter, case=False)
                mask = series if isinstance(mask, bool) else (mask | series)
        if not isinstance(mask, bool):
            df_view = df_view[mask]

    if not df_view.empty:
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CRT-F Failure Modes (CSV)",
            data=csv_bytes,
            file_name="crt_f_failures.csv",
            mime="text/csv",
        )

    st.dataframe(df_view, width="stretch")


def render_crt_n(df: pd.DataFrame) -> None:
    """Render CRT-N compensating controls."""
    st.subheader("🧩 CRT-N — Compensating Controls Registry")
    cfg = CATALOGUES_CONFIG["CRT-N"]
    st.markdown(cfg["description"])

    if df.empty:
        st.warning("No CRT-N data found. Ensure CRT-N.csv is available under crt_catalogues.")
        return

    cols = st.columns(2)
    with cols[0]:
        comp_id_filter = st.text_input(
            "Filter by Compensating ID (e.g., CRT-N-0001)",
            key="crt_n_comp_id_filter",
        )
    with cols[1]:
        text_filter = st.text_input(
            "Filter by text (name/description contains)",
            key="crt_n_text_filter",
        )

    df_view = df.copy()
    if comp_id_filter and "n_id" in df_view.columns:
        df_view = df_view[
            df_view["n_id"].astype(str).str.contains(comp_id_filter, case=False)
        ]
    if text_filter:
        mask = False
        # Tolerant text search: all string columns except the ID
        for col in df_view.columns:
            if col == "n_id":
                continue
            if df_view[col].dtype == object:
                series = df_view[col].astype(str).str.contains(text_filter, case=False)
                mask = series if isinstance(mask, bool) else (mask | series)
        if not isinstance(mask, bool):
            df_view = df_view[mask]

    if not df_view.empty:
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CRT-N Compensating Controls (CSV)",
            data=csv_bytes,
            file_name="crt_n_compensations.csv",
            mime="text/csv",
        )

    st.dataframe(df_view, width="stretch")


# -------------------------------------------------------------------------------------------------
# Governance Mapping Lenses
# -------------------------------------------------------------------------------------------------
def render_user_control_lens(
    uc_df: pd.DataFrame,
    c_df: pd.DataFrame,
    pol_df: pd.DataFrame,
    lr_df: pd.DataFrame,
) -> None:
    """
    Lens anchored on CRT-UC (user controls).
    Shows how a selected user control links to CRT controls, policies, and obligations.
    """
    if uc_df.empty:
        st.info("No user controls found in CRT-UC catalogue.")
        return

    st.markdown("### 🔍 User Control Lens (CRT-UC as anchor)")

    # Select user control
    uc_options = uc_df["user_control_id"].tolist()
    uc_labels = {
        row["user_control_id"]: f"{row['user_control_id']} — {row.get('user_control_name', '')}"
        for _, row in uc_df.iterrows()
        if "user_control_id" in row
    }

    selected_uc_id = st.selectbox(
        "Select a user control",
        options=uc_options,
        format_func=lambda x: uc_labels.get(x, x),
    )

    sel_row = uc_df[uc_df["user_control_id"] == selected_uc_id].iloc[0]

    st.markdown("#### 🎯 Selected User Control")
    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.write(f"**ID:** {sel_row.get('user_control_id', '')}")
        st.write(f"**Name:** {sel_row.get('user_control_name', '')}")
        st.write(f"**Framework:** {sel_row.get('framework_name', '')}")
    with meta_cols[1]:
        st.write(f"**Domain:** {sel_row.get('domain', '')}")
        st.write(f"**Status:** {sel_row.get('status', '')}")

    st.markdown("**Summary (structural, not prescriptive)**")
    st.write(sel_row.get("control_summary", ""))

    # Linked CRT Controls
    st.markdown("#### 🧱 Linked CRT Controls (CRT-C)")
    mapped_controls = parse_id_list(sel_row.get("mapped_crt_controls", ""))
    if not mapped_controls or c_df.empty or "control_id" not in c_df.columns:
        st.info("No CRT controls mapped to this user control yet.")
    else:
        df_controls = c_df[c_df["control_id"].isin(mapped_controls)].copy()
        if df_controls.empty:
            st.info("Mapped CRT controls not found in CRT-C catalogue.")
        else:
            st.dataframe(df_controls, width="stretch")

    # Linked Policies
    st.markdown("#### 📜 Linked Policies (CRT-POL)")
    pol_uc_exploded = explode_mapped_ids(pol_df, "mapped_user_controls", "_user_control_id")
    if pol_uc_exploded.empty or "_user_control_id" not in pol_uc_exploded.columns:
        st.info("No policies reference this user control yet.")
    else:
        df_pols = pol_uc_exploded[pol_uc_exploded["_user_control_id"] == selected_uc_id].copy()
        df_pols = df_pols.drop(columns=["_user_control_id"], errors="ignore")
        if df_pols.empty:
            st.info("No policies linked to this user control.")
        else:
            st.dataframe(df_pols, width="stretch")

    # Linked Obligations
    st.markdown("#### ⚖️ Linked Obligations (CRT-LR)")
    lr_uc_exploded = explode_mapped_ids(lr_df, "mapped_user_controls", "_user_control_id")
    if lr_uc_exploded.empty or "_user_control_id" not in lr_uc_exploded.columns:
        st.info("No obligations reference this user control yet.")
    else:
        df_lr = lr_uc_exploded[lr_uc_exploded["_user_control_id"] == selected_uc_id].copy()
        df_lr = df_lr.drop(columns=["_user_control_id"], errors="ignore")
        if df_lr.empty:
            st.info("No obligations linked to this user control.")
        else:
            st.dataframe(df_lr, width="stretch")


# -------------------------------------------------------------------------------------------------
# Requirements Mapping
# -------------------------------------------------------------------------------------------------
def render_requirement_lens(
    req_df: pd.DataFrame,
    c_df: pd.DataFrame,
    pol_df: pd.DataFrame,
    std_df: pd.DataFrame,
    lr_df: pd.DataFrame,
    f_df: pd.DataFrame,
    n_df: pd.DataFrame,
) -> None:
    """
    Lens anchored on CRT-REQ (requirements).

    Behaviour is intentionally similar to Policy / Standard lenses:

    For a selected requirement:
    - Show requirement meta (set, ref, name, text, category, source).
    - Build a CRT-C "Control Bundle" via mapped_control_ids.
    - Allow drill-down into a single control from that bundle.
    - For that control, show:
        • Failure Modes (CRT-F)
        • Compensating Controls (CRT-N)
        • Obligations (CRT-LR) for this control
    - For the whole requirement bundle, show:
        • Failure Modes (CRT-F) across bundle
        • Compensating Controls (CRT-N) across bundle
        • Obligations (CRT-LR) across bundle

    All relationships are derived via CRT-C:
        REQ.mapped_control_ids <-> CRT-C.control_id
        POL.mapped_control_ids <-> CRT-C.control_id
        STD.mapped_control_ids <-> CRT-C.control_id
        LR.mapped_control_ids  <-> CRT-C.control_id
    """
    if req_df.empty:
        st.info("No requirements found in CRT-REQ catalogue.")
        return

    if "requirement_id" not in req_df.columns:
        st.error("CRT-REQ catalogue is missing the 'requirement_id' column.")
        return

    st.markdown("### 📋 Requirements Lens (CRT-REQ as anchor)")

    # ----------------------------
    # 1) Select a requirement set (framework / source)
    # ----------------------------
    if "requirement_set_id" in req_df.columns:
        # Normalise to strings and unique values
        set_ids = sorted(
            {
                str(v)
                for v in req_df["requirement_set_id"].dropna().unique().tolist()
                if str(v).strip()
            }
        )
    else:
        set_ids = []

    # If there are no set IDs, we just operate over the full dataframe
    selected_set_id: Optional[str] = None
    filtered_req_df = req_df

    if set_ids:
        # We *do not* offer "All" here by design: we want a clean separation
        # between frameworks / sources to avoid cross-mixing.
        selected_set_id = st.selectbox(
            "Select a requirement set (framework / source)",
            options=set_ids,
            index=0,
        )
        filtered_req_df = req_df[req_df["requirement_set_id"] == selected_set_id].copy()

        if filtered_req_df.empty:
            st.info(
                f"No requirements found for requirement_set_id '{selected_set_id}'. "
                "Check CRT-REQ.csv for consistency."
            )
            return

    # ----------------------------
    # 2) Select a requirement within that set
    # ----------------------------
    req_labels: Dict[str, str] = {}
    for _, row in filtered_req_df.iterrows():
        rid = row.get("requirement_id")
        if not isinstance(rid, str):
            continue

        name = row.get("requirement_name", "") or ""
        ref = row.get("requirement_ref", "") or ""
        set_id = row.get("requirement_set_id", "") or ""

        label = rid
        if name:
            label += f" — {name}"

        trailing_bits = []
        if ref:
            trailing_bits.append(ref)
        if set_id:
            trailing_bits.append(set_id)
        if trailing_bits:
            label += f" ({', '.join(trailing_bits)})"

        req_labels[rid] = label

    req_options = list(req_labels.keys())
    if not req_options:
        st.info("No requirement IDs available in the filtered CRT-REQ catalogue.")
        return

    selected_req_id = st.selectbox(
        "Select a requirement",
        options=req_options,
        format_func=lambda x: req_labels.get(x, x),
    )

    sel_row = filtered_req_df[filtered_req_df["requirement_id"] == selected_req_id].iloc[0]

    # ----------------------------
    # 3) Requirement metadata
    # ----------------------------
    st.markdown("#### 🧾 Requirement Overview")

    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.write(f"**Requirement Set:** {sel_row.get('requirement_set_id', '')}")
        st.write(f"**Requirement ID:** {sel_row.get('requirement_id', '')}")
        ref = sel_row.get("requirement_ref", "")
        if isinstance(ref, str) and ref.strip():
            st.write(f"**Reference:** {ref}")

    with meta_cols[1]:
        cat = sel_row.get("requirement_category", "")
        subcat = sel_row.get("requirement_subcategory", "")
        if isinstance(cat, str) and cat.strip():
            st.write(f"**Category:** {cat}")
        if isinstance(subcat, str) and subcat.strip():
            st.write(f"**Subcategory:** {subcat}")
        src = sel_row.get("source_ref", "")
        if isinstance(src, str) and src.strip():
            st.write(f"**Source:** {src}")

    text = sel_row.get("requirement_text", "")
    if isinstance(text, str) and text.strip():
        st.markdown("**Requirement Text**")
        st.write(text)

    rationale = sel_row.get("rationale_summary", "")
    if isinstance(rationale, str) and rationale.strip():
        st.markdown("**Rationale Summary**")
        st.write(rationale)

    notes = sel_row.get("notes", "")
    if isinstance(notes, str) and notes.strip():
        st.markdown("**Notes**")
        st.write(notes)

    # ----------------------------
    # 4) Control bundle (CRT-C + F + N)
    # ----------------------------
    st.markdown("#### 🧱 Control Bundle for this Requirement (CRT-C)")

    bundle_control_ids: List[str] = parse_id_list(sel_row.get("mapped_control_ids", ""))

    if not bundle_control_ids:
        st.info("This requirement has no mapped CRT controls (mapped_control_ids is empty).")
        return

    if c_df.empty or "control_id" not in c_df.columns:
        st.warning("CRT-C catalogue not loaded or missing 'control_id' column.")
        return

    controls_view, failures_view, comps_view = build_controls_failure_comp_views(
        bundle_control_ids,
        c_df,
        f_df,
        n_df,
    )

    if controls_view.empty:
        st.info(
            "No CRT controls matching this requirement's mapped_control_ids were found in CRT-C. "
            "Check for ID mismatches between CRT-REQ.mapped_control_ids and CRT-C.control_id."
        )
        return

    display_cols = []
    for col in [
        "control_id",
        "control_name",
        "group_domain",
        "sub_domain",
        "type",
        "function",
        "risk_level",
    ]:
        if col in controls_view.columns:
            display_cols.append(col)

    st.dataframe(
        controls_view[display_cols] if display_cols else controls_view,
        width="stretch",
    )

    # ----------------------------
    # 5) Pick a specific control from the bundle
    # ----------------------------
    st.markdown("#### 🎯 Focus on a Single Control in the Bundle")

    control_labels = {
        row["control_id"]: f"{row['control_id']} — {row.get('control_name', '')}"
        for _, row in controls_view.iterrows()
        if isinstance(row.get("control_id"), str)
    }
    control_ids = list(control_labels.keys())

    selected_control_id = st.selectbox(
        "Select a CRT control from this requirement's bundle",
        options=control_ids,
        format_func=lambda cid: control_labels.get(cid, cid),
    )

    control_row = controls_view[controls_view["control_id"] == selected_control_id].iloc[0]

    st.markdown("##### 🧩 Control Detail (CRT-C)")
    with st.expander("View control metadata", expanded=True):
        c_meta_cols = st.columns(2)
        with c_meta_cols[0]:
            st.write(f"**Control ID:** {control_row.get('control_id', '')}")
            st.write(f"**Name:** {control_row.get('control_name', '')}")
            st.write(f"**Group:** {control_row.get('group_domain', '')}")
            st.write(f"**Sub-domain:** {control_row.get('sub_domain', '')}")
        with c_meta_cols[1]:
            st.write(f"**Type:** {control_row.get('type', '')}")
            st.write(f"**Function:** {control_row.get('function', '')}")
            st.write(f"**Risk Level:** {control_row.get('risk_level', '')}")

        desc_c = control_row.get("description", "")
        if isinstance(desc_c, str) and desc_c.strip():
            st.markdown("**Description**")
            st.write(desc_c)

        obj = control_row.get("objective", "")
        if isinstance(obj, str) and obj.strip():
            st.markdown("**Objective**")
            st.write(obj)

        ctx = control_row.get("deployment_exposure_context", "")
        if isinstance(ctx, str) and ctx.strip():
            st.markdown("**Deployment / Exposure Context**")
            st.write(ctx)

        scope = control_row.get("use_case_scope", "")
        if isinstance(scope, str) and scope.strip():
            st.markdown("**Use-Case Scope**")
            st.write(scope)

    # ----------------------------
    # 6) Failure Modes & Compensating Controls – per-control
    # ----------------------------
    st.markdown("##### ⚠️ CRT-F — Failure Modes for this Control")

    control_failure_ids: List[str] = []
    for col in control_row.index:
        if col.lower().startswith("mapped_fail"):
            control_failure_ids.extend(parse_id_list(str(control_row.get(col, ""))))
    control_failure_ids = sorted(set(control_failure_ids))

    if not control_failure_ids or failures_view.empty:
        st.info("No failure modes mapped for this control.")
    else:
        cf = failures_view[failures_view["failure_id"].isin(control_failure_ids)].copy()
        if cf.empty:
            st.info("No failure modes found in CRT-F for this control's mappings.")
        else:
            show_cols = [
                col
                for col in ["failure_id", "failure_name", "failure_category",
                "failure_description"]
                if col in cf.columns
            ]
            st.dataframe(cf[show_cols] if show_cols else cf, width="stretch")

    st.markdown("##### 🧩 CRT-N — Compensating Controls for this Control")

    control_comp_ids: List[str] = []
    for col in control_row.index:
        if col.lower().startswith("mapped_comp"):
            control_comp_ids.extend(parse_id_list(str(control_row.get(col, ""))))
    control_comp_ids = sorted(set(control_comp_ids))

    if not control_comp_ids or comps_view.empty:
        st.info("No compensating controls mapped for this control.")
    else:
        if "n_id" in comps_view.columns:
            cn = comps_view[comps_view["n_id"].isin(control_comp_ids)].copy()
        else:
            cn = comps_view.copy()

        if cn.empty:
            st.info("No compensating controls found in CRT-N for this control's mappings.")
        else:
            show_cols = [
                col
                for col in ["n_id", "compensating_name", "strength", "csf_category"]
                if col in cn.columns
            ]
            st.dataframe(cn[show_cols] if show_cols else cn, width="stretch")

    # ----------------------------
    # 7) Obligations – per-control view (CRT-LR)
    # ----------------------------
    st.markdown("#### ⚖️ CRT-LR — Obligations for this Control")

    if lr_df.empty or "mapped_control_ids" not in lr_df.columns:
        st.info("CRT-LR catalogue not loaded or missing 'mapped_control_ids' for obligations.")
    else:
        lr_exploded = explode_mapped_ids(lr_df, "mapped_control_ids", "_control_id")

        if lr_exploded.empty or "_control_id" not in lr_exploded.columns:
            st.info("No obligations are currently mapped to any controls in CRT-LR.")
        else:
            lr_for_control = lr_exploded[lr_exploded["_control_id"] == selected_control_id].copy()
            if lr_for_control.empty:
                st.info(f"No CRT-LR obligations mapped to control {selected_control_id}.")
            else:
                lr_display_cols = []
                for col in [
                    "lr_id",
                    "obligation_name",
                    "obligation_description",
                    "severity",
                    "evidence_required",
                    "source_reference_examples",
                ]:
                    if col in lr_for_control.columns:
                        lr_display_cols.append(col)

                st.dataframe(lr_for_control[lr_display_cols], width="stretch")

    # ----------------------------
    # 8) Obligations – requirement bundle summary (CRT-LR)
    # ----------------------------
    st.markdown("#### 📊 CRT-LR — Obligations Across this Requirement's Control Bundle")

    if lr_df.empty or "mapped_control_ids" not in lr_df.columns:
        st.info("CRT-LR catalogue not loaded or missing 'mapped_control_ids'.")
    else:
        lr_exploded = explode_mapped_ids(lr_df, "mapped_control_ids", "_control_id")

        if lr_exploded.empty or "_control_id" not in lr_exploded.columns:
            st.info("No obligations are mapped to any CRT controls yet.")
        else:
            lr_for_req = lr_exploded[lr_exploded["_control_id"].isin(bundle_control_ids)].copy()
            if lr_for_req.empty:
                st.info("No CRT-LR obligations mapped via this requirement's CRT controls.")
            else:
                if "lr_id" in lr_for_req.columns:
                    lr_for_req = lr_for_req.drop_duplicates(subset=["lr_id"])

                lr_req_cols = []
                for col in [
                    "lr_id",
                    "obligation_name",
                    "obligation_description",
                    "severity",
                    "evidence_required",
                    "source_reference_examples",
                ]:
                    if col in lr_for_req.columns:
                        lr_req_cols.append(col)

                st.dataframe(lr_for_req[lr_req_cols], width="stretch")

    # ----------------------------
    # 9) Failure Modes & Compensations – requirement bundle summaries
    # ----------------------------
    st.markdown("#### 📊 CRT-F — Failure Modes for this Requirement's Control Bundle")
    if failures_view.empty:
        st.info("No failure modes mapped via the CRT controls for this requirement.")
    else:
        show_cols = [
            col
            for col in ["failure_id", "failure_name", "failure_category", "failure_description"]
            if col in failures_view.columns
        ]
        st.dataframe(
            failures_view[show_cols].drop_duplicates() if show_cols
            else failures_view.drop_duplicates(),
            width="stretch",
        )

    st.markdown("#### 📊 CRT-N — Compensating Controls for this Requirement's Control Bundle")
    if comps_view.empty:
        st.info("No compensating controls mapped via the CRT controls for this requirement.")
    else:
        show_cols = [
            col
            for col in ["n_id", "compensating_name", "strength", "csf_category"]
            if col in comps_view.columns
        ]
        st.dataframe(
            comps_view[show_cols].drop_duplicates() if show_cols else comps_view.drop_duplicates(),
            width="stretch",
        )

# -------------------------------------------------------------------------------------------------
# Policy Mapping
# -------------------------------------------------------------------------------------------------
def render_policy_lens(
    pol_df: pd.DataFrame,
    uc_df: pd.DataFrame,
    c_df: pd.DataFrame,
    lr_df: pd.DataFrame,
    f_df: pd.DataFrame,
    n_df: pd.DataFrame,
) -> None:
    """
    Policy-centric view.

    • Anchor: CRT-POL (policy catalogue)
    • Forward path: POL -> mapped_control_ids (CRT-C)
    • Then: CRT-C -> bundle table + per-control drill-down
    • Obligations (CRT-LR) are derived by matching CRT-LR.mapped_control_ids
      against the controls in the bundle.
    • Failure Modes (CRT-F) and Compensating Controls (CRT-N) are resolved via
      CRT-C.mapped_fail* / mapped_comp* for the bundle and per-control views.

    Note:
    - Policy / Standard "sections" fields are *template* structure for AI flows.
      They are intentionally not surfaced here to keep this view structural.
    """
    if pol_df.empty:
        st.info("No policies found in CRT-POL catalogue.")
        return

    st.markdown("### 📜 Policy Lens (CRT-POL as anchor)")

    # ----------------------------
    # 1) Select a policy
    # ----------------------------
    if "policy_id" not in pol_df.columns:
        st.error("CRT-POL catalogue is missing the 'policy_id' column.")
        return

    pol_labels = {
        row["policy_id"]: f"{row['policy_id']} — {row.get('policy_name', '')}"
        for _, row in pol_df.iterrows()
        if isinstance(row.get("policy_id"), str)
    }

    policy_ids = list(pol_labels.keys())
    if not policy_ids:
        st.info("No policy IDs available in CRT-POL catalogue.")
        return

    selected_pol_id = st.selectbox(
        "Select a policy to explore",
        options=policy_ids,
        format_func=lambda pid: pol_labels.get(pid, pid),
    )

    pol_row = pol_df[pol_df["policy_id"] == selected_pol_id].iloc[0]

    # ----------------------------
    # Policy metadata
    # ----------------------------
    st.markdown("#### 🧾 Policy Overview")

    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.write(f"**Policy ID:** {pol_row.get('policy_id', '')}")
        st.write(f"**Name:** {pol_row.get('policy_name', '')}")

    with meta_cols[1]:
        mapped_standards = parse_id_list(pol_row.get("mapped_standard_ids", ""))
        if mapped_standards:
            st.write("**Mapped Standards (STD-IDs):** " + ", ".join(mapped_standards))

    desc = pol_row.get("description", "")
    if isinstance(desc, str) and desc.strip():
        st.markdown("**Description**")
        st.write(desc)

    # NOTE: We intentionally do NOT render policy_sections here,
    # as sections belong to AI orchestration templates.

    # ----------------------------
    # 2) Control bundle (CRT-C + F + N)
    # ----------------------------
    st.markdown("#### 🧱 Control Bundle for this Policy (CRT-C)")

    bundle_control_ids: List[str] = parse_id_list(pol_row.get("mapped_control_ids", ""))

    if not bundle_control_ids:
        st.info("This policy has no mapped CRT controls (mapped_control_ids is empty).")
        return

    if c_df.empty or "control_id" not in c_df.columns:
        st.warning("CRT-C catalogue not loaded or missing 'control_id' column.")
        return

    controls_view, failures_view, comps_view = build_controls_failure_comp_views(
        bundle_control_ids,
        c_df,
        f_df,
        n_df,
    )

    if controls_view.empty:
        st.warning(
            "None of the mapped CRT control IDs for this policy were found in CRT-C. "
            "Check for ID mismatches between CRT-POL.mapped_control_ids and CRT-C.control_id."
        )
        return

    # Lightweight projection for the bundle table
    display_cols = []
    for col in [
        "control_id",
        "control_name",
        "group_domain",
        "sub_domain",
        "type",
        "function",
        "risk_level",
    ]:
        if col in controls_view.columns:
            display_cols.append(col)

    st.dataframe(controls_view[display_cols], width='stretch')

    # ----------------------------
    # 3) Pick a specific control from the bundle
    # ----------------------------
    st.markdown("#### 🎯 Focus on a Single Control in the Bundle")

    control_labels = {
        row["control_id"]: f"{row['control_id']} — {row.get('control_name', '')}"
        for _, row in controls_view.iterrows()
        if isinstance(row.get("control_id"), str)
    }
    control_ids = list(control_labels.keys())

    selected_control_id = st.selectbox(
        "Select a CRT control from this policy bundle",
        options=control_ids,
        format_func=lambda cid: control_labels.get(cid, cid),
    )

    control_row = controls_view[controls_view["control_id"] == selected_control_id].iloc[0]

    st.markdown("##### 🧩 Control Detail (CRT-C)")
    with st.expander("View control metadata", expanded=True):
        meta_cols = st.columns(2)
        with meta_cols[0]:
            st.write(f"**Control ID:** {control_row.get('control_id', '')}")
            st.write(f"**Name:** {control_row.get('control_name', '')}")
            st.write(f"**Group:** {control_row.get('group_domain', '')}")
            st.write(f"**Sub-domain:** {control_row.get('sub_domain', '')}")
        with meta_cols[1]:
            st.write(f"**Type:** {control_row.get('type', '')}")
            st.write(f"**Function:** {control_row.get('function', '')}")
            st.write(f"**Risk Level:** {control_row.get('risk_level', '')}")

        desc = control_row.get("description", "")
        if isinstance(desc, str) and desc.strip():
            st.markdown("**Description**")
            st.write(desc)

        obj = control_row.get("objective", "")
        if isinstance(obj, str) and obj.strip():
            st.markdown("**Objective**")
            st.write(obj)

        ctx = control_row.get("deployment_exposure_context", "")
        if isinstance(ctx, str) and ctx.strip():
            st.markdown("**Deployment / Exposure Context**")
            st.write(ctx)

        scope = control_row.get("use_case_scope", "")
        if isinstance(scope, str) and scope.strip():
            st.markdown("**Use-Case Scope**")
            st.write(scope)

    # ----------------------------
    # 4) Failure Modes & Compensating Controls – per-control
    # ----------------------------
    st.markdown("##### ⚠️ CRT-F — Failure Modes for this Control")

    control_failure_ids: List[str] = []
    for col in control_row.index:
        if col.lower().startswith("mapped_fail"):
            control_failure_ids.extend(parse_id_list(str(control_row.get(col, ""))))
    control_failure_ids = sorted(set(control_failure_ids))

    if not control_failure_ids or failures_view.empty:
        st.info("No failure modes mapped for this control.")
    else:
        cf = failures_view[failures_view["failure_id"].isin(control_failure_ids)].copy()
        if cf.empty:
            st.info("No failure modes found in CRT-F for this control's mappings.")
        else:
            show_cols = [
                col
                for col in ["failure_id", "failure_name", "failure_category", "failure_description"]
                if col in cf.columns
            ]
            st.dataframe(cf[show_cols] if show_cols else cf, width='stretch')

    st.markdown("##### 🧩 CRT-N — Compensating Controls for this Control")

    control_comp_ids: List[str] = []
    for col in control_row.index:
        if col.lower().startswith("mapped_comp"):
            control_comp_ids.extend(parse_id_list(str(control_row.get(col, ""))))
    control_comp_ids = sorted(set(control_comp_ids))

    if not control_comp_ids or comps_view.empty:
        st.info("No compensating controls mapped for this control.")
    else:
        # `comps_view` has been normalised to `n_id`
        if "n_id" in comps_view.columns:
            cn = comps_view[comps_view["n_id"].isin(control_comp_ids)].copy()
        else:
            cn = comps_view.copy()

        if cn.empty:
            st.info("No compensating controls found in CRT-N for this control's mappings.")
        else:
            show_cols = [
                col
                for col in ["n_id", "compensating_name", "strength", "csf_category"]
                if col in cn.columns
            ]
            st.dataframe(cn[show_cols] if show_cols else cn, width='stretch')

    # ----------------------------
    # 5) Obligations – per-control view (CRT-LR)
    # ----------------------------
    st.markdown("#### ⚖️ CRT-LR — Obligations for this Control")

    if lr_df.empty or "mapped_control_ids" not in lr_df.columns:
        st.info("CRT-LR catalogue not loaded or missing 'mapped_control_ids' for obligations.")
    else:
        # Explode CRT-LR by mapped_control_ids -> _control_id
        lr_exploded = explode_mapped_ids(lr_df, "mapped_control_ids", "_control_id")

        if lr_exploded.empty or "_control_id" not in lr_exploded.columns:
            st.info("No obligations are currently mapped to any controls in CRT-LR.")
        else:
            lr_for_control = lr_exploded[lr_exploded["_control_id"] == selected_control_id].copy()
            if lr_for_control.empty:
                st.info(f"No CRT-LR obligations mapped to control {selected_control_id}.")
            else:
                lr_display_cols = []
                for col in [
                    "lr_id",
                    "obligation_name",
                    "obligation_description",
                    "severity",
                    "evidence_required",
                    "source_reference_examples",
                ]:
                    if col in lr_for_control.columns:
                        lr_display_cols.append(col)

                st.dataframe(lr_for_control[lr_display_cols], width="stretch")

                st.divider()


    # ----------------------------
    # 6) Failure Modes & Compensations – policy bundle summaries
    # ----------------------------
    st.markdown("#### 📊 CRT-F — Failure Modes for this Policy's Control Bundle")
    if failures_view.empty:
        st.info("No failure modes mapped via the CRT controls for this policy.")
    else:
        show_cols = [
            col
            for col in ["failure_id", "failure_name", "failure_category", "failure_description"]
            if col in failures_view.columns
        ]
        st.dataframe(
            failures_view[show_cols].drop_duplicates() if show_cols
            else failures_view.drop_duplicates(),
            width='stretch',
        )

    st.markdown("#### 📊 CRT-N — Compensating Controls for this Policy's Control Bundle")
    if comps_view.empty:
        st.info("No compensating controls mapped via the CRT controls for this policy.")
    else:
        show_cols = [
            col
            for col in ["n_id", "compensating_name", "strength", "csf_category"]
            if col in comps_view.columns
        ]
        st.dataframe(
            comps_view[show_cols].drop_duplicates() if show_cols else comps_view.drop_duplicates(),
            width='stretch',
        )

    # ----------------------------
    # 7) Obligations – policy bundle summary (CRT-LR)
    # ----------------------------
    st.markdown("#### 📊 CRT-LR — Obligations Across this Policy's Control Bundle")

    if lr_df.empty or "mapped_control_ids" not in lr_df.columns:
        st.info("CRT-LR catalogue not loaded or missing 'mapped_control_ids'.")
    else:
        lr_exploded = explode_mapped_ids(lr_df, "mapped_control_ids", "_control_id")

        if lr_exploded.empty or "_control_id" not in lr_exploded.columns:
            st.info("No obligations are mapped to any CRT controls yet.")
        else:
            lr_for_policy = lr_exploded[lr_exploded["_control_id"].isin(bundle_control_ids)].copy()
            if lr_for_policy.empty:
                st.info("No CRT-LR obligations mapped via this policy's CRT controls.")
            else:
                # Deduplicate so each LR obligation appears once per policy
                if "lr_id" in lr_for_policy.columns:
                    lr_for_policy = lr_for_policy.drop_duplicates(subset=["lr_id"])

                lr_policy_cols = []
                for col in [
                    "lr_id",
                    "obligation_name",
                    "obligation_description",
                    "severity",
                    "evidence_required",
                    "source_reference_examples",
                ]:
                    if col in lr_for_policy.columns:
                        lr_policy_cols.append(col)

                st.dataframe(lr_for_policy[lr_policy_cols], width="stretch")

# -------------------------------------------------------------------------------------------------
# Standards Mappings
# -------------------------------------------------------------------------------------------------
def render_standard_lens(
    std_df: pd.DataFrame,
    c_df: pd.DataFrame,
    lr_df: pd.DataFrame,
    f_df: pd.DataFrame,
    n_df: pd.DataFrame,
) -> None:
    """
    Lens anchored on CRT-STD (standards).

    For a selected standard:
    - Show standard meta (ID, name, status, mapped policies).
    - Show statement and description (structural framing).
    - Build a "Control Bundle" table (one row per CRT-C control).
    - Allow drill-down into a single control (CRT-C + F + N for that control).
    - Surface CRT-LR obligations:
        • Per-control obligations (for the selected control).
        • Bundle-wide obligations (across all controls mapped to the standard).
    - Show bundle-wide Failure Modes (CRT-F).
    - Show bundle-wide Compensating Controls (CRT-N).

    Note:
    - Standard "sections" are AI template structure and are intentionally not
      surfaced in this structural mapping view.
    """

    if std_df.empty:
        st.info("No standards found in CRT-STD catalogue.")
        return

    st.markdown("### 📏 Standard Lens (CRT-STD as anchor)")

    if "standard_id" not in std_df.columns:
        st.error("CRT-STD catalogue is missing the 'standard_id' column.")
        return

    # ----------------------------
    # 1) Select a standard
    # ----------------------------
    std_labels = {
        row["standard_id"]: f"{row['standard_id']} — {row.get('standard_name', '')}"
        for _, row in std_df.iterrows()
        if isinstance(row.get("standard_id"), str)
    }

    std_options = list(std_labels.keys())
    if not std_options:
        st.info("No standard IDs available in CRT-STD catalogue.")
        return

    selected_std_id = st.selectbox(
        "Select a standard to explore",
        options=std_options,
        format_func=lambda x: std_labels.get(x, x),
    )

    sel_row = std_df[std_df["standard_id"] == selected_std_id].iloc[0]

    # ----------------------------
    # 2) Standard metadata
    # ----------------------------
    st.markdown("#### 🧾 Standard Overview")

    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.write(f"**Standard ID:** {sel_row.get('standard_id', '')}")
        st.write(f"**Name:** {sel_row.get('standard_name', '')}")

    with meta_cols[1]:
        mapped_pols = parse_id_list(sel_row.get("mapped_policy_ids", ""))
        if mapped_pols:
            st.write("**Mapped Policies (POL-IDs):** " + ", ".join(mapped_pols))

    desc = sel_row.get("description", "")
    if isinstance(desc, str) and desc.strip():
        st.markdown("**Description**")
        st.write(desc)

    # ----------------------------
    # 3) Control bundle (CRT-C + F + N)
    # ----------------------------
    st.markdown("#### 🧱 Control Bundle for this Standard (CRT-C)")

    bundle_control_ids: List[str] = parse_id_list(sel_row.get("mapped_control_ids", ""))

    if not bundle_control_ids:
        st.info("This standard has no mapped CRT controls (mapped_control_ids is empty).")
        return

    if c_df.empty or "control_id" not in c_df.columns:
        st.warning("CRT-C catalogue not loaded or missing 'control_id' column.")
        return

    controls_view, failures_view, comps_view = build_controls_failure_comp_views(
        bundle_control_ids,
        c_df,
        f_df,
        n_df,
    )

    if controls_view.empty:
        st.warning(
            "None of the mapped CRT control IDs for this standard were found in CRT-C. "
            "Check for ID mismatches between CRT-STD.mapped_control_ids and CRT-C.control_id."
        )
    else:
        display_cols = []
        for col in [
            "control_id",
            "control_name",
            "group_domain",
            "sub_domain",
            "type",
            "function",
            "risk_level",
        ]:
            if col in controls_view.columns:
                display_cols.append(col)

        st.dataframe(controls_view[display_cols] if display_cols
        else controls_view, width="stretch")

    if controls_view.empty:
        # No point continuing to failures / compensations / LR if bundle is empty
        return

    # ----------------------------
    # 4) Pick a specific control from the bundle
    # ----------------------------
    st.markdown("#### 🎯 Focus on a Single Control in the Bundle")

    control_labels = {
        row["control_id"]: f"{row['control_id']} — {row.get('control_name', '')}"
        for _, row in controls_view.iterrows()
        if isinstance(row.get("control_id"), str)
    }
    control_ids = list(control_labels.keys())

    selected_control_id = st.selectbox(
        "Select a CRT control from this standard's bundle",
        options=control_ids,
        format_func=lambda cid: control_labels.get(cid, cid),
    )

    control_row = controls_view[controls_view["control_id"] == selected_control_id].iloc[0]

    st.markdown("##### 🧩 Control Detail (CRT-C)")
    with st.expander("View control metadata", expanded=True):
        meta_cols = st.columns(2)
        with meta_cols[0]:
            st.write(f"**Control ID:** {control_row.get('control_id', '')}")
            st.write(f"**Name:** {control_row.get('control_name', '')}")
            st.write(f"**Group:** {control_row.get('group_domain', '')}")
            st.write(f"**Sub-domain:** {control_row.get('sub_domain', '')}")
        with meta_cols[1]:
            st.write(f"**Type:** {control_row.get('type', '')}")
            st.write(f"**Function:** {control_row.get('function', '')}")
            st.write(f"**Risk Level:** {control_row.get('risk_level', '')}")

        desc_c = control_row.get("description", "")
        if isinstance(desc_c, str) and desc_c.strip():
            st.markdown("**Description**")
            st.write(desc_c)

        obj = control_row.get("objective", "")
        if isinstance(obj, str) and obj.strip():
            st.markdown("**Objective**")
            st.write(obj)

        ctx = control_row.get("deployment_exposure_context", "")
        if isinstance(ctx, str) and ctx.strip():
            st.markdown("**Deployment / Exposure Context**")
            st.write(ctx)

        scope = control_row.get("use_case_scope", "")
        if isinstance(scope, str) and scope.strip():
            st.markdown("**Use-Case Scope**")
            st.write(scope)

    # ----------------------------
    # 5) Failure Modes & Compensating Controls – per-control
    # ----------------------------
    st.markdown("##### ⚠️ CRT-F — Failure Modes for this Control")

    control_failure_ids: List[str] = []
    for col in control_row.index:
        if col.lower().startswith("mapped_fail"):
            control_failure_ids.extend(parse_id_list(str(control_row.get(col, ""))))
    control_failure_ids = sorted(set(control_failure_ids))

    if not control_failure_ids or failures_view.empty:
        st.info("No failure modes mapped for this control.")
    else:
        cf = failures_view[failures_view["failure_id"].isin(control_failure_ids)].copy()
        if cf.empty:
            st.info("No failure modes found in CRT-F for this control's mappings.")
        else:
            show_cols = [
                col
                for col in ["failure_id", "failure_name", "failure_category",
                "failure_description"]
                if col in cf.columns
            ]
            st.dataframe(cf[show_cols] if show_cols else cf, width="stretch")

    st.markdown("##### 🧩 CRT-N — Compensating Controls for this Control")

    control_comp_ids: List[str] = []
    for col in control_row.index:
        if col.lower().startswith("mapped_comp"):
            control_comp_ids.extend(parse_id_list(str(control_row.get(col, ""))))
    control_comp_ids = sorted(set(control_comp_ids))

    if not control_comp_ids or comps_view.empty:
        st.info("No compensating controls mapped for this control.")
    else:
        # `comps_view` has been normalised to `n_id`
        if "n_id" in comps_view.columns:
            cn = comps_view[comps_view["n_id"].isin(control_comp_ids)].copy()
        else:
            cn = comps_view.copy()

        if cn.empty:
            st.info("No compensating controls found in CRT-N for this control's mappings.")
        else:
            show_cols = [
                col
                for col in ["n_id", "compensating_name", "strength", "csf_category"]
                if col in cn.columns
            ]
            st.dataframe(cn[show_cols] if show_cols else cn, width="stretch")

    # ----------------------------
    # 6) Obligations – per-control view (CRT-LR)
    # ----------------------------
    st.markdown("#### ⚖️ CRT-LR — Obligations for this Control")

    if lr_df.empty or "mapped_control_ids" not in lr_df.columns:
        st.info("CRT-LR catalogue not loaded or missing 'mapped_control_ids' for obligations.")
    else:
        lr_exploded = explode_mapped_ids(lr_df, "mapped_control_ids", "_control_id")

        if lr_exploded.empty or "_control_id" not in lr_exploded.columns:
            st.info("No obligations are currently mapped to any controls in CRT-LR.")
        else:
            lr_for_control = lr_exploded[lr_exploded["_control_id"] == selected_control_id].copy()
            if lr_for_control.empty:
                st.info(f"No CRT-LR obligations mapped to control {selected_control_id}.")
            else:
                lr_display_cols = []
                for col in [
                    "lr_id",
                    "obligation_name",
                    "obligation_description",
                    "severity",
                    "evidence_required",
                    "source_reference_examples",
                ]:
                    if col in lr_for_control.columns:
                        lr_display_cols.append(col)

                st.dataframe(lr_for_control[lr_display_cols], width="stretch")

                st.divider()

    # ----------------------------
    # 7) Failure Modes & Compensations – standard bundle summaries
    # ----------------------------
    st.markdown("#### 📊 CRT-F — Failure Modes for this Standard's Control Bundle")
    if failures_view.empty:
        st.info("No failure modes mapped via the CRT controls for this standard.")
    else:
        show_cols = [
            col
            for col in ["failure_id", "failure_name", "failure_category", "failure_description"]
            if col in failures_view.columns
        ]
        st.dataframe(
            failures_view[show_cols].drop_duplicates() if show_cols
            else failures_view.drop_duplicates(),
            width="stretch",
        )

    st.markdown("#### 📊 CRT-N — Compensating Controls for this Standard's Control Bundle")
    if comps_view.empty:
        st.info("No compensating controls mapped via the CRT controls for this standard.")
    else:
        show_cols = [
            col
            for col in ["n_id", "compensating_name", "strength", "csf_category"]
            if col in comps_view.columns
        ]
        st.dataframe(
            comps_view[show_cols].drop_duplicates() if show_cols else comps_view.drop_duplicates(),
            width="stretch",
        )

    # ----------------------------
    # 8) Obligations – standard bundle summary (CRT-LR)
    # ----------------------------
    st.markdown("#### 📊 CRT-LR — Obligations Across this Standard's Control Bundle")

    if lr_df.empty or "mapped_control_ids" not in lr_df.columns:
        st.info("CRT-LR catalogue not loaded or missing 'mapped_control_ids'.")
    else:
        lr_exploded = explode_mapped_ids(lr_df, "mapped_control_ids", "_control_id")

        if lr_exploded.empty or "_control_id" not in lr_exploded.columns:
            st.info("No obligations are mapped to any CRT controls yet.")
        else:
            lr_for_standard = lr_exploded[lr_exploded["_control_id"].isin(bundle_control_ids)].copy()
            if lr_for_standard.empty:
                st.info("No CRT-LR obligations mapped via this standard's CRT controls.")
            else:
                if "lr_id" in lr_for_standard.columns:
                    lr_for_standard = lr_for_standard.drop_duplicates(subset=["lr_id"])

                lr_policy_cols = []
                for col in [
                    "lr_id",
                    "obligation_name",
                    "obligation_description",
                    "severity",
                    "evidence_required",
                    "source_reference_examples",
                ]:
                    if col in lr_for_standard.columns:
                        lr_policy_cols.append(col)

                st.dataframe(lr_for_standard[lr_policy_cols], width="stretch")

# -------------------------------------------------------------------------------------------------
# Obligations Mapping
# -------------------------------------------------------------------------------------------------
def render_obligation_lens(
    lr_df: pd.DataFrame,
    uc_df: pd.DataFrame,   # currently unused but kept for signature consistency
    c_df: pd.DataFrame,
    pol_df: pd.DataFrame,
    std_df: pd.DataFrame,
    f_df: pd.DataFrame,
    n_df: pd.DataFrame,
) -> None:
    """
    Lens anchored on CRT-LR (obligations).

    For a selected obligation (CRT-LR):
    - Show obligation meta (ID, name, severity, evidence, references).
    - Build a CRT-C control bundle via mapped_control_ids.
    - Show bundle-wide Failure Modes (CRT-F).
    - Show bundle-wide Compensating Controls (CRT-N).
    - Show Policies (CRT-POL) that are structurally linked via shared controls.
    - Show Standards (CRT-STD) that are structurally linked via shared controls.

    All relationships are derived via CRT-C:
        LR.mapped_control_ids <-> CRT-C.control_id
        POL.mapped_control_ids <-> CRT-C.control_id
        STD.mapped_control_ids <-> CRT-C.control_id
    """
    if lr_df.empty:
        st.info("No obligations found in CRT-LR catalogue.")
        return

    if "lr_id" not in lr_df.columns:
        st.error("CRT-LR catalogue is missing the 'lr_id' column.")
        return

    st.markdown("### ⚖️ Obligation Lens (CRT-LR as anchor)")

    # ----------------------------
    # 1) Select an obligation
    # ----------------------------
    lr_labels = {
        row["lr_id"]: f"{row['lr_id']} — {row.get('obligation_name', '')}"
        for _, row in lr_df.iterrows()
        if isinstance(row.get("lr_id"), str)
    }
    lr_options = list(lr_labels.keys())
    if not lr_options:
        st.info("No obligation IDs available in CRT-LR catalogue.")
        return

    selected_lr_id = st.selectbox(
        "Select an obligation",
        options=lr_options,
        format_func=lambda x: lr_labels.get(x, x),
    )

    sel_row = lr_df[lr_df["lr_id"] == selected_lr_id].iloc[0]

    # ----------------------------
    # 2) Obligation metadata
    # ----------------------------
    st.markdown("#### 🧾 Obligation Overview")

    meta_cols = st.columns(2)
    with meta_cols[0]:
        st.write(f"**Obligation ID:** {sel_row.get('lr_id', '')}")
        st.write(f"**Name:** {sel_row.get('obligation_name', '')}")

    with meta_cols[1]:
        sev = sel_row.get("severity", "")
        if isinstance(sev, str) and sev.strip():
            st.write(f"**Severity:** {sev}")
        ev = sel_row.get("evidence_required", "")
        if isinstance(ev, str) and ev.strip():
            st.write(f"**Evidence Required:** {ev}")

    desc = sel_row.get("obligation_description", "")
    if isinstance(desc, str) and desc.strip():
        st.markdown("**Description**")
        st.write(desc)

    src_ref = sel_row.get("source_reference_examples", "")
    if isinstance(src_ref, str) and src_ref.strip():
        st.markdown("**Source Reference Examples**")
        st.write(src_ref)

    notes = sel_row.get("notes", "")
    if isinstance(notes, str) and notes.strip():
        st.markdown("**Notes**")
        st.write(notes)

    # ----------------------------
    # 3) Control bundle (CRT-C) for this obligation
    # ----------------------------
    st.markdown("#### 🧱 CRT-C — Control Bundle for this Obligation")

    mapped_controls = parse_id_list(sel_row.get("mapped_control_ids", ""))

    if not mapped_controls:
        st.info("This obligation has no mapped CRT controls (mapped_control_ids is empty).")
        return

    if c_df.empty or "control_id" not in c_df.columns:
        st.warning("CRT-C catalogue not loaded or missing 'control_id' column.")
        return

    controls_view, failures_view, comps_view = build_controls_failure_comp_views(
        mapped_controls,
        c_df,
        f_df,
        n_df,
    )

    if controls_view.empty:
        st.info(
            "No CRT controls matching this obligation's mapped_control_ids were found in CRT-C. "
            "Check for ID mismatches between CRT-LR.mapped_control_ids and CRT-C.control_id."
        )
        return

    bundle_cols = []
    for col in ["control_id", "control_name", "group_domain", "sub_domain", "type",
    "function", "risk_level"]:
        if col in controls_view.columns:
            bundle_cols.append(col)

    st.dataframe(
        controls_view[bundle_cols] if bundle_cols else controls_view,
        width="stretch",
    )

    # ----------------------------
    # 4) Failure Modes & Compensations – obligation bundle summaries
    # ----------------------------
    st.markdown("#### 📊 CRT-F — Failure Modes for this Obligation's Control Bundle")
    if failures_view.empty:
        st.info("No failure modes mapped via the CRT controls for this obligation.")
    else:
        show_cols = [
            col
            for col in ["failure_id", "failure_name", "failure_category", "failure_description"]
            if col in failures_view.columns
        ]
        st.dataframe(
            failures_view[show_cols].drop_duplicates() if show_cols
            else failures_view.drop_duplicates(),
            width="stretch",
        )

    st.markdown("#### 📊 CRT-N — Compensating Controls for this Obligation's Control Bundle")
    if comps_view.empty:
        st.info("No compensating controls mapped via the CRT controls for this obligation.")
    else:
        show_cols = [
            col
            for col in ["n_id", "compensating_name", "strength", "csf_category"]
            if col in comps_view.columns
        ]
        st.dataframe(
            comps_view[show_cols].drop_duplicates() if show_cols else comps_view.drop_duplicates(),
            width="stretch",
        )

    # ----------------------------
    # 5) Policies linked via shared CRT controls (CRT-POL)
    # ----------------------------
    st.markdown("#### 📜 CRT-POL — Policies Linked via this Obligation's Controls")

    if pol_df.empty or "mapped_control_ids" not in pol_df.columns:
        st.info("CRT-POL catalogue not loaded or missing 'mapped_control_ids'.")
    else:
        pol_exploded = explode_mapped_ids(pol_df, "mapped_control_ids", "_control_id")

        if pol_exploded.empty or "_control_id" not in pol_exploded.columns:
            st.info("No policies currently mapped to any CRT controls.")
        else:
            pol_linked = pol_exploded[pol_exploded["_control_id"].isin(mapped_controls)].copy()
            if pol_linked.empty:
                st.info("No policies are structurally linked to this obligation via CRT controls.")
            else:
                # Deduplicate so each policy appears once
                if "policy_id" in pol_linked.columns:
                    pol_linked = pol_linked.drop_duplicates(subset=["policy_id"])
                else:
                    pol_linked = pol_linked.drop_duplicates()

                pol_cols = []
                for col in ["policy_id", "policy_name", "description"]:
                    if col in pol_linked.columns:
                        pol_cols.append(col)

                st.dataframe(
                    pol_linked[pol_cols] if pol_cols else pol_linked,
                    width="stretch",
                )

    # ----------------------------
    # 6) Standards linked via shared CRT controls (CRT-STD)
    # ----------------------------
    st.markdown("#### 📏 CRT-STD — Standards Linked via this Obligation's Controls")

    if std_df.empty or "mapped_control_ids" not in std_df.columns:
        st.info("CRT-STD catalogue not loaded or missing 'mapped_control_ids'.")
    else:
        std_exploded = explode_mapped_ids(std_df, "mapped_control_ids", "_control_id")

        if std_exploded.empty or "_control_id" not in std_exploded.columns:
            st.info("No standards currently mapped to any CRT controls.")
        else:
            std_linked = std_exploded[std_exploded["_control_id"].isin(mapped_controls)].copy()
            if std_linked.empty:
                st.info("No standards are structurally linked to this obligation via CRT controls.")
            else:
                if "standard_id" in std_linked.columns:
                    std_linked = std_linked.drop_duplicates(subset=["standard_id"])
                else:
                    std_linked = std_linked.drop_duplicates()

                std_cols = []
                for col in ["standard_id", "standard_name", "description"]:
                    if col in std_linked.columns:
                        std_cols.append(col)

                st.dataframe(
                    std_linked[std_cols] if std_cols else std_linked,
                    width="stretch",
                )

# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Structural Controls & Frameworks",
    page_icon="📂",
    layout="wide",
)

st.title("📂 Structural Controls & Frameworks — Command Centre")
st.caption(
    "Central hub for CRT catalogues. Browse the CRT backbone, onboard your organisation's "
    "requirements and obligations, define organisation profiles, and explore mappings between "
    "controls, policies, standards, obligations, and structural catalogues."
)

# -------------------------------------------------------------------------------------------------
# Info Panel
# -------------------------------------------------------------------------------------------------
with st.expander("📖 What is this app about?"):
    content = load_markdown_file(ABOUT_APP_MD)
    if content:
        st.markdown(content, unsafe_allow_html=True)
    else:
        st.markdown(
            "This module provides a non-prescriptive command centre for the Cyber Resilience "
            "Toolkit (CRT) catalogues. Core CRT Series catalogues are locked; operational and "
            "governance catalogues can be extended where explicitly supported. A mapping explorer "
            "allows read-only inspection of how requirements, policies, standards, and "
            "obligations relate to CRT controls."
        )

# -------------------------------------------------------------------------------------------------
# Org Profile Persistence Helpers
# -------------------------------------------------------------------------------------------------
ORG_PROFILES_DIR = "data"
ORG_PROFILES_PATH = os.path.join(ORG_PROFILES_DIR, "org_profiles.json")


def load_org_profiles_from_disk() -> tuple[Dict[str, Any], Any]:
    """
    Load saved org profiles and active profile name from disk, if present.

    Returns:
        (profiles_dict, active_profile_name)
    """
    if not os.path.exists(ORG_PROFILES_PATH):
        return {}, None

    try:
        with open(ORG_PROFILES_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        profiles = payload.get("profiles", {}) or {}
        active = payload.get("active_org_profile", None)

        # Basic sanity check
        if not isinstance(profiles, dict):
            profiles = {}
        if active is not None and active not in profiles:
            active = None

        return profiles, active
    except Exception:
        # Fail gracefully – treat as no profiles
        return {}, None


def save_org_profiles_to_disk(profiles: Dict[str, Any], active_profile_name: Any) -> None:
    """
    Save org profiles and active profile name to disk (JSON).
    Creates the data directory if required.
    """
    try:
        os.makedirs(ORG_PROFILES_DIR, exist_ok=True)
        payload = {
            "active_org_profile": active_profile_name,
            "profiles": profiles,
        }
        with open(ORG_PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        # Silent fail – UI should still work from session_state
        pass

# -------------------------------------------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------------------------------------------
st.sidebar.title("📂 Navigation Menu")
st.sidebar.page_link("app.py", label="CRT Portal")
for path, label in build_sidebar_links():
    st.sidebar.page_link(path, label=label)
st.sidebar.divider()
st.logo(BRAND_LOGO_PATH)  # pylint: disable=no-member

with st.sidebar.expander("🧾 Catalogue JSON reference models", expanded=False):
    st.caption(
        "CRT builds a derived **JSON view** for each catalogue (meta + records) under "
        "`apps/data_sources/crt_catalogues/json/`. CSV remains the source of truth."
    )
    if st.button("🔁 Rebuild JSON views (all catalogues)", use_container_width=True):
        try:
            results = rebuild_all_catalogue_json_views()
        except Exception as exc:
            st.error(f"Could not rebuild JSON views: {exc}")
        else:
            st.success(f"Rebuilt JSON views: {len(results)} catalogues.")
            with st.expander("Show outputs", expanded=False):
                for k, p in sorted(results.items()):
                    st.write(f"- **{k}** → `{os.path.relpath(p, PROJECT_PATH)}`")

st.sidebar.markdown("### 🚀 Flow Overview")
st.sidebar.caption(
    "1. **Org Governance Profile** — define organisation profiles (industry, jurisdictions, "
    "frameworks, obligations).\n"
    "2. **CRT Defaults Browser** — inspect the CRT backbone and all shipped catalogues.\n"
    "3. **Governance Setup** — onboard your own requirements and obligations (CRT-REQ / CRT-LR).\n"
    "4. **Operational Extensions** — extend assets, data, identity, supply-chain, telemetry.\n"
    "5. **Mapping Explorer** — inspect structural relationships."
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    [
        "Org Governance Profile (Org & Scope)",
        "CRT Defaults Browser",
        "Governance Setup (Framework Onboarding)",
        "Operational Extensions (Org-Specific)",
        "Mapping Explorer",
    ],
    index=0,
)

# -------------------------------------------------------------------------------------------------
# Load Core Data
# -------------------------------------------------------------------------------------------------
catalogues_effective, catalogues_raw = load_all_catalogues()

# -------------------------------------------------------------------------------------------------
# Initialise profile container in session (with disk persistence)
# -------------------------------------------------------------------------------------------------
if "org_profiles_initialised" not in st.session_state:
    loaded_profiles, loaded_active = load_org_profiles_from_disk()
    st.session_state["org_profiles"] = loaded_profiles
    st.session_state["active_org_profile"] = loaded_active
    st.session_state["org_profiles_initialised"] = True

# Fallback safety (in case something cleared state mid-session)
st.session_state.setdefault("org_profiles", {})
st.session_state.setdefault("active_org_profile", None)

# -------------------------------------------------------------------------------------------------
# Org Governance Profile Panel (Org & Scope — org_profiles only)
# -------------------------------------------------------------------------------------------------
if view_mode == "Org Governance Profile (Org & Scope)":
    st.header("🏛️ Org Governance Profile — Organisation & Scope")
    st.markdown(
        """
Use this view to define **organisation profiles** that capture:

- Basic organisation context (name, industry, jurisdictions, environment).
- Frameworks adopted (from **CRT-REQ.requirement_set_id**).
- Legal & regulatory obligations in scope (from **CRT-LR**).

Profiles are **read-only context containers** — they never modify CRT catalogues.
They are designed to be **bundled and passed to AI** alongside structural bundles
from other modules (e.g. Governance Orchestration, Architecture Workspace, etc.).
"""
    )

    # Pull current CRT-REQ / CRT-LR
    req_df = catalogues_effective.get("CRT-REQ", pd.DataFrame())
    lr_df = catalogues_effective.get("CRT-LR", pd.DataFrame())

    # Profile manager
    profiles: Dict[str, Any] = st.session_state["org_profiles"]
    existing_profile_names = sorted(profiles.keys())

    st.markdown("### 1. Profile Management")

    cols_profile = st.columns([1.4, 1.4, 1.2])

    with cols_profile[0]:
        selected_profile_name = st.selectbox(
            "Select existing profile",
            options=["<New profile>"] + existing_profile_names,
            index=(
                0
                if not st.session_state["active_org_profile"]
                or st.session_state["active_org_profile"] not in existing_profile_names
                else 1 + existing_profile_names.index(st.session_state["active_org_profile"])
            ),
        )

    with cols_profile[1]:
        profile_name = st.text_input(
            "Profile name",
            value=("" if selected_profile_name == "<New profile>" else selected_profile_name),
            placeholder="e.g. Default Programme, Third-Party ISO27001 Lens",
        )

    with cols_profile[2]:
        purpose_options = [
            "Default Programme",
            "Third-Party Review",
            "Regulator Engagement",
            "Internal Lens",
            "Custom",
        ]
        if selected_profile_name != "<New profile>" and selected_profile_name in profiles:
            current_purpose = profiles[selected_profile_name].get("profile_purpose", "Default Programme")
            purpose_index = purpose_options.index(current_purpose) if current_purpose in purpose_options else 0
        else:
            purpose_index = 0

        profile_purpose = st.selectbox(
            "Profile purpose",
            options=purpose_options,
            index=purpose_index,
        )

        purpose_hint = {
            "Default Programme": "Best choice for Policies, Standards, Governance material, and most bundle types.",
            "Third-Party Review": "Use when preparing vendor-facing or partner assessments.",
            "Regulator Engagement": "Use for supervisory interactions or regulatory material.",
            "Internal Lens": "For inward-facing work. Policies and Standards usually use Default Programme.",
            "Custom": "Define your own organisational framing or context.",
        }
        st.caption(purpose_hint.get(profile_purpose, ""))

    # ------------------------------------------------------------
    # Load existing profile data if editing
    # (Backward compatible with older schema that stored 'jurisdictions' as a flat list)
    # ------------------------------------------------------------
    if selected_profile_name != "<New profile>" and selected_profile_name in profiles:
        profile_data = profiles[selected_profile_name] or {}
    else:
        profile_data = {}

    def _profile_jurisdiction_explicit(pdct: Dict[str, Any]) -> List[str]:
        js = pdct.get("jurisdiction_scope", {})
        if isinstance(js, dict):
            explicit = js.get("explicit", [])
            if isinstance(explicit, list):
                return [str(x) for x in explicit if str(x).strip()]
        # Back-compat: older profiles stored "jurisdictions": [...]
        legacy = pdct.get("jurisdictions", [])
        if isinstance(legacy, list):
            return [str(x) for x in legacy if str(x).strip() and str(x).strip() != "Global"]
        return []

    def _profile_jurisdiction_effective(pdct: Dict[str, Any]) -> List[str]:
        js = pdct.get("jurisdiction_scope", {})
        if isinstance(js, dict):
            effective = js.get("effective", [])
            if isinstance(effective, list) and effective:
                # ensure Global baseline
                eff = [str(x) for x in effective if str(x).strip()]
                if "Global" not in eff:
                    eff = ["Global"] + eff
                # stable dedupe
                return list(dict.fromkeys(eff))
        # Fallback: derive from explicit
        explicit = _profile_jurisdiction_explicit(pdct)
        eff = ["Global"] + [j for j in explicit if j != "Global"]
        return list(dict.fromkeys(eff))

    st.markdown("### 2. Organisation Context")

    col_org_left, col_org_right = st.columns(2)

    with col_org_left:
        org_name = st.text_input(
            "Organisation name",
            value=profile_data.get("org_name", ""),
            placeholder="e.g. Example Financial Services Ltd.",
        )

        industry_options = [
            "Financial Services",
            "Healthcare",
            "Technology / SaaS",
            "Manufacturing",
            "Public Sector / Government",
            "Critical Infrastructure",
            "Retail / Ecommerce",
            "Other / Mixed",
        ]
        industry_value = profile_data.get("industry", "Other / Mixed")
        industry_index = industry_options.index(industry_value) if industry_value in industry_options else 7

        industry = st.selectbox(
            "Primary industry / sector",
            options=industry_options,
            index=industry_index,
        )

        env_options = [
            "Cloud-first",
            "Hybrid (Cloud + On-Prem)",
            "Primarily On-Premises",
            "Mixed / Other",
        ]
        env_value = profile_data.get("environment", "Mixed / Other")
        env_index = env_options.index(env_value) if env_value in env_options else 3

        environment = st.selectbox(
            "Operational environment",
            options=env_options,
            index=env_index,
        )

    with col_org_right:
        # Jurisdictions: driven by parsed CRT-LR.jurisdiction tags (semicolon-separated).
        # We store explicit vs effective to make inheritance (Global baseline) deterministic.
        stored_juris_explicit = _profile_jurisdiction_explicit(profile_data)
        stored_juris_effective = _profile_jurisdiction_effective(profile_data)

        juris_suggestions: List[str] = []
        jurisdiction_meta_col = None

        if not lr_df.empty:
            for cand in ["jurisdiction", "jurisdiction_code", "region"]:
                if cand in lr_df.columns:
                    jurisdiction_meta_col = cand
                    all_vals = lr_df[cand].dropna().astype(str).tolist()
                    tokens: List[str] = []
                    for v in all_vals:
                        tokens.extend([t.strip() for t in v.split(";") if t.strip()])
                    juris_suggestions = sorted(set(tokens))
                    break

        if jurisdiction_meta_col and juris_suggestions:
            # Default selection behaviour:
            # - Editing: use stored explicit jurisdictions (do not auto-select everything)
            # - New profile: default to Global if present, else empty
            if selected_profile_name != "<New profile>":
                defaults = [j for j in stored_juris_explicit if j in juris_suggestions and j != "Global"]
            else:
                defaults = []  # explicit only

            # We allow Global to appear as an option (if it exists), but we don't require manual selection.
            jurisdictions_ui = st.multiselect(
                "Jurisdictions / regions in scope",
                options=juris_suggestions,
                default=(["Global"] if (selected_profile_name == "<New profile>" and "Global" in juris_suggestions) else []) + defaults,
                help=(
                    f"Values are derived from CRT-LR.{jurisdiction_meta_col}, parsed into unique tags "
                    "(e.g. EU, UK, US, Singapore). Global is treated as the baseline lens."
                ),
            )

            # Normalise into explicit vs effective
            jurisdictions_explicit = [j for j in jurisdictions_ui if j and j.strip() and j != "Global"]
            jurisdictions_effective = ["Global"] + jurisdictions_explicit
            jurisdictions_effective = list(dict.fromkeys(jurisdictions_effective))  # stable dedupe

        else:
            # No CRT-LR jurisdiction metadata column found → context-only freeform list
            # Keep backward compat: show stored explicit list as options.
            jurisdictions_explicit = stored_juris_explicit
            jurisdictions_effective = list(dict.fromkeys((["Global"] + jurisdictions_explicit))) if jurisdictions_explicit else ["Global"]

            jurisdictions_ui = st.multiselect(
                "Jurisdictions / regions in scope (context only)",
                options=jurisdictions_explicit,
                default=jurisdictions_explicit,
                help=(
                    "No explicit jurisdiction metadata column was found in CRT-LR. "
                    "You can still record high-level jurisdiction context here for AI, "
                    "but it will not filter CRT-LR automatically.\n\n"
                    "If you want obligations to be grouped or filtered by jurisdiction, "
                    "add a column such as 'jurisdiction' to CRT-LR and reload."
                ),
            )

            jurisdictions_explicit = [j for j in jurisdictions_ui if j and j.strip() and j != "Global"]
            jurisdictions_effective = ["Global"] + jurisdictions_explicit
            jurisdictions_effective = list(dict.fromkeys(jurisdictions_effective))

        size_options = [
            "Start-up / Small",
            "Mid-size",
            "Large / Enterprise",
            "Global / Multi-region",
        ]
        size_value = profile_data.get("org_size", "Mid-size")
        size_index = size_options.index(size_value) if size_value in size_options else 1

        org_size = st.selectbox(
            "Organisation size (approximate)",
            options=size_options,
            index=size_index,
        )

    org_notes = st.text_area(
        "Context notes (optional)",
        value=profile_data.get("notes", ""),
        placeholder=(
            "Any additional context that might be helpful when AI interprets your profile "
            "(e.g. critical business services, listing status, special regulators)."
        ),
        height=80,
    )

    st.markdown("---")
    st.markdown("### 3. Frameworks Adopted (CRT-REQ)")

    frameworks_selected: List[str] = profile_data.get("frameworks_in_scope", [])
    if not isinstance(frameworks_selected, list):
        frameworks_selected = []

    # How selected frameworks should interact with the default CRT catalogues
    frameworks_mode_options = {
        "default_only": "Use default CRT catalogues only (no explicit CRT-REQ overlay)",
        "overlay": "Overlay selected frameworks on top of default CRT catalogues (recommended)",
        "framework_only": "Use selected frameworks as the primary requirements lens (still mapped via CRT-C)",
    }
    mode_keys = list(frameworks_mode_options.keys())
    mode_labels = list(frameworks_mode_options.values())

    current_mode_key = profile_data.get("frameworks_mode", "overlay")
    if current_mode_key not in mode_keys:
        current_mode_key = "overlay"
    current_mode_index = mode_keys.index(current_mode_key)

    if req_df.empty or "requirement_set_id" not in req_df.columns:
        st.info(
            "CRT-REQ is not loaded or missing 'requirement_set_id'. "
            "Onboard requirements via **Governance Setup (Framework Onboarding)** first."
        )
        frameworks_selected = []
        selected_mode_label = st.radio(
            "How should selected frameworks be treated?",
            options=mode_labels,
            index=current_mode_index,
            help=(
                "Even if no CRT-REQ sets are currently available, this preference will be stored "
                "with the profile and used once frameworks are onboarded."
            ),
        )
    else:
        set_ids = sorted(
            s for s in req_df["requirement_set_id"].astype(str).unique() if s.strip()
        )

        # Platinum default: do NOT auto-select all frameworks for a new profile.
        if selected_profile_name == "<New profile>" and not frameworks_selected:
            default_frameworks = []
        else:
            default_frameworks = [f for f in frameworks_selected if f in set_ids]

        st.markdown(
            "Select any **requirements sets** (e.g. NIST 800-53, ISO overlays, internal frameworks) "
            "that should apply to this organisational profile."
        )
        frameworks_selected = st.multiselect(
            "Frameworks in scope",
            options=set_ids,
            default=default_frameworks,
            help=(
                "Values come from CRT-REQ.requirement_set_id. These may represent ISO27001, "
                "NIST 800-53, PCI DSS, SOC2, internal frameworks, or custom uploaded sets."
            ),
        )

        selected_mode_label = st.radio(
            "How should selected frameworks be treated?",
            options=mode_labels,
            index=current_mode_index,
            help=(
                "- **Use default CRT catalogues only** → other modules rely on the core CRT spine "
                "(CRT-G / CRT-C / CRT-F / CRT-N) and ignore explicit CRT-REQ overlays.\n"
                "- **Overlay selected frameworks** → selected requirement sets from CRT-REQ are added as "
                "an overlay **on top of** the default CRT catalogues.\n"
                "- **Framework-only lens** → selected CRT-REQ sets are treated as the primary requirements lens "
                "for this profile. The structural CRT mapping still uses CRT-C / CRT-N, but default requirement "
                "overlays are not assumed."
            ),
        )

        st.caption(
            "If the frameworks or requirement sets your organisation relies on are not listed here, "
            "append them to **CRT-REQ** via **Governance Setup (Framework Onboarding)** first."
        )

        if frameworks_selected:
            req_preview = req_df[req_df["requirement_set_id"].astype(str).isin(frameworks_selected)]
            with st.expander("Preview — Requirements for selected frameworks", expanded=False):
                st.dataframe(req_preview, width="stretch")
        else:
            st.info(
                "No frameworks explicitly selected. Other modules will default to the core CRT catalogues "
                "(CRT-G / CRT-C / CRT-F / CRT-N) without an explicit CRT-REQ overlay."
            )

    # Resolve mode key from label
    selected_mode_key = mode_keys[mode_labels.index(selected_mode_label)]

    st.markdown("---")
    # -------------------------------------------------------------------------------------------------
    # 4. Legal & Regulatory Obligations in Scope (CRT-LR)
    # (Platinum: never silently filter to empty; optional baseline defaults for new profiles)
    # -------------------------------------------------------------------------------------------------
    st.markdown("### 4. Legal & Regulatory Obligations in Scope (CRT-LR)")

    obligations_selected_ids: List[str] = profile_data.get("obligations_ids_in_scope", [])
    if not isinstance(obligations_selected_ids, list):
        obligations_selected_ids = []

    lr_selected = pd.DataFrame()

    if lr_df.empty:
        st.info(
            "CRT-LR is not loaded. Onboard legal / regulatory obligations via "
            "**Governance Setup (Framework Onboarding)** first."
        )
    else:
        lr_view = lr_df.copy()

        # ----------------------------
        # Detect key columns
        # ----------------------------
        jurisdiction_col = None
        for candidate in ["jurisdiction", "jurisdiction_code", "region"]:
            if candidate in lr_view.columns:
                jurisdiction_col = candidate
                break

        industry_col = None
        for candidate in ["industry", "sector", "domain"]:
            if candidate in lr_view.columns:
                industry_col = candidate
                break

        def _split_tags(value: Any) -> set:
            return {t.strip() for t in str(value).split(";") if t.strip()}

        # ----------------------------
        # Jurisdiction scope
        # ----------------------------
        allowed_base_tags: set = set(jurisdictions_effective) if jurisdictions_effective else {"Global"}
        additional_juris: List[str] = []

        if jurisdiction_col:
            all_vals = lr_view[jurisdiction_col].dropna().astype(str).tolist()
            all_tokens: set = set()
            for v in all_vals:
                all_tokens.update(_split_tags(v))

            extra_candidates = sorted(all_tokens - allowed_base_tags) if allowed_base_tags else sorted(all_tokens)

            with st.expander("Jurisdiction scope for obligations", expanded=False):
                st.markdown(
                    "By default, obligations are scoped to your organisation's jurisdictions "
                    "and any entries tagged as **Global**. You can optionally include additional "
                    "jurisdictions here (for example where you review a third-country vendor)."
                )
                if extra_candidates:
                    additional_juris = st.multiselect(
                        "Include additional jurisdictions",
                        options=extra_candidates,
                        default=[],
                    )
                else:
                    st.caption("No additional jurisdiction tags found beyond the current organisation scope.")

        allowed_tags = allowed_base_tags.union(additional_juris) if jurisdiction_col else set()

        # Apply jurisdiction filter (safe)
        lr_after_juris = lr_view
        if jurisdiction_col and allowed_tags:
            lr_after_juris = lr_view[
                lr_view[jurisdiction_col].apply(lambda v: bool(_split_tags(v) & allowed_tags))
            ]

        # ----------------------------
        # Industry filter (SOFT)
        # Only apply if it doesn't collapse the view to zero.
        # ----------------------------
        lr_after_industry = lr_after_juris
        industry_filter_applied = False
        industry_filter_backed_off = False

        if industry_col and industry:
            # Only filter if column has meaningful values OR the filter yields results.
            # We treat blanks as "not classified", so a strict filter can wipe everything.
            candidate = lr_after_juris[lr_after_juris[industry_col].notna()].copy()

            # If mostly blank, candidate may be empty; still attempt filter on full set.
            filtered = lr_after_juris[lr_after_juris[industry_col].astype(str) == str(industry)]

            if not filtered.empty:
                lr_after_industry = filtered
                industry_filter_applied = True
            else:
                # Back off: keep jurisdiction-filtered view
                lr_after_industry = lr_after_juris
                industry_filter_backed_off = True

        lr_view_scoped = lr_after_industry

        if industry_filter_applied:
            st.caption(f"Obligations filtered by industry: **{industry}**.")
        elif industry_filter_backed_off:
            st.caption(
                f"Industry filter (**{industry}**) would hide all obligations, so it was not applied."
            )

        # ----------------------------
        # Build selectable obligations
        # ----------------------------
        if "lr_id" in lr_view_scoped.columns:
            lr_ids = sorted(lid for lid in lr_view_scoped["lr_id"].astype(str).unique() if lid.strip())

            if not lr_ids:
                st.warning(
                    "No obligations are currently visible after jurisdiction/industry scoping. "
                    "This typically indicates missing tags in CRT-LR (e.g. jurisdiction values) "
                    "or an overly strict filter."
                )

            # Baseline selection for NEW profiles (optional)
            is_new_profile = (selected_profile_name == "<New profile>") and (selected_profile_name not in profiles)

            # Default: ON for new profiles, OFF for existing profiles
            auto_baseline_default = True if is_new_profile else False

            auto_select_baseline = st.checkbox(
                "Auto-select baseline obligations for new profiles",
                value=auto_baseline_default,
                help=(
                    "When enabled for a new profile, the selection defaults to a sensible baseline "
                    "within the scoped view (e.g. Global + jurisdiction-in-scope entries). "
                    "You can always refine manually."
                ),
            )

            # Determine default selection
            if not is_new_profile:
                # Existing profile → honour saved selection
                default_lr_ids = [lid for lid in obligations_selected_ids if lid in lr_ids]
            else:
                # New profile → either nothing, or baseline
                if auto_select_baseline and jurisdiction_col:
                    # Baseline: anything tagged Global OR intersecting the org scope jurisdictions
                    def _is_baseline_row(v: Any) -> bool:
                        tags = _split_tags(v)
                        return ("Global" in tags) or bool(tags & set(jurisdictions_effective or ["Global"]))

                    baseline_df = lr_view_scoped[lr_view_scoped[jurisdiction_col].apply(_is_baseline_row)]
                    default_lr_ids = sorted(
                        lid for lid in baseline_df["lr_id"].astype(str).unique().tolist() if lid.strip()
                    )
                elif auto_select_baseline and not jurisdiction_col:
                    # No jurisdiction column → baseline == everything visible
                    default_lr_ids = lr_ids.copy()
                else:
                    default_lr_ids = []

            obligations_selected_ids = st.multiselect(
                "Obligations in scope",
                options=lr_ids,
                default=default_lr_ids,
                help=(
                    "Values come from CRT-LR.lr_id, scoped by jurisdiction (plus Global baseline). "
                    "If obligations for a given regulator, framework, or jurisdiction are missing, "
                    "append them to **CRT-LR** via **Governance Setup (Framework Onboarding)**."
                ),
            )

            lr_selected = lr_view_scoped[lr_view_scoped["lr_id"].astype(str).isin(obligations_selected_ids)]

        else:
            st.warning(
                "CRT-LR is missing 'lr_id'; obligations cannot be individually selected. "
                "Profile-based obligation scoping is limited."
            )
            obligations_selected_ids = []
            lr_selected = lr_view_scoped.copy()

        if lr_selected.empty and obligations_selected_ids:
            st.info("No obligations match the current selections.")
        elif not lr_selected.empty:
            with st.expander("Preview — Obligations in scope for this profile", expanded=False):
                st.dataframe(lr_selected, width="stretch")

        st.markdown("---")

    # -------------------------------------------------------------------------------------------------
    # 5. Save Profile & Build Scope Bundle
    # -------------------------------------------------------------------------------------------------
    st.markdown("### 5. Save Profile & Build Scope Bundle")

    col_actions = st.columns([1.2, 1.2, 2])

    with col_actions[0]:
        if st.button("💾 Save / Update Profile", type="primary"):
            if not profile_name.strip():
                st.error("Profile name is required before saving.")
            else:
                profiles[profile_name] = {
                    "profile_name": profile_name,
                    "profile_purpose": profile_purpose,
                    "org_name": org_name,
                    "industry": industry,
                    "environment": environment,
                    "jurisdiction_scope": {
                        "explicit": jurisdictions_explicit,
                        "effective": jurisdictions_effective,
                    },
                    "org_size": org_size,
                    "notes": org_notes,
                    "frameworks_in_scope": frameworks_selected,
                    "frameworks_mode": selected_mode_key,
                    "obligations_ids_in_scope": obligations_selected_ids,
                }

                # Optional: keep legacy key for older consumers (safe redundancy)
                profiles[profile_name]["jurisdictions"] = jurisdictions_explicit

                st.session_state["org_profiles"] = profiles
                st.session_state["active_org_profile"] = profile_name

                # 🔐 Save to disk as well
                save_org_profiles_to_disk(
                    profiles=profiles,
                    active_profile_name=profile_name,
                )

                st.success(f"Profile '{profile_name}' saved and set as primary.")

    with col_actions[1]:
        if selected_profile_name != "<New profile>" and selected_profile_name in profiles:
            if st.button("⭐ Set as Primary Profile"):
                st.session_state["active_org_profile"] = selected_profile_name

                # 🔐 Persist new active profile to disk
                save_org_profiles_to_disk(
                    profiles=st.session_state["org_profiles"],
                    active_profile_name=selected_profile_name,
                )

                st.success(f"Primary profile set to '{selected_profile_name}'.")

    # Build scope bundle directly from the **current UI state**
    # (so the JSON reflects what you see, even before saving).
    st.markdown("#### 🧩 Org Governance Scope Bundle (for AI Context)")

    scope_bundle: Dict[str, Any] = {
        "bundle_type": "org_governance_scope",
        "source_module": "StructuralControlsFrameworks",
        "profile_name": profile_name if profile_name.strip() else selected_profile_name,
        "profile_purpose": profile_purpose,
        "org_name": org_name,
        "industry": industry,
        "environment": environment,
        "jurisdiction_scope": {
            "explicit": jurisdictions_explicit,
            "effective": jurisdictions_effective,
        },
        "org_size": org_size,
        "notes": org_notes,
        "frameworks_in_scope": frameworks_selected,
        "frameworks_mode": selected_mode_key,
        "obligations_ids_in_scope": obligations_selected_ids,
    }

    # Attach resolved obligation rows (optional, useful for AI) — use lr_view if available to stay consistent
    try:
        if "lr_view" in locals() and isinstance(locals().get("lr_view"), pd.DataFrame):
            lr_scope_source = lr_view
        else:
            lr_scope_source = lr_df

        if not lr_scope_source.empty and obligations_selected_ids and "lr_id" in lr_scope_source.columns:
            lr_scope_records = (
                lr_scope_source[lr_scope_source["lr_id"].astype(str).isin(obligations_selected_ids)]
                .reset_index(drop=True)
                .to_dict(orient="records")
            )
        else:
            lr_scope_records = []
    except Exception:
        lr_scope_records = []

    scope_bundle["obligations_in_scope"] = lr_scope_records

    st.json(scope_bundle, expanded=False)

    # Optional JSON download
    try:
        json_bytes = json.dumps(scope_bundle, indent=2).encode("utf-8")
        st.download_button(
            "⬇️ Download org governance scope bundle (JSON)",
            data=json_bytes,
            file_name="org_governance_scope_bundle.json",
            mime="application/json",
        )
    except Exception:
        st.caption("JSON download unavailable (local JSON serialisation failed).")

    st.caption(
        "Profiles are stored in-memory for this session under `org_profiles` and also "
        f"persisted to `{ORG_PROFILES_PATH}`. "
        "Other modules (e.g. 🧭 Governance Orchestration) can consume the active profile via "
        "`active_org_profile` + `org_profiles` when building AI-ready bundles. "
        "The JSON preview above always reflects the current on-screen selections."
    )



# -------------------------------------------------------------------------------------------------
# Governance Setup Panel
# -------------------------------------------------------------------------------------------------
if view_mode == "Governance Setup (Framework Onboarding)":
    st.header("🧭 Governance Setup — Framework Onboarding")
    st.markdown(
    """
    This section allows you to update your organisation’s governance catalogues:

    - **CRT-REQ** — Requirements
    - **CRT-LR** — Legal & Regulatory Obligations

    These catalogues connect into your CRT backbone via **CRT-C controls** without modifying the locked core series (CRT-G, CRT-C, CRT-F, CRT-N).

    **Workflow (simple):** download the active catalogue → edit locally → upload back → save.

    If mistakes occur, restore the shipped default catalogue from the `/defaults` folder (or use 🧹 Maintenance for restore/replace).
    """
    )

    with st.expander("ℹ️ Help & Guidance — Working With Requirements & Obligations", expanded=False):
        help_md = load_markdown_file(HELP_STC_MD)
        if help_md:
            st.markdown(help_md, unsafe_allow_html=True)
        else:
            st.info(
                "Help content for this section is not currently available. "
                "Please ensure the file defined by `HELP_STC_MD` "
                "(for example `/docs/help_structural_controls_frameworks.md`) exists and is readable."
            )

    # Restrict governance catalogues that can be extended here
    governance_options = ["CRT-REQ", "CRT-LR"]

    selected_name = st.selectbox(
        "Choose a governance catalogue to view / extend",
        options=governance_options,
        format_func=lambda x: {
            "CRT-REQ": "📋 CRT-REQ — Requirements Catalogue",
            "CRT-LR": "⚖️ CRT-LR — Legal & Regulatory Obligations",
        }.get(x, x),
    )

    # ------------------------------------------------------------
    # Resolve file paths using YOUR existing scheme
    # ------------------------------------------------------------
    defaults_dir = os.path.join(PROJECT_PATH, "apps", "data_sources", "defaults")

    cfg = CATALOGUES_CONFIG.get(selected_name, {})
    filename = cfg.get("filename") or f"{selected_name}.csv"

    live_path = os.path.join(CRT_CATALOGUE_DIR, filename)
    default_path = os.path.join(defaults_dir, filename)

    # Sample template naming (matches your existing samples tree)
    sample_path = None
    if selected_name == "CRT-REQ":
        sample_path = os.path.join(SAMPLES_DIR, "CRT-REQ.sample.csv")
    elif selected_name == "CRT-LR":
        sample_path = os.path.join(SAMPLES_DIR, "CRT-LR.sample.csv")

    def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    st.markdown("#### 📄 Current Effective Catalogue")
    eff_df = catalogues_effective.get(selected_name, pd.DataFrame())
    if eff_df.empty:
        st.info("No data found for this catalogue yet.")
    else:
        st.dataframe(eff_df, width="stretch")

    # ------------------------------------------------------------
    # Where do I get the file to edit? (Download actions)
    # ------------------------------------------------------------
    st.markdown("---")
    with st.expander("📥 Where do I get the file to edit?", expanded=False):
        st.caption(
            "Download the **active catalogue**, edit it locally, then upload it back to overwrite the working file. "
            "Shipped defaults are provided as a **restore reference** if you need to roll back."
        )

        with st.expander("How this works (simple)", expanded=False):
            st.markdown(
                f"""
    - **Edit path (recommended):** download **Active catalogue**, edit locally, then use **Upload & Overwrite**.
    - **What happens on upload:** the active file is overwritten, a timestamped backup is created, and the JSON reference model is regenerated automatically.
    - **Defaults:** shipped baseline files are **restore references only**.
    - **Restore (recommended):** use 🎛 Programme Builder & AI Export → 🧹 Maintenance → Governance Setup catalogues (for {selected_name}).
    - **Manual copying is not recommended:** copying files directly into `crt_catalogues/` does **not** regenerate JSON views and may leave the system out of sync.
    """
            )

        with st.expander("Show active catalogue location", expanded=False):
            st.code(f"{live_path}", language="text")

        with st.expander("Show shipped default location (restore reference only)", expanded=False):
            st.caption(
                "Read-only reference. Do not edit or copy this file directly into the working directory. "
                "Use the restore flow to ensure backups and JSON regeneration occur correctly."
            )
            st.code(f"{default_path}", language="text")



        c1, c2, c3, c4 = st.columns(4)

        # 1) Active catalogue (edit this)
        with c1:
            if os.path.exists(live_path):
                try:
                    live_bytes = open(live_path, "rb").read()
                    st.download_button(
                        "⬇️ Active catalogue (edit this)",
                        data=live_bytes,
                        file_name=os.path.basename(live_path),
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read active catalogue file — {exc}")
                    st.button("⬇️ Active catalogue (edit this)", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Active catalogue (edit this)", disabled=True, use_container_width=True)

        # 2) Latest backup (restore reference)
        with c2:
            latest_backup = get_latest_backup_path(selected_name)
            if latest_backup and os.path.exists(latest_backup):
                try:
                    backup_bytes = open(latest_backup, "rb").read()
                    st.download_button(
                        "⬇️ Latest backup (restore only)",
                        data=backup_bytes,
                        file_name=os.path.basename(latest_backup),
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read backup file — {exc}")
                    st.button("⬇️ Latest backup (restore only)", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Latest backup (restore only)", disabled=True, use_container_width=True)

        # 3) Shipped default (restore reference)
        with c3:
            if os.path.exists(default_path):
                try:
                    default_bytes = open(default_path, "rb").read()
                    st.download_button(
                        "⬇️ Shipped default (restore only)",
                        data=default_bytes,
                        file_name=f"{selected_name}.default.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read default catalogue file — {exc}")
                    st.button("⬇️ Shipped default (restore only)", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Shipped default (restore only)", disabled=True, use_container_width=True)

        # 4) Sample template (scaffold)
        with c4:
            if sample_path and os.path.exists(sample_path):
                try:
                    sample_bytes = open(sample_path, "rb").read()
                    st.download_button(
                        "⬇️ Sample template",
                        data=sample_bytes,
                        file_name=os.path.basename(sample_path),
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read sample template — {exc}")
                    st.button("⬇️ Sample template", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Sample template", disabled=True, use_container_width=True)
    st.markdown("#### 📤 Upload & Overwrite (Active Catalogue)")
    st.caption(
        "Upload a CSV to overwrite the active working file (e.g. `CRT-LR.csv`). "
        "CRT creates a timestamped backup in `/backup` and regenerates the JSON view in `/json` automatically.\n\n"
        "If you need to roll back, you can upload a previously downloaded backup or the shipped default file."
    )

    # --------------------
    # Sample / Template Files (preview)
    # --------------------
    with st.expander("📘 Sample & Template Files — Requirements & Obligations", expanded=False):
        if sample_path and os.path.exists(sample_path):
            try:
                sample_df = read_csv_with_fallback(sample_path)
                if sample_df.empty:
                    st.info("Sample file loaded, but contains no rows.")
                else:
                    st.dataframe(sample_df, width="stretch")
            except Exception as exc:
                st.warning(f"Could not load sample file — {exc}")
        else:
            if selected_name == "CRT-REQ":
                st.info("`CRT-REQ.sample.csv` not found in samples directory.")
            elif selected_name == "CRT-LR":
                st.info("`CRT-LR.sample.csv` not found in samples directory.")
            else:
                st.info("No sample file is defined for this catalogue selection.")

    # --------------------
    # Upload CRT-REQ.csv / CRT-LR.csv Files (overwrite active + backup + JSON sync)
    # --------------------
    uploaded = st.file_uploader(
        "Choose a CSV file (replaces current working catalogue)",
        type=["csv"],
        key=f"upload_{selected_name}",
    )

    if uploaded is not None:
        if st.button("💾 Overwrite & Save", key=f"save_{selected_name}"):
            try:
                active_path = overwrite_catalogue_with_backup(selected_name, uploaded)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(
                    f"✅ {selected_name} updated. Previous version backed up to `/backup`."
                )
                try:
                    eff_df = read_csv_with_fallback(active_path)
                    json_path = write_catalogue_json_view(selected_name, eff_df)
                    st.caption(
                        f"Reference model updated: `{os.path.relpath(json_path, PROJECT_PATH)}`"
                    )
                except Exception as exc:
                    st.warning(f"Could not update JSON reference model — {exc}")


# -------------------------------------------------------------------------------------------------
# CRT Defaults Browser
# -------------------------------------------------------------------------------------------------
elif view_mode == "CRT Defaults Browser":
    # Page-level intro
    st.header("📂 CRT Defaults Browser")
    st.markdown(
        """
Browse all shipped CRT catalogues — both the **locked backbone** and the **governance / operational layers**.

This view is **read-only** and exists to give you structural clarity **before** you extend the framework through
**Governance Setup** or **Operational Extensions**.
"""
    )

    # Core CRT Series (locked backbone)
    st.subheader("🧱 Core CRT Series (Locked Backbone)")
    st.caption(
        "The foundational CRT catalogues that define the structural spine of the programme. "
        "These are shipped read-only and form the basis for all mappings and outputs."
    )
    tab_g, tab_c, tab_f, tab_n = st.tabs(
        ["📘 CRT-G Domains", "🧱 CRT-C Controls", "⚠️ CRT-F Failures", "🧩 CRT-N Compensations"]
    )
    with tab_g:
        render_crt_g(catalogues_effective.get("CRT-G", pd.DataFrame()))
    with tab_c:
        render_crt_c(
            catalogues_effective.get("CRT-C", pd.DataFrame()),
            catalogues_effective.get("CRT-G", pd.DataFrame()),
        )
    with tab_f:
        render_crt_f(catalogues_effective.get("CRT-F", pd.DataFrame()))
    with tab_n:
        render_crt_n(catalogues_effective.get("CRT-N", pd.DataFrame()))

    st.markdown("---")

    # Governance Catalogues
    st.subheader("📋 Governance Catalogues (Shipped)")
    st.caption(
        "Baseline governance layers that can be extended via **Governance Setup**. "
        "These catalogues express expectations, policies, standards, and obligations that connect back into CRT-C."
    )
    gov_tabs = st.tabs(
        [
            "📋 CRT-REQ Requirements",
            "📜 CRT-POL Policies",
            "📏 CRT-STD Standards",
            "⚖️ CRT-LR Obligations",
        ]
    )
    with gov_tabs[0]:
        render_generic_catalogue("CRT-REQ", catalogues_effective.get("CRT-REQ", pd.DataFrame()))
    with gov_tabs[1]:
        render_generic_catalogue("CRT-POL", catalogues_effective.get("CRT-POL", pd.DataFrame()))
    with gov_tabs[2]:
        render_generic_catalogue("CRT-STD", catalogues_effective.get("CRT-STD", pd.DataFrame()))
    with gov_tabs[3]:
        render_generic_catalogue("CRT-LR", catalogues_effective.get("CRT-LR", pd.DataFrame()))

    st.markdown("---")

    # Operational Structure (organisation-specific extensions)
    st.subheader("🛰 Operational Structure (Organisation-Specific)")
    st.caption(
        "Shipped baselines for assets, data, identity, supply-chain, and telemetry. "
        "These catalogues describe **your real environment** once extended, and connect back into CRT-D and CRT-C."
    )
    op_tabs = st.tabs(
        [
            "🛰 CRT-AS Assets",
            "📦 CRT-D Data",
            "🔐 CRT-I Identity Zones",
            "🚢 CRT-SC Supply Chain",
            "📡 CRT-T Telemetry",
        ]
    )
    with op_tabs[0]:
        render_generic_catalogue("CRT-AS", catalogues_effective.get("CRT-AS", pd.DataFrame()))
    with op_tabs[1]:
        render_generic_catalogue("CRT-D", catalogues_effective.get("CRT-D", pd.DataFrame()))
    with op_tabs[2]:
        render_generic_catalogue("CRT-I", catalogues_effective.get("CRT-I", pd.DataFrame()))
    with op_tabs[3]:
        render_generic_catalogue("CRT-SC", catalogues_effective.get("CRT-SC", pd.DataFrame()))
    with op_tabs[4]:
        render_generic_catalogue("CRT-T", catalogues_effective.get("CRT-T", pd.DataFrame()))

# -------------------------------------------------------------------------------------------------
# Operational Extensions Panel
# -------------------------------------------------------------------------------------------------
elif view_mode == "Operational Extensions (Org-Specific)":
    st.header("🛰 Operational Extensions — Org-Specific Catalogues")
    st.markdown(
        """
This section lets you update the **operational surface** of your programme by maintaining the following org-specific catalogues:

- **CRT-AS** — Asset & technology landscape
- **CRT-D** — Data & classification catalogue
- **CRT-I** — Identity zones & trust anchors
- **CRT-SC** — Supply-chain & vendor catalogue
- **CRT-T** — Telemetry & signal sources

These catalogues describe **your real environment** and connect back into the CRT backbone via
data classes (CRT-D) and structural controls (CRT-C).

**Workflow (simple):** download the active catalogue → edit locally → upload back → save.

If mistakes occur, restore the shipped default catalogue from the `/defaults` folder (or use 🧹 Maintenance for restore/replace).
"""
    )

    with st.expander("ℹ️ Help & Guidance — Working With Operational Catalogues", expanded=False):
        help_md = load_markdown_file(HELP_OS_MD)
        if help_md:
            st.markdown(help_md, unsafe_allow_html=True)
        else:
            st.info(
                "Help content for this section is not currently available. "
                "Please ensure the file defined by `HELP_OS_MD` "
                "(for example `/docs/help_operational_extensions.md`) exists and is readable."
            )

    # Choose a single operational catalogue to view / extend (mirrors Governance Setup pattern)
    selected_op_name = st.selectbox(
        "Choose an operational catalogue to view / extend",
        options=OPERATIONAL_CATALOGUES,
        format_func=lambda x: CATALOGUES_CONFIG.get(x, {}).get("label", x),
    )

    # ------------------------------------------------------------
    # Resolve file paths using YOUR existing scheme
    # ------------------------------------------------------------
    defaults_dir = os.path.join(PROJECT_PATH, "apps", "data_sources", "defaults")

    cfg = CATALOGUES_CONFIG.get(selected_op_name, {})
    filename = cfg.get("filename") or f"{selected_op_name}.csv"

    live_path = os.path.join(CRT_CATALOGUE_DIR, filename)
    default_path = os.path.join(defaults_dir, filename)

    # Sample template naming (matches your existing samples tree)
    sample_filename = f"{selected_op_name}.sample.csv"
    sample_path = os.path.join(SAMPLES_DIR, sample_filename)

    st.markdown("#### 📄 Current Effective Catalogue")
    eff_op_df = catalogues_effective.get(selected_op_name, pd.DataFrame())
    if eff_op_df.empty:
        st.info("No data found for this catalogue yet.")
    else:
        st.dataframe(eff_op_df, width="stretch")

    # ------------------------------------------------------------
    # Where do I get the file to edit? (Download actions)
    # ------------------------------------------------------------
    st.markdown("---")
    with st.expander("📥 Where do I get the file to edit?", expanded=False):
        st.caption(
            "Download the **active catalogue**, edit it locally, then upload it back to overwrite the working file. "
            "Shipped defaults are provided as a **restore reference** if you need to roll back."
        )

        with st.expander("How this works (simple)", expanded=False):
            st.markdown(
                f"""
        - **Edit path (recommended):** download **Active catalogue**, edit locally, then use **Upload & Overwrite**.
        - **What happens on upload:** the active file is overwritten, a timestamped backup is created, and the JSON reference model is regenerated automatically.
        - **Defaults:** shipped baseline files are **restore references only**.
        - **Restore (recommended):** use 🎛 Programme Builder & AI Export → 🧹 Maintenance → Operational Extensions (for {selected_op_name}).
        - **Manual copying is not recommended:** copying files directly into `crt_catalogues/` does **not** regenerate JSON views and may leave the system out of sync.
        """
            )

        with st.expander("Show active catalogue location", expanded=False):
            st.code(f"{live_path}", language="text")

        with st.expander("Show shipped default location (restore reference only)", expanded=False):
            st.caption(
                "Read-only reference. Do not edit or copy this file directly into the working directory. "
                "Use the restore flow to ensure backups and JSON regeneration occur correctly."
            )
            st.code(f"{default_path}", language="text")


        c1, c2, c3, c4 = st.columns(4)

        # 1) Active catalogue (edit this)
        with c1:
            if os.path.exists(live_path):
                try:
                    live_bytes = open(live_path, "rb").read()
                    st.download_button(
                        "⬇️ Active catalogue (edit this)",
                        data=live_bytes,
                        file_name=os.path.basename(live_path),
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read active catalogue file — {exc}")
                    st.button("⬇️ Active catalogue (edit this)", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Active catalogue (edit this)", disabled=True, use_container_width=True)

        # 2) Latest backup (restore reference)
        with c2:
            latest_backup = get_latest_backup_path(selected_op_name)
            if latest_backup and os.path.exists(latest_backup):
                try:
                    backup_bytes = open(latest_backup, "rb").read()
                    st.download_button(
                        "⬇️ Latest backup (restore only)",
                        data=backup_bytes,
                        file_name=os.path.basename(latest_backup),
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read backup file — {exc}")
                    st.button("⬇️ Latest backup (restore only)", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Latest backup (restore only)", disabled=True, use_container_width=True)

        # 3) Shipped default (restore reference)
        with c3:
            if os.path.exists(default_path):
                try:
                    default_bytes = open(default_path, "rb").read()
                    st.download_button(
                        "⬇️ Shipped default (restore only)",
                        data=default_bytes,
                        file_name=f"{selected_op_name}.default.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read default catalogue file — {exc}")
                    st.button("⬇️ Shipped default (restore only)", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Shipped default (restore only)", disabled=True, use_container_width=True)

        # 4) Sample template (scaffold)
        with c4:
            if os.path.exists(sample_path):
                try:
                    sample_bytes = open(sample_path, "rb").read()
                    st.download_button(
                        "⬇️ Sample template",
                        data=sample_bytes,
                        file_name=os.path.basename(sample_path),
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.warning(f"Could not read sample template — {exc}")
                    st.button("⬇️ Sample template", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Sample template", disabled=True, use_container_width=True)
    st.markdown("#### 📤 Upload & Overwrite (Active Catalogue)")
    st.caption(
        "Upload a CSV to overwrite the active working file (e.g. `CRT-AS.csv`). "
        "CRT creates a timestamped backup in `/backup` and regenerates the JSON view in `/json` automatically.\n\n"
        "If you need to roll back, you can upload a previously downloaded backup or the shipped default file."
    )

    # Sample / Template Files for operational catalogues (generic pattern)
    with st.expander("📘 Sample & Template Files — Operational Catalogues", expanded=False):
        st.markdown(f"### {CATALOGUES_CONFIG.get(selected_op_name, {}).get('label', selected_op_name)} Sample")

        if os.path.exists(sample_path):
            try:
                sample_df = read_csv_with_fallback(sample_path)
                if sample_df.empty:
                    st.info("Sample file loaded, but contains no rows.")
                else:
                    st.dataframe(sample_df, width="stretch")
            except Exception as exc:
                st.warning(f"Could not load {sample_filename} — {exc}")
        else:
            st.info(f"`{sample_filename}` not found in samples directory.")

    # Upload override for the selected operational catalogue

    uploaded_op = st.file_uploader(
        "Choose a CSV file (replaces current working catalogue)",
        type=["csv"],
        key=f"upload_{selected_op_name}",
    )

    if uploaded_op is not None:
        if st.button("💾 Overwrite & Save", key=f"save_{selected_op_name}"):
            try:
                active_path = overwrite_catalogue_with_backup(selected_op_name, uploaded_op)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(
                    f"✅ {selected_op_name} updated. Previous version backed up to `/backup`."
                )
                try:
                    eff_df = read_csv_with_fallback(active_path)
                    json_path = write_catalogue_json_view(selected_op_name, eff_df)
                    st.caption(
                        f"Reference model updated: `{os.path.relpath(json_path, PROJECT_PATH)}`"
                    )
                except Exception as exc:
                    st.warning(f"Could not update JSON reference model - {exc}")


# -------------------------------------------------------------------------------------------------
# Mapping Explorer Panel
# -------------------------------------------------------------------------------------------------
elif view_mode == "Mapping Explorer":
    st.header("🔗 Structural Mapping Explorer — Requirements, Policies, Standards, Obligations")
    st.markdown(
        """
This read-only view shows how governance catalogues map structurally into the CRT backbone.

- **Requirements (CRT-REQ)** → CRT-C controls → CRT-F failures / CRT-N compensations, plus which
  policies, standards, and obligations touch the same control bundle.
- **Policies (CRT-POL)** → CRT-C controls → CRT-F failures / CRT-N compensations → CRT-LR obligations.
- **Standards (CRT-STD)** → CRT-C controls → CRT-F failures / CRT-N compensations → CRT-LR obligations.
- **Obligations (CRT-LR)** → CRT-C controls → CRT-F failures / CRT-N compensations.

Mappings are driven by the `mapped_*` columns in the catalogues. All relationships shown here are
**structural and conceptual**, not advisory or assurance.

The lenses shown below reflect structural relationships based on the catalogue data currently loaded.

- **CRT-REQ** and **CRT-LR** include the shipped defaults and may be extended through **Governance Setup**.
- **CRT-POL** and **CRT-STD** are shipped as **read-only baseline catalogues**, showing how the default
  policy and standard families align with CRT-C. These files are not modified in this module.
- Organisation-specific policy and standard artefacts are created in **Policy & Standard Orchestration**
  and are not written back into CRT-POL or CRT-STD.
"""
    )

    # We still allow uc_df to be passed into lenses where useful for legacy/questionnaire context,
    # but CRT-REQ is the primary requirements overlay.
    uc_df = catalogues_effective.get("CRT-UC", pd.DataFrame())
    req_df = catalogues_effective.get("CRT-REQ", pd.DataFrame())
    pol_df = catalogues_effective.get("CRT-POL", pd.DataFrame())
    lr_df = catalogues_effective.get("CRT-LR", pd.DataFrame())
    std_df = catalogues_effective.get("CRT-STD", pd.DataFrame())
    c_df = catalogues_effective.get("CRT-C", pd.DataFrame())
    f_df = catalogues_effective.get("CRT-F", pd.DataFrame())
    n_df = catalogues_effective.get("CRT-N", pd.DataFrame())

    if req_df.empty and pol_df.empty and std_df.empty and lr_df.empty:
        st.info(
            "No governance catalogue data found yet. Populate CRT-REQ and CRT-LR via Governance Setup. "
            "CRT-POL and CRT-STD are provided as read-only defaults and will appear here when present."
        )
    else:
        tab_req, tab_pol, tab_std, tab_lr = st.tabs(
            [
                "📋 Requirements Lens",
                "📜 Policy Lens",
                "📏 Standard Lens",
                "⚖️ Obligation Lens",
            ]
        )

        with tab_req:
            render_requirement_lens(req_df, c_df, pol_df, std_df, lr_df, f_df, n_df)

        with tab_pol:
            render_policy_lens(pol_df, uc_df, c_df, lr_df, f_df, n_df)

        with tab_std:
            render_standard_lens(std_df, c_df, lr_df, f_df, n_df)

        with tab_lr:
            render_obligation_lens(lr_df, uc_df, c_df, pol_df, std_df, f_df, n_df)

st.sidebar.divider()
with st.sidebar.expander("ℹ️ About & Support"):
    support_md = load_markdown_file(ABOUT_SUPPORT_MD)
    if support_md:
        st.markdown(support_md, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
st.divider()
st.caption(
    "© Blake Media Ltd. | Cyber Resilience Toolkit by Blake Wiltshire — "
    "All content is structural and conceptual; no configuration, advice, or assurance is provided."
)
