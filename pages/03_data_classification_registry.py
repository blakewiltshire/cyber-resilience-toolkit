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
🧮 Data Classification Registry — Cyber Resilience Toolkit (CRT)

Define and explore data sensitivity tiers, categories, propagation rules,
and structural control inheritance. This module provides a structural,
read-only view of how data classes interact with CRT controls across
environments.

Views provided:

- 📊 Catalogue Overview
  - Tabular view of all data classes with lightweight filters
  - Integrated 📈 Coverage & Metrics (descriptive only)
  - Optional per-class inspection panel

- 📦 Optional Data Scope for Tasks
  - Export-only, normalised `bundle_type = "data"` context bundle
  - Supports single class, multi-class cluster, and segment scopes
  - Lens pages are **build + preview + persist** (disk shelf only)
  - Maintenance / attachment is handled in 🧠 AI Observation Console
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
except Exception:  # pylint: disable=broad-except, wrong-import-position
    get_sih = None  # type: ignore


# -------------------------------------------------------------------------------------------------
# Resolve Key Paths (for modules under /pages)
# -------------------------------------------------------------------------------------------------
PATHS = get_named_paths(__file__)
PROJECT_PATH = PATHS["level_up_1"]

ABOUT_APP_MD = os.path.join(PROJECT_PATH, "docs", "about_data_classification_registry.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")

# Optional per-view help docs
HELP_VIEW_OVERVIEW_MD = os.path.join(PROJECT_PATH, "docs", "help_data_classification_overview.md")
HELP_VIEW_INSPECTOR_MD = os.path.join(PROJECT_PATH, "docs", "help_data_classification_inspector.md")
HELP_VIEW_METRICS_MD = os.path.join(PROJECT_PATH, "docs", "help_data_classification_metrics.md")

BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# CRT catalogue locations — used only as a fallback if SIH is not available
CATALOGUE_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "crt_catalogues")
CRT_D_CSV = os.path.join(CATALOGUE_DIR, "CRT-D.csv")  # Data classification catalogue
CRT_C_CSV = os.path.join(CATALOGUE_DIR, "CRT-C.csv")  # Controls catalogue (for summaries)

# Workspace shelf for lens snapshots (disk persistence)
DCR_LENS_SHELF_DIR = os.path.join(
    PROJECT_PATH, "apps", "data_sources", "crt_workspace", "lenses", "dcr", "bundles"
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
# Lens shelf helpers (Disk persistence only — maintenance handled in 🧠 AI Observation Console)
# -------------------------------------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:  # pylint: disable=broad-except
        pass


def _utc_stamp() -> str:
    # Filename-safe + sortable (UTC, timezone-aware)
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


def _derive_lens_label(bundle: Dict[str, Any]) -> str:
    # Example: "🧮 DCR — Data Scope (data_cluster: CRT-D-cluster-abcdef12)"
    pe = bundle.get("primary_entity") if isinstance(bundle.get("primary_entity"), dict) else {}
    pe_type = pe.get("type") if isinstance(pe, dict) else None
    pe_id = pe.get("id") if isinstance(pe, dict) else None
    if pe_type and pe_id:
        return f"🧮 DCR — Data Scope ({pe_type}: {pe_id})"
    return "🧮 DCR — Data Scope"


def _save_json_file(path: str, payload: Dict[str, Any]) -> bool:
    try:
        _ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except Exception:  # pylint: disable=broad-except
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
    Load CRT-D and CRT-C catalogues in a read-only manner.

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
                "CRT-D": sih.get_catalogue("CRT-D"),
                "CRT-C": sih.get_catalogue("CRT-C"),
            }
        except Exception:  # pylint: disable=broad-except
            # Fallback path retains app usability even if SIH is not initialised yet.
            pass

    # Fallback: direct CSV read (still read-only)
    return {
        "CRT-D": _safe_read_csv(CRT_D_CSV),
        "CRT-C": _safe_read_csv(CRT_C_CSV),
    }


def _first_present_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return the first column name from `candidates` that exists in `df`."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _prepare_view(df_d: pd.DataFrame, df_c: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    """
    Prepare the classification view and identify key columns dynamically.

    - Detects tier/category/environment/propagation/link columns
    - Adds derived columns:
      - mapped_control_count
      - has_propagation_rules
      - linked_control_summary (best-effort, CRT-C join)
    """
    if df_d.empty:
        return pd.DataFrame(), {}

    df_view = df_d.copy()

    tier_col = _first_present_column(df_view, ["data_tier", "tier", "classification_tier"])
    category_col = _first_present_column(df_view, ["data_category", "category"])
    env_col = _first_present_column(df_view, ["environment", "env", "data_environment", "context"])
    desc_col = _first_present_column(df_view, ["description", "data_description", "summary"])
    examples_col = _first_present_column(df_view, ["examples", "example_values", "sample_assets"])
    propagation_col = _first_present_column(df_view, ["propagation_rules", "propagation", "flow_notes", "sharing_rules"])
    linked_controls_col = _first_present_column(df_view, ["mapped_control_ids", "linked_controls"])

    if linked_controls_col:

        def _count_controls(raw) -> int:
            if pd.isna(raw):
                return 0
            parts = str(raw).replace(";", ",").split(",")
            parts = [p.strip() for p in parts if p.strip()]
            return len(set(parts))

        df_view["mapped_control_count"] = df_view[linked_controls_col].apply(_count_controls)
    else:
        df_view["mapped_control_count"] = 0

    if propagation_col:
        df_view["has_propagation_rules"] = df_view[propagation_col].fillna("").astype(str).str.len() > 0
    else:
        df_view["has_propagation_rules"] = False

    if linked_controls_col and not df_c.empty and "control_id" in df_c.columns:
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
                names.append(f"{cid} — {label}" if label else cid)
            return "; ".join(names)

        df_view["linked_control_summary"] = df_view[linked_controls_col].apply(_resolve_controls)
    else:
        df_view["linked_control_summary"] = ""

    colmap = {
        "tier_col": tier_col,
        "category_col": category_col,
        "env_col": env_col,
        "desc_col": desc_col,
        "examples_col": examples_col,
        "propagation_col": propagation_col,
        "linked_controls_col": linked_controls_col,
    }

    return df_view, colmap


def _build_class_label(row: pd.Series, colmap: Dict[str, Optional[str]]) -> str:
    """Human-readable label using Tier / Category / Environment."""
    tier_col = colmap.get("tier_col")
    category_col = colmap.get("category_col")
    env_col = colmap.get("env_col")

    parts: List[str] = []
    if tier_col and tier_col in row.index and pd.notna(row.get(tier_col)):
        parts.append(str(row[tier_col]))
    if category_col and category_col in row.index and pd.notna(row.get(category_col)):
        parts.append(str(row[category_col]))
    if env_col and env_col in row.index and pd.notna(row.get(env_col)):
        parts.append(f"[{row[env_col]}]")

    return " — ".join(parts) if parts else "Unlabelled class"


def _detect_id_column(df_view: pd.DataFrame) -> Optional[str]:
    """Detect a likely primary identifier column for CRT-D entries."""
    return _first_present_column(df_view, ["data_id", "d_id", "class_id", "id"])


def _row_to_data_entity(row: pd.Series, colmap: Dict[str, Optional[str]], id_col: Optional[str]) -> Dict[str, object]:
    """
    Convert a CRT-D row into a normalised data-domain entity for context bundles.
    Structural-only: identifiers + key attributes + raw row.
    """
    if id_col and id_col in row.index and pd.notna(row[id_col]):
        entity_id = str(row[id_col])
    else:
        entity_id = _build_class_label(row, colmap) or f"row-{row.name}"

    tier_col = colmap.get("tier_col")
    category_col = colmap.get("category_col")
    env_col = colmap.get("env_col")

    entity: Dict[str, object] = {
        "catalogue": "CRT-D",
        "id": entity_id,
        "raw": row.to_dict(),
    }
    if tier_col and tier_col in row.index:
        entity["tier"] = row[tier_col]
    if category_col and category_col in row.index:
        entity["category"] = row[category_col]
    if env_col and env_col in row.index:
        entity["environment"] = row[env_col]

    return entity


def _compute_coverage(df_scope: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> Dict[str, int]:
    """Descriptive coverage metrics for a given scope of data classes."""
    if df_scope.empty:
        return {
            "total_classes_in_scope": 0,
            "distinct_tiers_in_scope": 0,
            "distinct_categories_in_scope": 0,
            "distinct_environments_in_scope": 0,
            "classes_with_mapped_controls_in_scope": 0,
            "classes_with_propagation_rules_in_scope": 0,
        }

    tier_col = colmap.get("tier_col")
    category_col = colmap.get("category_col")
    env_col = colmap.get("env_col")
    linked_controls_col = colmap.get("linked_controls_col")

    total_classes = len(df_scope)
    tier_count = df_scope[tier_col].dropna().astype(str).nunique() if tier_col and tier_col in df_scope.columns else 0
    category_count = (
        df_scope[category_col].dropna().astype(str).nunique() if category_col and category_col in df_scope.columns else 0
    )
    env_count = df_scope[env_col].dropna().astype(str).nunique() if env_col and env_col in df_scope.columns else 0

    if linked_controls_col and linked_controls_col in df_scope.columns:

        def _has_controls(val: object) -> bool:
            if pd.isna(val):
                return False
            s = str(val).strip()
            if not s:
                return False
            parts = [p.strip() for p in s.replace(";", ",").split(",")]
            return any(parts)

        with_mapped_controls = int(df_scope[linked_controls_col].apply(_has_controls).sum())
    else:
        with_mapped_controls = 0

    with_propagation = int(df_scope["has_propagation_rules"].sum()) if "has_propagation_rules" in df_scope.columns else 0

    return {
        "total_classes_in_scope": int(total_classes),
        "distinct_tiers_in_scope": int(tier_count),
        "distinct_categories_in_scope": int(category_count),
        "distinct_environments_in_scope": int(env_count),
        "classes_with_mapped_controls_in_scope": int(with_mapped_controls),
        "classes_with_propagation_rules_in_scope": int(with_propagation),
    }


# -------------------------------------------------------------------------------------------------
# View 1 — Catalogue Overview (with inspection)
# -------------------------------------------------------------------------------------------------
def render_view_overview(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📊 Classification Catalogue Overview")
    st.markdown(
        """
Use this view to **scan the overall structure** of your data classification model:

- Which tiers and categories exist
- How many classes are defined
- Where propagation rules and mapped controls are present

Metrics shown here are **structural and descriptive only**. They do not score maturity or provide assurance.
"""
    )

    with st.expander("ℹ️ Help & Guidance — Overview", expanded=False):
        render_markdown_file(
            HELP_VIEW_OVERVIEW_MD,
            fallback=(
                "This overview presents the effective CRT-D catalogue as a table, with simple structural metrics. "
                "Use the per-class panel below to inspect a single data class in more detail. "
                "Structural changes are made in the Command Centre."
            ),
        )

    if df_view.empty:
        st.warning("No data classes found in CRT-D. Populate CRT-D via the Command Centre.")
        return

    st.markdown("### 📈 Coverage & Metrics (structural, descriptive)")
    coverage = _compute_coverage(df_view, colmap)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Data Classes", value=coverage["total_classes_in_scope"])
    with m2:
        st.metric("Distinct Tiers", value=coverage["distinct_tiers_in_scope"])
    with m3:
        st.metric("Distinct Categories", value=coverage["distinct_categories_in_scope"])

    m4, m5, m6 = st.columns(3)
    with m4:
        st.metric("Distinct Environments", value=coverage["distinct_environments_in_scope"])
    with m5:
        st.metric("Classes with mapped controls (CRT-C)", value=coverage["classes_with_mapped_controls_in_scope"])
    with m6:
        st.metric("Classes with Propagation Rules", value=coverage["classes_with_propagation_rules_in_scope"])

    with st.expander("ℹ️ Coverage & Metrics — Detail", expanded=False):
        render_markdown_file(
            HELP_VIEW_METRICS_MD,
            fallback=(
                "These metrics summarise how many data classes exist across tiers, categories, environments, "
                "and where mapped controls or propagation rules are recorded. They are purely descriptive."
            ),
        )

    st.markdown("### 🧮 All Data Classes")

    tier_col = colmap.get("tier_col")
    category_col = colmap.get("category_col")
    env_col = colmap.get("env_col")
    desc_col = colmap.get("desc_col")
    examples_col = colmap.get("examples_col")
    propagation_col = colmap.get("propagation_col")

    filter_col, table_col = st.columns([1, 3])

    with filter_col:
        st.markdown("#### 🔎 Filters")

        tier_choice = None
        category_choice = None
        env_choice = None

        if tier_col and tier_col in df_view.columns:
            tiers = ["(All tiers)"] + sorted(df_view[tier_col].dropna().astype(str).unique().tolist())
            tier_choice = st.selectbox("Tier", tiers)

        if category_col and category_col in df_view.columns:
            cats = ["(All categories)"] + sorted(df_view[category_col].dropna().astype(str).unique().tolist())
            category_choice = st.selectbox("Category", cats)

        if env_col and env_col in df_view.columns:
            envs = ["(All environments)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
            env_choice = st.selectbox("Environment / Context", envs)

        text_filter = st.text_input("Description / examples contains", "")
        only_with_propagation = st.checkbox("Only classes with propagation rules", value=False)
        only_with_mapped_controls = st.checkbox("Only classes with mapped controls (CRT-C)", value=False)

    with table_col:
        df_filtered = df_view.copy()

        if tier_col and tier_choice and tier_choice != "(All tiers)":
            df_filtered = df_filtered[df_filtered[tier_col].astype(str) == tier_choice]

        if category_col and category_choice and category_choice != "(All categories)":
            df_filtered = df_filtered[df_filtered[category_col].astype(str) == category_choice]

        if env_col and env_choice and env_choice != "(All environments)":
            df_filtered = df_filtered[df_filtered[env_col].astype(str) == env_choice]

        if text_filter:
            text_filter_lower = text_filter.lower()
            text_cols: List[str] = []
            for col in (desc_col, examples_col, propagation_col):
                if col and col in df_filtered.columns:
                    text_cols.append(col)

            if text_cols:
                mask = False
                for col in text_cols:
                    series = df_filtered[col].astype(str).str.lower().str.contains(text_filter_lower)
                    mask = series if isinstance(mask, bool) else (mask | series)
                if not isinstance(mask, bool):
                    df_filtered = df_filtered[mask]

        if only_with_propagation and "has_propagation_rules" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["has_propagation_rules"]]

        if only_with_mapped_controls and "mapped_control_count" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["mapped_control_count"] > 0]

        if df_filtered.empty:
            st.info("No data classes match the selected filters.")
        else:
            cols_to_hide = {"mapped_control_ids", "mapped_control_count", "has_propagation_rules", "linked_control_summary"}
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "data_id",
                "data_name",
                "definition",
                "data_tier",
                "classification_level",
                "data_category",
                "environment",
                "confidentiality_impact",
                "integrity_impact",
                "availability_impact",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("### 🧬 Inspect a Single Data Class (optional)")

    if df_filtered.empty:
        st.caption("Adjust filters above to enable per-class inspection.")
        return

    df_filtered = df_filtered.reset_index(drop=True)
    labels = [_build_class_label(row, colmap) for _, row in df_filtered.iterrows()]
    inspect_labels = ["(None selected)"] + labels

    selected_label = st.selectbox("Select a data class to inspect", options=inspect_labels, index=0)

    if selected_label == "(None selected)":
        st.caption("Choose a class to see structural details and mapped controls.")
        return

    idx = labels.index(selected_label)
    class_row = df_filtered.iloc[[idx]]

    linked_controls_col = colmap.get("linked_controls_col")

    details_col, col_controls = st.columns([2, 2])

    with details_col:
        st.markdown("#### Structural Attributes")

        if tier_col and tier_col in class_row.columns:
            st.write(f"**Tier:** {class_row[tier_col].iloc[0]}")
        if category_col and category_col in class_row.columns:
            st.write(f"**Category:** {class_row[category_col].iloc[0]}")
        if env_col and env_col in class_row.columns:
            st.write(f"**Environment / Context:** {class_row[env_col].iloc[0]}")

        if desc_col and desc_col in class_row.columns:
            desc_val = class_row[desc_col].iloc[0]
            if pd.notna(desc_val) and str(desc_val).strip():
                st.markdown("**Description**")
                st.write(str(desc_val))

        if examples_col and examples_col in class_row.columns:
            ex_val = class_row[examples_col].iloc[0]
            if pd.notna(ex_val) and str(ex_val).strip():
                st.markdown("**Examples**")
                st.write(str(ex_val))

        if propagation_col and propagation_col in class_row.columns:
            rules = class_row[propagation_col].iloc[0]
            if pd.isna(rules) or not str(rules).strip():
                st.caption("No propagation rules recorded for this class.")
            else:
                st.markdown("**Propagation Rules**")
                st.code(str(rules), language="text")

    with col_controls:
        st.markdown("#### 🧱 Structural Control Inheritance")

        if linked_controls_col and linked_controls_col in class_row.columns:
            raw_links = class_row[linked_controls_col].iloc[0]
            summary = class_row["linked_control_summary"].iloc[0]
            if pd.isna(raw_links) or not str(raw_links).strip():
                st.caption("No mapped CRT-C controls recorded for this class.")
            else:
                st.markdown("**Mapped controls (CRT-C IDs)**")
                st.code(str(raw_links), language="text")

                if isinstance(summary, str) and summary.strip():
                    st.markdown("**Resolved Control Summary**")
                    st.write(summary)
                else:
                    st.caption("No control names resolved; check `CRT-C.csv` for matching IDs.")
        else:
            st.caption("No `mapped_control_ids` / `linked_controls` column present in the classification catalogue.")


# -------------------------------------------------------------------------------------------------
# View 2 — Optional Data Scope for Tasks (export-only + disk shelf persistence)
# -------------------------------------------------------------------------------------------------
def render_view_context_bundles(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📦 Optional Data Scope for Tasks")

    st.markdown(
        """
Most users can **skip this step** and go straight to **🎛 Programmes — Task Builder**.

Use this page **only if you want AI-driven tasks to talk about a specific patch of data**
(for example, “Tier 1 customer data in EU production systems”).

Whatever you choose here:

- It does **not** edit CRT-D or configure controls
- You will see the bundle JSON before using it
- You can review and attach lenses in **🧠 AI Observation Console**
  **before anything is sent to an external AI model**
"""
    )

    if df_view.empty:
        st.warning("No data classes available — cannot build a data scope bundle.")
        return

    st.markdown("### 0️⃣ Do you want a focused data scope?")
    activation_mode = st.radio(
        "Choose an option:",
        [
            "Don’t define a special data scope (use everything)",
            "Define a focused data scope (optional)",
        ],
        index=0,
        help=(
            "If you’re not sure, use the first option. Lens maintenance and attachment happens in "
            "🧠 AI Observation Console."
        ),
    )

    if activation_mode == "Don’t define a special data scope (use everything)":
        st.info(
            "Downstream tools will see your **entire data classification catalogue** from CRT-D.\n\n"
            "If you later decide to focus scope, return here to build a DCR lens and save it to the disk shelf."
        )
        return

    st.info(
        "You’re defining a **focused data scope**. This does **not** change CRT-D.\n\n"
        "This module will: **build → preview → persist** the lens (disk shelf). "
        "Attachment and maintenance is handled in 🧠 AI Observation Console."
    )

    id_col = _detect_id_column(df_view)

    tier_col = colmap.get("tier_col")
    category_col = colmap.get("category_col")
    env_col = colmap.get("env_col")

    st.markdown("### 1️⃣ Choose Scope Mode")
    scope_mode = st.radio(
        "Scope mode",
        ["Single data class", "Multi-class cluster", "Tier / segment scope"],
        help="Choose whether to focus on a single class, a small cluster, or a segment defined by filters.",
    )

    scope_df = pd.DataFrame()
    primary_entity: Dict[str, object] = {}
    filters: Dict[str, object] = {}

    st.markdown("### 2️⃣ Select Data Scope")

    # Pattern A — Single Entity Focus
    if scope_mode == "Single data class":
        filter_col, table_col = st.columns([1, 2])

        with filter_col:
            tier_choice = None
            category_choice = None
            env_choice = None

            if tier_col and tier_col in df_view.columns:
                tiers = ["(Any tier)"] + sorted(df_view[tier_col].dropna().astype(str).unique().tolist())
                tier_choice = st.selectbox("Tier", tiers)

            if category_col and category_col in df_view.columns:
                cats = ["(Any category)"] + sorted(df_view[category_col].dropna().astype(str).unique().tolist())
                category_choice = st.selectbox("Category", cats)

            if env_col and env_col in df_view.columns:
                envs = ["(Any environment)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
                env_choice = st.selectbox("Environment / Context", envs)

            text_filter = st.text_input("Description / examples contains", "")

        with table_col:
            df_filtered = df_view.copy()

            if tier_col and tier_choice and tier_choice != "(Any tier)":
                df_filtered = df_filtered[df_filtered[tier_col].astype(str) == tier_choice]

            if category_col and category_choice and category_choice != "(Any category)":
                df_filtered = df_filtered[df_filtered[category_col].astype(str) == category_choice]

            if env_col and env_choice and env_choice != "(Any environment)":
                df_filtered = df_filtered[df_filtered[env_col].astype(str) == env_choice]

            if text_filter:
                text_filter_lower = text_filter.lower()
                text_cols: List[str] = []
                for col in (colmap.get("desc_col"), colmap.get("examples_col"), colmap.get("propagation_col")):
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
                st.info("No data classes match the selected filters.")
                st.stop()

            st.markdown("#### Matching Data Classes")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_class_label(row, colmap) for _, row in df_filtered.iterrows()]
        selected_label = st.selectbox("Data class to use as primary focus", options=labels)
        idx = labels.index(selected_label)

        scope_df = df_filtered.iloc[[idx]]
        row = scope_df.iloc[0]
        primary_id = str(row[id_col]) if id_col and id_col in row.index and pd.notna(row[id_col]) else (
            _build_class_label(row, colmap) or f"row-{row.name}"
        )
        primary_entity = {"type": "data_class", "id": primary_id}

    # Pattern B — Cluster
    elif scope_mode == "Multi-class cluster":
        filter_col, table_col = st.columns([1, 2])

        with filter_col:
            tier_choice = None
            category_choice = None
            env_choice = None

            if tier_col and tier_col in df_view.columns:
                tiers = ["(Any tier)"] + sorted(df_view[tier_col].dropna().astype(str).unique().tolist())
                tier_choice = st.selectbox("Tier", tiers)

            if category_col and category_col in df_view.columns:
                cats = ["(Any category)"] + sorted(df_view[category_col].dropna().astype(str).unique().tolist())
                category_choice = st.selectbox("Category", cats)

            if env_col and env_col in df_view.columns:
                envs = ["(Any environment)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
                env_choice = st.selectbox("Environment / Context", envs)

        with table_col:
            df_filtered = df_view.copy()

            if tier_col and tier_choice and tier_choice != "(Any tier)":
                df_filtered = df_filtered[df_filtered[tier_col].astype(str) == tier_choice]

            if category_col and category_choice and category_choice != "(Any category)":
                df_filtered = df_filtered[df_filtered[category_col].astype(str) == category_choice]

            if env_col and env_choice and env_choice != "(Any environment)":
                df_filtered = df_filtered[df_filtered[env_col].astype(str) == env_choice]

            if df_filtered.empty:
                st.info("No data classes match the selected filters.")
                st.stop()

            st.markdown("#### Available Data Classes for Cluster")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_class_label(row, colmap) for _, row in df_filtered.iterrows()]
        cluster_labels = st.multiselect("Select data classes to include in the cluster", options=labels)

        if not cluster_labels:
            st.info("Select at least one data class to form a cluster.")
            st.stop()

        indices = [labels.index(lbl) for lbl in cluster_labels]
        scope_df = df_filtered.iloc[indices]

        base_ids: List[str] = []
        for _, row in scope_df.iterrows():
            if id_col and id_col in row.index and pd.notna(row[id_col]):
                base_ids.append(str(row[id_col]))
            else:
                base_ids.append(_build_class_label(row, colmap) or f"row-{row.name}")

        cluster_key = ",".join(sorted(base_ids))
        cluster_id = f"CRT-D-cluster-{hashlib.sha256(cluster_key.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "data_cluster", "id": cluster_id}

    # Pattern C — Segment
    else:
        st.markdown("#### Define Segment Filters")

        tier_choice = None
        category_choice = None
        env_choice = None

        if tier_col and tier_col in df_view.columns:
            tiers = ["(Any tier)"] + sorted(df_view[tier_col].dropna().astype(str).unique().tolist())
            tier_choice = st.selectbox("Tier", tiers)

        if category_col and category_col in df_view.columns:
            cats = ["(Any category)"] + sorted(df_view[category_col].dropna().astype(str).unique().tolist())
            category_choice = st.selectbox("Category", cats)

        if env_col and env_col in df_view.columns:
            envs = ["(Any environment)"] + sorted(df_view[env_col].dropna().astype(str).unique().tolist())
            env_choice = st.selectbox("Environment / Context", envs)

        scope_df = df_view.copy()

        if tier_col and tier_choice and tier_choice != "(Any tier)":
            scope_df = scope_df[scope_df[tier_col].astype(str) == tier_choice]
            filters["tier"] = tier_choice

        if category_col and category_choice and category_choice != "(Any category)":
            scope_df = scope_df[scope_df[category_col].astype(str) == category_choice]
            filters["category"] = category_choice

        if env_col and env_choice and env_choice != "(Any environment)":
            scope_df = scope_df[scope_df[env_col].astype(str) == env_choice]
            filters["environment"] = env_choice

        st.markdown("#### Segment Preview")
        if scope_df.empty:
            st.info("No data classes match this segment definition. The bundle will have an empty data_domains list.")
        else:
            st.dataframe(scope_df, width="stretch", hide_index=True)

        filter_str = json.dumps(filters, sort_keys=True) if filters else "all"
        segment_id = f"CRT-D-segment-{hashlib.sha256(filter_str.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "data_segment", "id": segment_id, "filters": filters}

    if scope_df is None or primary_entity == {}:
        st.warning("Unable to determine scope or primary entity — please review selections.")
        return

    st.markdown("### 3️⃣ Bundle Summary")
    coverage = _compute_coverage(scope_df, colmap)

    st.write(
        f"- **Scope mode:** `{scope_mode}`  \n"
        f"- **Classes in scope:** `{coverage['total_classes_in_scope']}`  \n"
        f"- **Primary entity:** `{primary_entity.get('type')}` → `{primary_entity.get('id')}`"
    )

    data_entities = [_row_to_data_entity(row, colmap, id_col) for _, row in scope_df.iterrows()]

    bundle: Dict[str, Any] = {
        "bundle_type": "data",
        "module": "🧮 Data Classification Registry",
        "primary_entity": primary_entity,
        "entities": {
            "assets": [],
            "identities": [],
            "data_domains": data_entities,
            "vendors": [],
            "controls": [],
            "failures": [],
            "telemetry": [],
        },
        "relationships": [],
        "structural_findings": {
            "gaps": [],
            "compensations": [],
            "coverage": coverage,
            "propagation_paths": [],
        },
        "guardrails": {
            "no_advice": True,
            "no_configuration": True,
            "no_assurance": True,
        },
        # Lens metadata for downstream shelf maintenance (AOC)
        "lens_meta": {
            "lens_family": "dcr",
            "lens_label": _derive_lens_label({"primary_entity": primary_entity}),
            "built_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z",
            "source_module": "🧮 Data Classification Registry",
            "persisted_to_disk": False,
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
            file_name="dcr_data_bundle.json",
            mime="application/json",
            use_container_width=True,
        )

    with b:
        if st.button("💾 Save to lens shelf", use_container_width=True):
            _ensure_dir(DCR_LENS_SHELF_DIR)

            pe = primary_entity if isinstance(primary_entity, dict) else {}
            pe_id = pe.get("id") if isinstance(pe, dict) else None

            name_hint = _safe_filename(str(pe_id)) if pe_id else "dcr-scope"
            filename = f"dcr_{name_hint}_{_utc_stamp()}.json"
            path = os.path.join(DCR_LENS_SHELF_DIR, filename)

            bundle["lens_meta"]["persisted_to_disk"] = True
            bundle["lens_meta"]["shelf_path_hint"] = f"lenses/dcr/bundles/{filename}"

            ok = _save_json_file(path, bundle)
            if ok:
                st.success(f"Saved to lens shelf: {filename}")
                st.caption("Load, tag, attach, or retire lenses inside 🧠 AI Observation Console.")
            else:
                st.error("Could not save to the lens shelf. Check filesystem permissions and path availability.")

    st.caption(
        "This lens is **export-only**. It does not configure controls, score maturity, or provide assurance. "
        "Lens maintenance and attachment happens in 🧠 AI Observation Console."
    )


# -------------------------------------------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Data Classification Registry",
    page_icon="🧮",
    layout="wide",
)

st.title("🧮 Data Classification Registry")
st.caption(
    "Define sensitivity tiers, propagation rules, and structural control inheritance — "
    "read-only exploration of your CRT-D classification model."
)

# -------------------------------------------------------------------------------------------------
# Info Panel
# -------------------------------------------------------------------------------------------------
with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "# 📚 Data Classification Registry\n\n"
            "This module surfaces the **effective CRT-D catalogue** in a structured, non-prescriptive way.\n\n"
            "- Explore data classes, tiers, and categories\n"
            "- Inspect propagation rules and environments\n"
            "- View structural links to CRT-C controls (where defined)\n"
            "- Optionally build an export-only `bundle_type = \"data\"` lens for downstream use\n\n"
            "It does **not** configure controls, score maturity, or provide assurance."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Load Catalogues
# -------------------------------------------------------------------------------------------------
CATALOGUES = _load_crt_catalogues()
DF_D = CATALOGUES.get("CRT-D", pd.DataFrame())
DF_C = CATALOGUES.get("CRT-C", pd.DataFrame())
DF_VIEW, COLMAP = _prepare_view(DF_D, DF_C)

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
st.sidebar.caption("Use the view selector below to switch between perspectives within the Data Classification Registry.")

st.sidebar.info(
    """
**🧮 Data Classification Registry**

Use this module to:

- Examine how data tiers and categories are defined
- View propagation rules and environments where classes appear
- Inspect structural control inheritance via mapped CRT-C controls
- (Optionally) build an export-only `bundle_type = "data"` lens for downstream use

All views are read-only. Catalogue updates and append operations are handled exclusively
via the 📂 Structural Controls & Frameworks — Command Centre and 🛰 Org-Specific Catalogues.
"""
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    ["📊 Catalogue Overview", "📦 Optional Data Scope for Tasks"],
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
elif view_mode == "📦 Optional Data Scope for Tasks":
    render_view_context_bundles(DF_VIEW, COLMAP)
else:
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
