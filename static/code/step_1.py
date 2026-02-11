import re
import pandas as pd
from pathlib import Path


def _clean_col(s):
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _dedupe_columns(cols):
    seen = {}
    out = []
    for c in cols:
        base = _clean_col(c)
        if base == "":
            base = "Unnamed"
        if base not in seen:
            seen[base] = 0
            out.append(base)
        else:
            seen[base] += 1
            out.append(f"{base}__{seen[base]}")
    return out


def _looks_like_default_numeric_headers(columns):
    cols = [_clean_col(c) for c in columns]
    if len(cols) == 0:
        return True
    numeric_like = 0
    empty_like = 0
    for c in cols:
        if c == "" or c.lower().startswith("unnamed"):
            empty_like += 1
            continue
        if re.fullmatch(r"[-+]?\d+(\.\d+)?", c):
            numeric_like += 1
    return (numeric_like + empty_like) / max(1, len(cols)) > 0.5


def _find_required_cols(df_cols, required):
    colset = set(df_cols)
    missing = [c for c in required if c not in colset]
    return missing


def _build_datetime_utc(df, year_col, month_col, day_col, time_col):
    y = pd.to_numeric(df[year_col], errors="coerce")
    m = pd.to_numeric(df[month_col], errors="coerce")
    d = pd.to_numeric(df[day_col], errors="coerce")
    hh = pd.to_numeric(df[time_col], errors="coerce")

    dt = pd.to_datetime(
        {"year": y, "month": m, "day": d, "hour": hh},
        errors="coerce",
        utc=True,
    )

    out = df.copy()
    out["datetime_utc"] = dt
    out = out.dropna(subset=["datetime_utc"]).reset_index(drop=True)

    if not pd.api.types.is_datetime64_any_dtype(out["datetime_utc"]):
        raise RuntimeError("datetime_utc is not datetime dtype after parsing")

    return out


def _make_excel_safe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        s = out[c]
        if pd.api.types.is_datetime64tz_dtype(s):
            out[c] = s.dt.tz_convert(None)
    return out


def main():
    header_path = Path(r"E:\sci-data-copilot\xlsx\head.xls")
    data_path = Path(r"E:\sci-data-copilot\xlsx\2005-2006.xls")
    save_dir = Path(r"E:\sci-data-copilot\exp\jidi_exp_20260209_175516")
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading header file: {header_path}")
    header_df = pd.read_excel(str(header_path), engine="calamine", header=0)
    canonical_cols = _dedupe_columns([_clean_col(c) for c in header_df.columns.tolist()])
    if not canonical_cols:
        raise RuntimeError("Header file has no columns")

    print(f"Canonical columns detected: {len(canonical_cols)}")
    print("First 10 canonical columns:", canonical_cols[:10])

    print(f"Loading data file: {data_path}")
    data_df_try = pd.read_excel(str(data_path), engine="calamine", header=0)

    reload_no_header = False
    if data_df_try.shape[1] != len(canonical_cols):
        print(
            f"Column count mismatch with header=0 (data={data_df_try.shape[1]} vs header={len(canonical_cols)}). "
            "Will reload with header=None."
        )
        reload_no_header = True
    elif _looks_like_default_numeric_headers(list(data_df_try.columns)):
        print("Data columns look non-semantic (numeric/Unnamed). Will reload with header=None.")
        reload_no_header = True

    if reload_no_header:
        data_df = pd.read_excel(str(data_path), engine="calamine", header=None)
        print(f"Reloaded data with header=None. Shape: {data_df.shape[0]} rows x {data_df.shape[1]} cols")
        if data_df.shape[1] != len(canonical_cols):
            raise RuntimeError(
                f"After reloading with header=None, column count still mismatched: "
                f"data has {data_df.shape[1]} cols, header defines {len(canonical_cols)} cols"
            )
        data_df.columns = canonical_cols
    else:
        data_df = data_df_try.copy()
        if data_df.shape[1] != len(canonical_cols):
            raise RuntimeError(
                f"Column count mismatch: data has {data_df.shape[1]} cols, header defines {len(canonical_cols)} cols"
            )
        data_df.columns = canonical_cols

    data_df.columns = _dedupe_columns(data_df.columns.tolist())
    print(f"Data loaded. Rows: {len(data_df)}, Cols: {data_df.shape[1]}")

    year_col = "Year"
    month_col = "Month"
    day_col = "Day"
    time_col = "Three-hourly observation time(UTC)"
    missing_req = _find_required_cols(data_df.columns, [year_col, month_col, day_col, time_col])
    if missing_req:
        raise RuntimeError(f"Missing required datetime fields in merged dataset: {missing_req}")

    print("Building datetime_utc from Year/Month/Day + Three-hourly observation time(UTC)")
    data_df = _build_datetime_utc(data_df, year_col, month_col, day_col, time_col)
    print(f"Rows after dropping invalid datetime: {len(data_df)}")
    if len(data_df) == 0:
        raise RuntimeError("No valid rows remain after datetime parsing")

    normalized_path = save_dir / "normalized_merged.xlsx"
    print(f"Saving normalized merged dataset: {normalized_path}")
    _make_excel_safe(data_df).to_excel(str(normalized_path), index=False, engine="openpyxl")

    print("Preparing for daily averaging")
    df = data_df.copy()
    df["date_utc"] = df["datetime_utc"].dt.floor("D")

    exclude_from_avg = {
        year_col,
        month_col,
        day_col,
        time_col,
    }

    numeric_df = df.apply(lambda s: pd.to_numeric(s, errors="coerce") if s.name not in ["datetime_utc", "date_utc"] else s)
    numeric_cols = []
    for c in numeric_df.columns:
        if c in exclude_from_avg or c in ["datetime_utc", "date_utc"]:
            continue
        if pd.api.types.is_numeric_dtype(numeric_df[c]):
            if numeric_df[c].notna().any():
                numeric_cols.append(c)

    if not numeric_cols:
        raise RuntimeError("No numeric measurement columns found for daily averaging")

    print(f"Numeric measurement columns to average: {len(numeric_cols)}")
    print("First 10 measurement columns:", numeric_cols[:10])

    daily_avg = numeric_df.groupby("date_utc", as_index=False)[numeric_cols].mean(numeric_only=True)
    if not pd.api.types.is_datetime64_any_dtype(daily_avg["date_utc"]):
        raise RuntimeError("date_utc is not datetime dtype in daily_avg result")

    daily_path = save_dir / "daily_averaged.xlsx"
    print(f"Saving daily-averaged dataset: {daily_path} (rows={len(daily_avg)})")
    _make_excel_safe(daily_avg).to_excel(str(daily_path), index=False, engine="openpyxl")

    print("Splitting daily-averaged dataset by month and saving monthly files")
    daily_avg["year"] = daily_avg["date_utc"].dt.year
    daily_avg["month"] = daily_avg["date_utc"].dt.month

    written = 0
    for (yy, mm), g in daily_avg.groupby(["year", "month"], dropna=False):
        if pd.isna(yy) or pd.isna(mm):
            raise RuntimeError("Found NA year/month during monthly split")
        yy = int(yy)
        mm = int(mm)

        out_dir = save_dir / f"{yy:04d}" / f"{mm:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = out_dir / f"daily_averaged_{yy:04d}-{mm:02d}.xlsx"
        g_out = g.drop(columns=["year", "month"]).sort_values("date_utc").reset_index(drop=True)

        print(f"Writing: {out_path} (rows={len(g_out)})")
        _make_excel_safe(g_out).to_excel(str(out_path), index=False, engine="openpyxl")
        written += 1

    if written == 0:
        raise RuntimeError("No monthly files were written")

    print(f"Processing completed successfully. Monthly files written: {written}")


if __name__ == "__main__":
    main()