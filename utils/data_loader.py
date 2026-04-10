"""
Unified data loader — queries BigQuery live with CSV fallback.
All modules use this instead of reading CSVs directly.
"""

import pandas as pd
import streamlit as st
from pathlib import Path

GCP_PROJECT = "gen-lang-client-0205243793"
BQ_DATASET = "streamshield"
DATA_DIR = Path(__file__).parent.parent / "data" / "cached"
PIPELINE_DIR = DATA_DIR / "pipelines"


def _get_credentials():
    """Get GCP credentials from st.secrets (Streamlit Cloud) or ADC (local)."""
    try:
        import streamlit as _st
        if "gcp_service_account" in _st.secrets:
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(
                dict(_st.secrets["gcp_service_account"])
            )
    except Exception:
        pass
    return None  # Falls back to ADC


def _get_bq_client():
    """Get BigQuery client, return None if unavailable."""
    try:
        from google.cloud import bigquery
        creds = _get_credentials()
        if creds:
            return bigquery.Client(project=GCP_PROJECT, credentials=creds)
        return bigquery.Client(project=GCP_PROJECT)
    except Exception:
        return None


def _query_bq(query, parse_dates=None):
    """Run a BigQuery query, return DataFrame or None."""
    client = _get_bq_client()
    if client is None:
        return None
    try:
        df = client.query(query).to_dataframe()
        if parse_dates:
            for col in parse_dates:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
        return df
    except Exception:
        return None


@st.cache_data(ttl=300)
def load_streaming_events():
    """Load streaming events — BigQuery first, CSV fallback."""
    df = _query_bq(
        f"SELECT * FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events`",
        parse_dates=["timestamp"],
    )
    if df is not None:
        return df, "bigquery"
    return pd.read_csv(DATA_DIR / "streaming_events.csv", parse_dates=["timestamp"]), "csv"


@st.cache_data(ttl=300)
def load_analyst_reviews():
    df = _query_bq(
        f"SELECT * FROM `{GCP_PROJECT}.{BQ_DATASET}.analyst_reviews`",
        parse_dates=["review_date"],
    )
    if df is not None:
        return df, "bigquery"
    return pd.read_csv(DATA_DIR / "analyst_reviews.csv", parse_dates=["review_date"]), "csv"


@st.cache_data(ttl=300)
def load_model_performance():
    df = _query_bq(
        f"SELECT * FROM `{GCP_PROJECT}.{BQ_DATASET}.model_performance` ORDER BY date",
        parse_dates=["date"],
    )
    if df is not None:
        return df, "bigquery"
    return pd.read_csv(DATA_DIR / "model_performance.csv", parse_dates=["date"]), "csv"


@st.cache_data(ttl=300)
def load_appeal_cases():
    df = _query_bq(
        f"SELECT * FROM `{GCP_PROJECT}.{BQ_DATASET}.appeal_cases`",
        parse_dates=["appeal_date", "resolution_date"],
    )
    if df is not None:
        return df, "bigquery"
    return pd.read_csv(DATA_DIR / "appeal_cases.csv", parse_dates=["appeal_date", "resolution_date"]), "csv"


def _empty_honkify_df():
    """Empty DataFrame with the canonical honkify_live_events schema."""
    return pd.DataFrame(columns=[
        "event_id", "timestamp", "user_id", "user_type", "track_id", "track_name",
        "artist_name", "duration_ms", "device_type", "country", "ip_hash",
        "vpn_detected", "skip_rate", "account_age_days", "fraud_score",
        "classification", "source",
    ])


HONKIFY_TABLE = f"{GCP_PROJECT}.{BQ_DATASET}.honkify_live_events"


@st.cache_data(ttl=60)
def load_honkify_live_events(hours_back=24, limit=500):
    """Load recent Honkify-published events via tabledata.list (list_rows).

    Uses the tabledata.list API instead of jobs.query for ~10x lower latency
    (~500ms warm vs ~5s for SQL queries). Time filtering is done in pandas
    after the fetch since list_rows does not support WHERE clauses.

    Returns (df, source) where source is one of:
      - "bigquery"        : table reachable AND has rows in window
      - "bigquery_empty"  : table reachable, zero rows in window
      - "unavailable"     : BigQuery unreachable / fetch failed
    """
    client = _get_bq_client()
    if client is None:
        return _empty_honkify_df(), "unavailable"
    try:
        rows = client.list_rows(HONKIFY_TABLE, max_results=int(limit))
        df = rows.to_dataframe()
        if len(df) == 0:
            return _empty_honkify_df(), "bigquery_empty"
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours_back)
        df = df[df["timestamp"] >= cutoff].sort_values("timestamp", ascending=False)
        if len(df) == 0:
            return _empty_honkify_df(), "bigquery_empty"
        return df, "bigquery"
    except Exception:
        return _empty_honkify_df(), "unavailable"


def warmup_honkify_table():
    """Fire-and-forget warmup to defeat cold-start latency on first demo click.

    Pre-warms the auth tokens and tabledata.list connection that the live
    Honkify loader and the verify-readback both depend on.
    """
    try:
        client = _get_bq_client()
        if client is not None:
            list(client.list_rows(HONKIFY_TABLE, max_results=1))
    except Exception:
        pass


@st.cache_data(ttl=300)
def load_pipeline_data():
    """Load all pipeline CSVs into a dict."""
    data = {}
    if PIPELINE_DIR.exists():
        for f in PIPELINE_DIR.glob("*.csv"):
            data[f.stem] = pd.read_csv(f)
    return data


def get_data_source_badge(source):
    """Return an HTML badge indicating data source."""
    if source == "bigquery":
        return '<span style="background:rgba(29,185,84,0.2); color:#1DB954; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:600;">LIVE BigQuery</span>'
    return '<span style="background:rgba(83,83,83,0.3); color:#B3B3B3; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:600;">Local CSV</span>'
