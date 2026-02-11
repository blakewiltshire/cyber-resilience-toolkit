# =================================================================================================
# core/catalogue_json_views.py
# -------------------------------------------------------------------------------------------------
# CRT Catalogue JSON Views (CSV → JSON projection)
#
# Locked principles:
# - CSV is authoritative. JSON is derived and regenerable.
# - JSON view format = { "meta": {...}, "records": [...] }
# - Drop Excel artefact columns: any column starting with "Unnamed:"
# - Drop fully empty columns (all values empty/"")
# - Robust CSV read: utf-8 / utf-8-sig / latin1 + last-resort decode
#
# Output directory:
#   apps/data_sources/crt_catalogues/json/
# Output files:
#   CRT-AS.json, CRT-C.json, ...
# -------------------------------------------------------------------------------------------------
# pylint: disable=import-error
# =================================================================================================

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd


# Canonical catalogue set (explicit, stable)
CRT_BACKBONE: Tuple[str, ...] = ("CRT-G", "CRT-C", "CRT-F", "CRT-N")
CRT_GOV_ORG: Tuple[str, ...] = ("CRT-REQ", "CRT-LR")
CRT_STRUCT_LENSES: Tuple[str, ...] = ("CRT-AS", "CRT-D", "CRT-I", "CRT-SC", "CRT-T")
CRT_POLICY_STD: Tuple[str, ...] = ("CRT-POL", "CRT-STD")

ALL_CRT_CATALOGUES: Tuple[str, ...] = (
    *CRT_BACKBONE,
    *CRT_GOV_ORG,
    *CRT_STRUCT_LENSES,
    *CRT_POLICY_STD,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _mtime_utc_iso(path: str) -> str:
    try:
        ts = os.path.getmtime(path)
    except OSError:
        ts = 0.0
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _csv_path(crt_catalogue_dir: str, catalogue_key: str) -> str:
    return os.path.join(crt_catalogue_dir, f"{catalogue_key}.csv")


def _json_dir(crt_catalogue_dir: str) -> str:
    return os.path.join(crt_catalogue_dir, "json")


def _json_view_path(crt_catalogue_dir: str, catalogue_key: str) -> str:
    return os.path.join(_json_dir(crt_catalogue_dir), f"{catalogue_key}.json")


def _is_effectively_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    s = str(v).strip()
    return s == ""


def _drop_excel_artefact_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)
    drop_cols = [c for c in cols if str(c).strip().startswith("Unnamed:")]
    if drop_cols:
        df = df.drop(columns=drop_cols, errors="ignore")
    return df


def _drop_fully_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Treat NaN as empty string first
    df2 = df.fillna("")
    keep_cols: List[str] = []
    for c in df2.columns:
        series = df2[c]
        # keep if any cell is non-empty
        if any(not _is_effectively_empty(x) for x in series.tolist()):
            keep_cols.append(c)
    return df2[keep_cols] if keep_cols else df2


def read_csv_with_fallback_df(path: str) -> pd.DataFrame:
    """
    Read CSV robustly:
    - try utf-8, utf-8-sig, latin1
    - final fallback: decode bytes as utf-8 with replacement
    """
    if not os.path.isfile(path):
        return pd.DataFrame()

    encodings = ("utf-8", "utf-8-sig", "latin1")
    last_error: Optional[Exception] = None

    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except Exception as exc:
            last_error = exc
            continue

    # Final fallback
    try:
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        return pd.read_csv(StringIO(text))
    except Exception:
        # Fail closed (no crash)
        return pd.DataFrame()


def is_json_view_stale(crt_catalogue_dir: str, catalogue_key: str) -> bool:
    csv_path = _csv_path(crt_catalogue_dir, catalogue_key)
    json_path = _json_view_path(crt_catalogue_dir, catalogue_key)

    if not os.path.isfile(csv_path):
        return False
    if not os.path.isfile(json_path):
        return True

    try:
        return os.path.getmtime(json_path) < os.path.getmtime(csv_path)
    except OSError:
        return True


def ensure_catalogue_json_view(
    crt_catalogue_dir: str,
    catalogue_key: str,
    *,
    force: bool = False,
) -> Optional[str]:
    """
    Ensure a single catalogue JSON view exists and is up-to-date.
    Returns JSON path or None if the CSV does not exist.
    """
    csv_path = _csv_path(crt_catalogue_dir, catalogue_key)
    if not os.path.isfile(csv_path):
        return None

    json_path = _json_view_path(crt_catalogue_dir, catalogue_key)
    if not force and not is_json_view_stale(crt_catalogue_dir, catalogue_key):
        return json_path

    _ensure_dir(_json_dir(crt_catalogue_dir))

    df = read_csv_with_fallback_df(csv_path)
    if df.empty:
        payload: Dict[str, Any] = {
            "meta": {
                "catalogue": catalogue_key,
                "generated_at_utc": _utc_now_iso(),
                "source_csv": os.path.basename(csv_path),
                "source_csv_mtime_utc": _mtime_utc_iso(csv_path),
                "row_count": 0,
                "columns": [],
                "notes": "CSV unreadable or empty.",
            },
            "records": [],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        return json_path

    df = _drop_excel_artefact_columns(df)
    df = _drop_fully_empty_columns(df)

    # Normalise NaN → "" (already done in drop_fully_empty_columns, but keep deterministic)
    df = df.fillna("")

    records: List[Dict[str, Any]] = df.to_dict(orient="records")  # type: ignore[assignment]
    cols = [str(c) for c in df.columns.tolist()]

    payload = {
        "meta": {
            "catalogue": catalogue_key,
            "generated_at_utc": _utc_now_iso(),
            "source_csv": os.path.basename(csv_path),
            "source_csv_mtime_utc": _mtime_utc_iso(csv_path),
            "row_count": len(records),
            "columns": cols,
        },
        "records": records,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)

    return json_path


def ensure_all_catalogue_json_views(
    crt_catalogue_dir: str,
    *,
    force: bool = False,
    catalogue_keys: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """
    Ensure JSON views for all CRT catalogues (or a subset) exist and are up-to-date.
    Returns mapping: catalogue_key -> json_path (only for those with existing CSVs).
    """
    keys = list(catalogue_keys) if catalogue_keys else list(ALL_CRT_CATALOGUES)
    out: Dict[str, str] = {}
    for k in keys:
        p = ensure_catalogue_json_view(crt_catalogue_dir, k, force=force)
        if p:
            out[k] = p
    return out


def load_catalogue_json_view(crt_catalogue_dir: str, catalogue_key: str) -> Dict[str, Any]:
    """
    Load JSON view (ensuring it exists first). Returns {} if missing/unreadable.
    """
    p = ensure_catalogue_json_view(crt_catalogue_dir, catalogue_key, force=False)
    if not p or not os.path.isfile(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
