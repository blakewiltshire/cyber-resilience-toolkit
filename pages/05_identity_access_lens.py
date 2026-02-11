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
🔐 Identity & Access Lens — Cyber Resilience Toolkit (CRT)

Explore identity and access anchors across users, services, machines,
and trust boundaries. This module provides a structural, read-only view
of how identities, privilege tiers, and trust anchors relate to CRT
controls (and, where present, associated assets/zones).

It is not a risk engine or access review workflow. It shows **what is
recorded today** in CRT-I and lets you optionally export a normalised
`bundle_type = "identity"` scope for downstream CRT modules.

Views provided:

- 📊 Catalogue Overview
  - Tabular view of all identity entries with lightweight filters
  - Integrated 📈 Coverage & Metrics (descriptive only)
  - Optional per-identity inspection panel

- 📦 Optional Identity Scope for Tasks
  - Optional, export-only `bundle_type = "identity"` context bundle
  - Supports single identity, multi-identity cluster, and segment scopes
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

ABOUT_APP_MD = os.path.join(PROJECT_PATH, "docs", "about_identity_access_lens.md")
ABOUT_SUPPORT_MD = os.path.join(PROJECT_PATH, "docs", "about_and_support.md")

# Optional per-view help docs
HELP_VIEW_OVERVIEW_MD = os.path.join(PROJECT_PATH, "docs", "help_identity_access_overview.md")
HELP_VIEW_SCOPE_MD = os.path.join(PROJECT_PATH, "docs", "help_identity_access_scope.md")

BRAND_LOGO_PATH = os.path.join(PROJECT_PATH, "brand", "blake_logo.png")

# CRT catalogue locations — used only as a fallback if SIH is not available
CATALOGUE_DIR = os.path.join(PROJECT_PATH, "apps", "data_sources", "crt_catalogues")
CRT_I_CSV = os.path.join(CATALOGUE_DIR, "CRT-I.csv")  # Identity & access catalogue
CRT_C_CSV = os.path.join(CATALOGUE_DIR, "CRT-C.csv")  # Controls catalogue (for summaries)

# Lens shelf (persisted JSON bundles)
IAL_LENS_SHELF_DIR = os.path.join(
    PROJECT_PATH,
    "apps",
    "data_sources",
    "crt_workspace",
    "lenses",
    "ial",
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
    Load CRT-I and CRT-C catalogues in a read-only manner.

    Preferred path is via SIH; fallback reads CSV directly.
    """
    if get_sih is not None:
        try:
            sih = get_sih()
            return {
                "CRT-I": sih.get_catalogue("CRT-I"),
                "CRT-C": sih.get_catalogue("CRT-C"),
            }
        except Exception:  # pylint: disable=broad-except
            pass

    return {
        "CRT-I": _safe_read_csv(CRT_I_CSV),
        "CRT-C": _safe_read_csv(CRT_C_CSV),
    }


def _first_present_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


# -------------------------------------------------------------------------------------------------
# View Preparation
# -------------------------------------------------------------------------------------------------
def _prepare_view(df_i: pd.DataFrame, df_c: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    if df_i.empty:
        return pd.DataFrame(), {}

    df_view = df_i.copy()

    # Typical CRT-I fields:
    # identity_id,name,type,zone,trust_anchor,policy_anchor,privilege_level,
    # associated_assets,notes,source_ref,mapped_control_ids
    id_col = _first_present_column(df_view, ["identity_id", "i_id", "id"])
    name_col = _first_present_column(df_view, ["name", "identity_name", "label"])
    type_col = _first_present_column(df_view, ["type", "identity_type"])
    zone_col = _first_present_column(df_view, ["zone", "identity_zone", "context_zone"])
    trust_anchor_col = _first_present_column(df_view, ["trust_anchor", "is_trust_anchor", "trust_flag"])
    policy_anchor_col = _first_present_column(df_view, ["policy_anchor", "policy_scope", "policy_domain"])
    privilege_col = _first_present_column(df_view, ["privilege_level", "priv_level", "privilege_tier"])
    assets_col = _first_present_column(df_view, ["associated_assets", "asset_scope", "linked_assets"])
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

    # Derived: is_trust_anchor flag
    if trust_anchor_col and trust_anchor_col in df_view.columns:
        def _as_bool(val: object) -> bool:
            if pd.isna(val):
                return False
            s = str(val).strip().lower()
            return s in ("yes", "true", "y", "1", "anchor")

        df_view["is_trust_anchor_flag"] = df_view[trust_anchor_col].apply(_as_bool)
    else:
        df_view["is_trust_anchor_flag"] = False

    # Derived: privileged flag (high / critical)
    if privilege_col and privilege_col in df_view.columns:
        def _is_privileged(val: object) -> bool:
            if pd.isna(val):
                return False
            s = str(val).strip().lower()
            return s in ("high", "critical")

        df_view["is_privileged_flag"] = df_view[privilege_col].apply(_is_privileged)
    else:
        df_view["is_privileged_flag"] = False

    # Optional: join CRT-C to show summary of linked control names
    if linked_controls_col and not df_c.empty and "control_id" in df_c.columns:
        df_c_lookup = df_c[["control_id", "control_name"]].copy()
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
                    label = df_c_lookup.loc[df_c_lookup["control_id"] == cid, "control_name"].iloc[0]
                names.append(f"{cid} — {label}" if label else cid)
            return "; ".join(names)

        df_view["linked_control_summary"] = df_view[linked_controls_col].apply(_resolve_controls)
    else:
        df_view["linked_control_summary"] = ""

    colmap: Dict[str, Optional[str]] = {
        "id_col": id_col,
        "name_col": name_col,
        "type_col": type_col,
        "zone_col": zone_col,
        "trust_anchor_col": trust_anchor_col,
        "policy_anchor_col": policy_anchor_col,
        "privilege_col": privilege_col,
        "assets_col": assets_col,
        "notes_col": notes_col,
        "source_ref_col": source_ref_col,
        "linked_controls_col": linked_controls_col,
    }
    return df_view, colmap


def _build_identity_label(row: pd.Series, colmap: Dict[str, Optional[str]]) -> str:
    name_col = colmap.get("name_col")
    type_col = colmap.get("type_col")
    zone_col = colmap.get("zone_col")

    parts: List[str] = []
    if name_col and name_col in row.index and pd.notna(row.get(name_col)):
        parts.append(str(row[name_col]))
    if type_col and type_col in row.index and pd.notna(row.get(type_col)):
        parts.append(f"({row[type_col]})")
    if zone_col and zone_col in row.index and pd.notna(row.get(zone_col)):
        parts.append(f"[{row[zone_col]}]")

    return " ".join(parts) if parts else "Unlabelled identity"


def _detect_id_column(df_view: pd.DataFrame) -> Optional[str]:
    return _first_present_column(df_view, ["identity_id", "i_id", "id"])


def _row_to_identity_entity(row: pd.Series, colmap: Dict[str, Optional[str]], id_col: Optional[str]) -> Dict[str, object]:
    if id_col and id_col in row.index and pd.notna(row[id_col]):
        entity_id = str(row[id_col])
    else:
        entity_id = _build_identity_label(row, colmap) or f"row-{row.name}"

    entity: Dict[str, object] = {
        "catalogue": "CRT-I",
        "id": entity_id,
        "raw": row.to_dict(),
    }

    type_col = colmap.get("type_col")
    zone_col = colmap.get("zone_col")
    privilege_col = colmap.get("privilege_col")
    trust_anchor_col = colmap.get("trust_anchor_col")

    if type_col and type_col in row.index:
        entity["identity_type"] = row[type_col]
    if zone_col and zone_col in row.index:
        entity["zone"] = row[zone_col]
    if privilege_col and privilege_col in row.index:
        entity["privilege_level"] = row[privilege_col]
    if trust_anchor_col and trust_anchor_col in row.index:
        entity["trust_anchor"] = row[trust_anchor_col]

    return entity


def _compute_coverage(df_scope: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> Dict[str, int]:
    if df_scope.empty:
        return {
            "total_identities_in_scope": 0,
            "distinct_types_in_scope": 0,
            "distinct_zones_in_scope": 0,
            "identities_with_mapped_controls_in_scope": 0,
            "trust_anchors_in_scope": 0,
            "privileged_identities_in_scope": 0,
        }

    type_col = colmap.get("type_col")
    zone_col = colmap.get("zone_col")
    linked_controls_col = colmap.get("linked_controls_col")

    total_identities = len(df_scope)
    type_count = df_scope[type_col].dropna().astype(str).nunique() if type_col and type_col in df_scope.columns else 0
    zone_count = df_scope[zone_col].dropna().astype(str).nunique() if zone_col and zone_col in df_scope.columns else 0

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

    trust_anchors = int(df_scope["is_trust_anchor_flag"].sum()) if "is_trust_anchor_flag" in df_scope.columns else 0
    privileged = int(df_scope["is_privileged_flag"].sum()) if "is_privileged_flag" in df_scope.columns else 0

    return {
        "total_identities_in_scope": int(total_identities),
        "distinct_types_in_scope": int(type_count),
        "distinct_zones_in_scope": int(zone_count),
        "identities_with_mapped_controls_in_scope": int(with_mapped_controls),
        "trust_anchors_in_scope": int(trust_anchors),
        "privileged_identities_in_scope": int(privileged),
    }


# -------------------------------------------------------------------------------------------------
# View 1 — Catalogue Overview (with inspection)
# -------------------------------------------------------------------------------------------------
def render_view_overview(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📊 Identity & Access Catalogue Overview")
    st.markdown(
        """
Use this view to scan the **structure** of your identity and access model:

- Which identity types exist (user, service, machine, vendor, delegated, etc.)
- Where identities are anchored (zones, trust anchors, policy anchors)
- How many entries have mapped CRT-C controls

Metrics shown here are **structural and descriptive only**. They do not
score maturity or provide assurance.
"""
    )

    with st.expander("ℹ️ Help & Guidance — Overview", expanded=False):
        render_markdown_file(
            HELP_VIEW_OVERVIEW_MD,
            fallback=(
                "This overview presents the effective CRT-I catalogue as a table with lightweight filters "
                "and simple descriptive metrics. Use the inspection panel to review a single identity "
                "and any recorded structural control links."
            ),
        )

    if df_view.empty:
        st.warning("No identity entries found in CRT-I. Populate CRT-I via the Command Centre.")
        return

    st.markdown("### 📈 Coverage & Metrics (structural, descriptive only)")
    coverage = _compute_coverage(df_view, colmap)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Identities / Anchors", value=coverage["total_identities_in_scope"])
    with m2:
        st.metric("Distinct Identity Types", value=coverage["distinct_types_in_scope"])
    with m3:
        st.metric("Distinct Zones / Contexts", value=coverage["distinct_zones_in_scope"])

    m4, m5, m6 = st.columns(3)
    with m4:
        st.metric("Entries with mapped controls (CRT-C)", value=coverage["identities_with_mapped_controls_in_scope"])
    with m5:
        st.metric("Trust Anchors in Scope", value=coverage["trust_anchors_in_scope"])
    with m6:
        st.metric("Privileged Identities in Scope", value=coverage["privileged_identities_in_scope"])

    with st.expander("ℹ️ Coverage & Metrics — Detail", expanded=False):
        st.markdown(
            """
These metrics summarise how many identities exist across types and zones, and where
mapped CRT-C controls, trust anchors, and privileged roles appear. They are **purely
descriptive** and do not provide scoring or assurance.
"""
        )

    st.markdown("### 🧾 All Identities & Access Anchors")

    type_col = colmap.get("type_col")
    zone_col = colmap.get("zone_col")
    privilege_col = colmap.get("privilege_col")
    notes_col = colmap.get("notes_col")
    assets_col = colmap.get("assets_col")

    filter_col, table_col = st.columns([1, 3])

    with filter_col:
        st.markdown("#### 🔎 Filters")

        type_choice = None
        zone_choice = None
        priv_choice = None

        if type_col and type_col in df_view.columns:
            types = ["(All types)"] + sorted(df_view[type_col].dropna().astype(str).unique().tolist())
            type_choice = st.selectbox("Identity Type", types)

        if zone_col and zone_col in df_view.columns:
            zones = ["(All zones)"] + sorted(df_view[zone_col].dropna().astype(str).unique().tolist())
            zone_choice = st.selectbox("Zone / Context", zones)

        if privilege_col and privilege_col in df_view.columns:
            privs = ["(All privilege levels)"] + sorted(df_view[privilege_col].dropna().astype(str).unique().tolist())
            priv_choice = st.selectbox("Privilege Level", privs)

        text_filter = st.text_input("Notes / assets contain", "")

        only_trust_anchors = st.checkbox("Only trust anchors", value=False)
        only_privileged = st.checkbox("Only privileged identities", value=False)
        only_with_controls = st.checkbox("Only entries with mapped controls (CRT-C)", value=False)

    with table_col:
        df_filtered = df_view.copy()

        if type_col and type_choice and type_choice != "(All types)":
            df_filtered = df_filtered[df_filtered[type_col].astype(str) == type_choice]

        if zone_col and zone_choice and zone_choice != "(All zones)":
            df_filtered = df_filtered[df_filtered[zone_col].astype(str) == zone_choice]

        if privilege_col and priv_choice and priv_choice != "(All privilege levels)":
            df_filtered = df_filtered[df_filtered[privilege_col].astype(str) == priv_choice]

        if text_filter:
            text_filter_lower = text_filter.lower()
            text_cols: List[str] = []
            for col in (notes_col, assets_col):
                if col and col in df_filtered.columns:
                    text_cols.append(col)

            if text_cols:
                mask = False
                for col in text_cols:
                    series = df_filtered[col].astype(str).str.lower().str.contains(text_filter_lower)
                    mask = series if isinstance(mask, bool) else (mask | series)
                if not isinstance(mask, bool):
                    df_filtered = df_filtered[mask]

        if only_trust_anchors and "is_trust_anchor_flag" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["is_trust_anchor_flag"]]

        if only_privileged and "is_privileged_flag" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["is_privileged_flag"]]

        if only_with_controls and "mapped_control_count" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["mapped_control_count"] > 0]

        if df_filtered.empty:
            st.info("No identity entries match the selected filters.")
        else:
            cols_to_hide = {
                "mapped_control_ids",
                "mapped_control_count",
                "is_trust_anchor_flag",
                "is_privileged_flag",
                "linked_control_summary",
            }
            available_cols = [c for c in df_filtered.columns if c not in cols_to_hide]

            preferred_order = [
                "identity_id",
                "name",
                "type",
                "zone",
                "trust_anchor",
                "policy_anchor",
                "privilege_level",
                "associated_assets",
            ]
            ordered = [c for c in preferred_order if c in available_cols]
            remaining = [c for c in available_cols if c not in ordered]
            display_cols = ordered + remaining

            st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("### 🧬 Inspect a Single Identity / Anchor (optional)")

    if df_filtered.empty:
        st.caption("Adjust filters above to enable per-identity inspection.")
        return

    df_filtered = df_filtered.reset_index(drop=True)
    labels = [_build_identity_label(row, colmap) for _, row in df_filtered.iterrows()]
    inspect_labels = ["(None selected)"] + labels

    selected_label = st.selectbox("Select an identity to inspect", options=inspect_labels, index=0)
    if selected_label == "(None selected)":
        st.caption("Choose an identity or anchor to see structural details and mapped controls.")
        return

    idx = labels.index(selected_label)
    identity_row = df_filtered.iloc[[idx]]

    linked_controls_col = colmap.get("linked_controls_col")
    name_col = colmap.get("name_col")
    policy_anchor_col = colmap.get("policy_anchor_col")
    trust_anchor_col = colmap.get("trust_anchor_col")

    details_col, col_controls = st.columns([2, 2])

    with details_col:
        st.markdown("#### Structural Attributes")

        if name_col and name_col in identity_row.columns:
            st.write(f"**Name:** {identity_row[name_col].iloc[0]}")
        if type_col and type_col in identity_row.columns:
            st.write(f"**Type:** {identity_row[type_col].iloc[0]}")
        if zone_col and zone_col in identity_row.columns:
            st.write(f"**Zone / Context:** {identity_row[zone_col].iloc[0]}")
        if privilege_col and privilege_col in identity_row.columns:
            st.write(f"**Privilege Level:** {identity_row[privilege_col].iloc[0]}")

        if policy_anchor_col and policy_anchor_col in identity_row.columns:
            val = identity_row[policy_anchor_col].iloc[0]
            if pd.notna(val) and str(val).strip():
                st.write(f"**Policy Anchor:** {val}")

        if trust_anchor_col and trust_anchor_col in identity_row.columns:
            st.write(f"**Trust Anchor Flag:** {identity_row[trust_anchor_col].iloc[0]}")

        if assets_col and assets_col in identity_row.columns:
            assets_val = identity_row[assets_col].iloc[0]
            if pd.notna(assets_val) and str(assets_val).strip():
                st.markdown("**Associated Assets / Surfaces**")
                st.write(str(assets_val))

        if notes_col and notes_col in identity_row.columns:
            notes_val = identity_row[notes_col].iloc[0]
            if pd.notna(notes_val) and str(notes_val).strip():
                st.markdown("**Notes**")
                st.write(str(notes_val))

    with col_controls:
        st.markdown("#### 🧱 Structural Control Links (CRT-C)")

        if linked_controls_col and linked_controls_col in identity_row.columns:
            raw_links = identity_row[linked_controls_col].iloc[0]
            summary = identity_row["linked_control_summary"].iloc[0] if "linked_control_summary" in identity_row.columns else ""
            if pd.isna(raw_links) or not str(raw_links).strip():
                st.caption("No mapped CRT-C controls recorded for this identity.")
            else:
                st.markdown("**Mapped controls (CRT-C IDs)**")
                st.code(str(raw_links), language="text")

                if isinstance(summary, str) and summary.strip():
                    st.markdown("**Resolved Control Summary**")
                    st.write(summary)
                else:
                    st.caption("No control names resolved; check `CRT-C.csv` for matching IDs.")
        else:
            st.caption("No `mapped_control_ids` / `linked_controls` column present in the identity catalogue.")


# -------------------------------------------------------------------------------------------------
# View 2 — Optional Identity Scope for Tasks (export-only)
# -------------------------------------------------------------------------------------------------
def render_view_context_bundles(df_view: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> None:
    st.header("📦 Optional Identity Scope for Tasks")

    st.markdown(
        """
Most users can **skip this step** and go straight to **🎛 Programmes — Task Builder**.

Use this page only if you want downstream tasks or AI-assisted exploration to focus on a
**specific patch of your identity and access landscape** (for example: break-glass admin
accounts in production zones).

Whatever you choose here:

- It does **not** edit CRT-I or configure controls
- You will see the bundle JSON before exporting it
- Lens maintenance and attachment happens in 🧠 AI Observation Console
"""
    )

    with st.expander("ℹ️ Help & Guidance — Identity Scope", expanded=False):
        render_markdown_file(
            HELP_VIEW_SCOPE_MD,
            fallback=(
                "Define a focused identity scope when you want exports (or downstream modules) "
                "to reference a subset of CRT-I. This is structural only and export-only."
            ),
        )

    if df_view.empty:
        st.warning("No identity entries available — cannot build a context bundle.")
        return

    id_col = _detect_id_column(df_view)

    type_col = colmap.get("type_col")
    zone_col = colmap.get("zone_col")
    privilege_col = colmap.get("privilege_col")
    notes_col = colmap.get("notes_col")

    st.markdown("### 0️⃣ How should identities be handled for this session?")

    scope_activation = st.radio(
        "Choose how to handle identities for this scope export:",
        [
            "Don’t define a special identity scope (use everything)",
            "Define a focused identity scope (optional)",
        ],
        index=0,
        help="If you’re not sure, use the default and come back later.",
    )

    if scope_activation.startswith("Don’t define"):
        st.info(
            "No focused identity scope will be built in this view. "
            "You can return later to export a focused scope if needed."
        )
        return

    st.markdown("### 1️⃣ Choose Scope Mode")

    scope_mode = st.radio(
        "Scope mode",
        [
            "Single identity",
            "Multi-identity cluster",
            "Segment (filters)",
        ],
        help="Single = one primary identity. Cluster = small set. Segment = filter-defined scope.",
    )

    scope_df = pd.DataFrame()
    primary_entity: Dict[str, object] = {}
    filters: Dict[str, object] = {}

    st.markdown("### 2️⃣ Select Identity Scope")

    # ---------------------------------------------------------------------
    # Single identity
    # ---------------------------------------------------------------------
    if scope_mode == "Single identity":
        fcol, tcol = st.columns([1, 2])

        with fcol:
            type_choice = None
            zone_choice = None
            priv_choice = None

            if type_col and type_col in df_view.columns:
                types = ["(Any type)"] + sorted(df_view[type_col].dropna().astype(str).unique().tolist())
                type_choice = st.selectbox("Identity Type", types)

            if zone_col and zone_col in df_view.columns:
                zones = ["(Any zone)"] + sorted(df_view[zone_col].dropna().astype(str).unique().tolist())
                zone_choice = st.selectbox("Zone / Context", zones)

            if privilege_col and privilege_col in df_view.columns:
                privs = ["(Any privilege level)"] + sorted(df_view[privilege_col].dropna().astype(str).unique().tolist())
                priv_choice = st.selectbox("Privilege Level", privs)

            text_filter = st.text_input("Notes contain", "")

        with tcol:
            df_filtered = df_view.copy()

            if type_col and type_choice and type_choice != "(Any type)":
                df_filtered = df_filtered[df_filtered[type_col].astype(str) == type_choice]
            if zone_col and zone_choice and zone_choice != "(Any zone)":
                df_filtered = df_filtered[df_filtered[zone_col].astype(str) == zone_choice]
            if privilege_col and priv_choice and priv_choice != "(Any privilege level)":
                df_filtered = df_filtered[df_filtered[privilege_col].astype(str) == priv_choice]

            if text_filter and notes_col and notes_col in df_filtered.columns:
                tf = text_filter.lower()
                df_filtered = df_filtered[df_filtered[notes_col].astype(str).str.lower().str.contains(tf)]

            if df_filtered.empty:
                st.info("No identities match the selected filters.")
                st.stop()

            st.markdown("#### Matching Identities")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_identity_label(row, colmap) for _, row in df_filtered.iterrows()]
        selected_label = st.selectbox("Identity / anchor to use as primary entity", options=labels)
        idx = labels.index(selected_label)

        scope_df = df_filtered.iloc[[idx]]
        row = scope_df.iloc[0]
        primary_id = str(row[id_col]) if id_col and id_col in row.index and pd.notna(row[id_col]) else (_build_identity_label(row, colmap) or f"row-{row.name}")
        primary_entity = {"type": "identity", "id": primary_id}

    # ---------------------------------------------------------------------
    # Multi-identity cluster
    # ---------------------------------------------------------------------
    elif scope_mode == "Multi-identity cluster":
        fcol, tcol = st.columns([1, 2])

        with fcol:
            type_choice = None
            zone_choice = None
            priv_choice = None

            if type_col and type_col in df_view.columns:
                types = ["(Any type)"] + sorted(df_view[type_col].dropna().astype(str).unique().tolist())
                type_choice = st.selectbox("Identity Type", types)

            if zone_col and zone_col in df_view.columns:
                zones = ["(Any zone)"] + sorted(df_view[zone_col].dropna().astype(str).unique().tolist())
                zone_choice = st.selectbox("Zone / Context", zones)

            if privilege_col and privilege_col in df_view.columns:
                privs = ["(Any privilege level)"] + sorted(df_view[privilege_col].dropna().astype(str).unique().tolist())
                priv_choice = st.selectbox("Privilege Level", privs)

        with tcol:
            df_filtered = df_view.copy()

            if type_col and type_choice and type_choice != "(Any type)":
                df_filtered = df_filtered[df_filtered[type_col].astype(str) == type_choice]
            if zone_col and zone_choice and zone_choice != "(Any zone)":
                df_filtered = df_filtered[df_filtered[zone_col].astype(str) == zone_choice]
            if privilege_col and priv_choice and priv_choice != "(Any privilege level)":
                df_filtered = df_filtered[df_filtered[privilege_col].astype(str) == priv_choice]

            if df_filtered.empty:
                st.info("No identities match the selected filters.")
                st.stop()

            st.markdown("#### Available Identities for Cluster")
            st.dataframe(df_filtered, width="stretch", hide_index=True)

        df_filtered = df_filtered.reset_index(drop=True)
        labels = [_build_identity_label(row, colmap) for _, row in df_filtered.iterrows()]

        cluster_labels = st.multiselect(
            "Select identities to include in the cluster",
            options=labels,
        )

        if not cluster_labels:
            st.info("Select at least one identity to form a cluster.")
            st.stop()

        indices = [labels.index(lbl) for lbl in cluster_labels]
        scope_df = df_filtered.iloc[indices]

        base_ids: List[str] = []
        for _, row in scope_df.iterrows():
            if id_col and id_col in row.index and pd.notna(row[id_col]):
                base_ids.append(str(row[id_col]))
            else:
                base_ids.append(_build_identity_label(row, colmap) or f"row-{row.name}")

        cluster_key = ",".join(sorted(base_ids))
        cluster_id = f"CRT-I-cluster-{hashlib.sha256(cluster_key.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "identity_cluster", "id": cluster_id}

    # ---------------------------------------------------------------------
    # Segment (filters)
    # ---------------------------------------------------------------------
    else:
        st.markdown("#### Define Segment Filters")

        type_choice = None
        zone_choice = None
        priv_choice = None

        if type_col and type_col in df_view.columns:
            types = ["(Any type)"] + sorted(df_view[type_col].dropna().astype(str).unique().tolist())
            type_choice = st.selectbox("Identity Type", types)

        if zone_col and zone_col in df_view.columns:
            zones = ["(Any zone)"] + sorted(df_view[zone_col].dropna().astype(str).unique().tolist())
            zone_choice = st.selectbox("Zone / Context", zones)

        if privilege_col and privilege_col in df_view.columns:
            privs = ["(Any privilege level)"] + sorted(df_view[privilege_col].dropna().astype(str).unique().tolist())
            priv_choice = st.selectbox("Privilege Level", privs)

        scope_df = df_view.copy()

        if type_col and type_choice and type_choice != "(Any type)":
            scope_df = scope_df[scope_df[type_col].astype(str) == type_choice]
            filters["identity_type"] = type_choice

        if zone_col and zone_choice and zone_choice != "(Any zone)":
            scope_df = scope_df[scope_df[zone_col].astype(str) == zone_choice]
            filters["zone"] = zone_choice

        if privilege_col and priv_choice and priv_choice != "(Any privilege level)":
            scope_df = scope_df[scope_df[privilege_col].astype(str) == priv_choice]
            filters["privilege_level"] = priv_choice

        st.markdown("#### Segment Preview")
        if scope_df.empty:
            st.info("No identities match this segment definition. The bundle will have an empty identities list.")
        else:
            st.dataframe(scope_df, width="stretch", hide_index=True)

        filter_str = json.dumps(filters, sort_keys=True) if filters else "all"
        segment_id = f"CRT-I-segment-{hashlib.sha256(filter_str.encode('utf-8')).hexdigest()[:8]}"
        primary_entity = {"type": "identity_segment", "id": segment_id, "filters": filters}

    if scope_df is None or primary_entity == {}:
        st.warning("Unable to determine scope or primary entity — please review selections.")
        return

    st.markdown("### 3️⃣ Bundle Summary")

    coverage = _compute_coverage(scope_df, colmap)
    st.write(
        f"- **Scope mode:** `{scope_mode}`  \n"
        f"- **Identities in scope:** `{coverage['total_identities_in_scope']}`  \n"
        f"- **Primary entity:** `{primary_entity.get('type')}` → `{primary_entity.get('id')}`"
    )

    identity_entities = [_row_to_identity_entity(row, colmap, id_col) for _, row in scope_df.iterrows()]

    bundle: Dict[str, Any] = {
        "bundle_type": "identity",
        "module": "🔐 Identity & Access Lens",
        "primary_entity": primary_entity,
        "entities": {
            "assets": [],
            "identities": identity_entities,
            "data_domains": [],
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
            "identity_paths": [],
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
            file_name="ial_identity_bundle.json",
            mime="application/json",
            use_container_width=True,
        )

    with b:
        if st.button("💾 Save to lens shelf", use_container_width=True):
            _ensure_dir(IAL_LENS_SHELF_DIR)

            pe = primary_entity if isinstance(primary_entity, dict) else {}
            pe_id = pe.get("id") if isinstance(pe, dict) else None

            name_hint = _safe_filename(str(pe_id)) if pe_id else "ial-scope"
            filename = f"ial_{name_hint}_{_utc_stamp()}.json"
            path = os.path.join(IAL_LENS_SHELF_DIR, filename)

            bundle["lens_meta"]["persisted_to_disk"] = True
            bundle["lens_meta"]["shelf_path_hint"] = f"lenses/ial/bundles/{filename}"

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
    page_title="Identity & Access Lens",
    page_icon="🔐",
    layout="wide",
)

st.title("🔐 Identity & Access Lens")
st.caption(
    "Explore identities, privilege tiers, and trust anchors — "
    "read-only structural view of your CRT-I identity and access model."
)

with st.expander("📖 What is this app about?"):
    render_markdown_file(
        ABOUT_APP_MD,
        fallback=(
            "# 🔐 Identity & Access Lens\n\n"
            "This module surfaces the **effective CRT-I catalogue** in a structured, "
            "non-prescriptive way.\n\n"
            "- Explore identity types, zones, and trust anchors\n"
            "- Inspect privilege tiers and policy anchors\n"
            "- View structural links to CRT-C controls (where defined)\n"
            "- Export a normalised `bundle_type = \"identity\"` context bundle\n\n"
            "It does **not** configure controls, score maturity, or provide assurance."
        ),
    )

# -------------------------------------------------------------------------------------------------
# Load Catalogues
# -------------------------------------------------------------------------------------------------
CATALOGUES = _load_crt_catalogues()
DF_I = CATALOGUES.get("CRT-I", pd.DataFrame())
DF_C = CATALOGUES.get("CRT-C", pd.DataFrame())
DF_VIEW, COLMAP = _prepare_view(DF_I, DF_C)

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
st.sidebar.caption("Use the view selector below to switch between perspectives within the Identity & Access Lens.")

st.sidebar.info(
    """
**🔐 Identity & Access Lens**

Use this module to:

- Examine how identities and access anchors are defined
- See where trust anchors and privilege tiers sit across zones
- Inspect structural links to CRT-C controls (where recorded)
- Export a normalised `bundle_type = "identity"` context bundle

All views are read-only. Catalogue updates and append operations are handled
exclusively via the 📂 Structural Controls & Frameworks — Command Centre and
🛰 Org-Specific Catalogues.
"""
)

st.sidebar.subheader("🗂️ View Options")
view_mode = st.sidebar.radio(
    "Choose a view",
    ["📊 Catalogue Overview", "📦 Optional Identity Scope for Tasks"],
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
elif view_mode == "📦 Optional Identity Scope for Tasks":
    render_view_context_bundles(DF_VIEW, COLMAP)
else:
    st.warning("Unknown view selected. Please choose an option from the sidebar.")

# -------------------------------------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------------------------------------
crt_footer()
