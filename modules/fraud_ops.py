"""Fraud Operations — 1st Line of Defense team view.

Two tabs: 'Before Controls' (current state) and 'After Controls' (post-recommendation state).
Both tabs read from the same live `honkify_live_events` BigQuery table — the framing
changes, the data does not. The After tab Signal Confirmation Card writes dispositions
into `st.session_state['fraud_ops_dispositions']`, which the Internal Audit page reads
to compute the T3 (Signal Card Enforcement) and T4 (LLM Output Quality) controls live.
"""

import hashlib
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_honkify_live_events
from utils.style import (
    COLOR_DANGER, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING,
    SPOTIFY_CARD_BG, SPOTIFY_GRAY, SPOTIFY_GREEN, SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE, apply_spotify_style, story_nav, story_next,
)
from modules.signal_card_demo import render_signal_card_widget


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _init_session_state():
    if "fraud_ops_dispositions" not in st.session_state:
        st.session_state["fraud_ops_dispositions"] = []
    if "fraud_ops_active_case" not in st.session_state:
        st.session_state["fraud_ops_active_case"] = None


def _ensure_review_zone(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return df
    return df[df["classification"] == "review"].copy()


def _queue_age_minutes(review_df: pd.DataFrame) -> float:
    if review_df is None or len(review_df) == 0:
        return 0.0
    oldest = pd.to_datetime(review_df["timestamp"]).min()
    now = pd.Timestamp.now(tz=oldest.tz) if oldest.tzinfo else pd.Timestamp.utcnow()
    return max(0.0, (now - oldest).total_seconds() / 60.0)


def _top3_signals_for_row(row: pd.Series) -> list:
    """Deterministic synthetic 'top 3 contributing signals' for a Honkify event row.

    This is NOT a real SHAP computation — it's a demo proxy. The selected chips
    are derived from the row's actual values so the chips are honest about
    what's suspicious in this specific row. Hashing the event_id is used only
    to break ties deterministically.
    """
    candidates = []
    if bool(row.get("vpn_detected", False)):
        candidates.append(("VPN detected", COLOR_DANGER))
    if int(row.get("account_age_days", 999)) < 60:
        candidates.append(("New account", COLOR_WARNING))
    if float(row.get("skip_rate", 1.0)) < 0.05:
        candidates.append(("Bot-like skip rate", COLOR_DANGER))
    if int(row.get("duration_ms", 0)) < 35000:
        candidates.append(("Short play (<35s)", COLOR_WARNING))
    if str(row.get("country", "")) in {"RU", "CN", "VN", "TR", "PK"}:
        candidates.append(("High-risk geo", COLOR_DANGER))
    if str(row.get("device_type", "")) == "web_player":
        candidates.append(("Web-player only", COLOR_WARNING))
    if float(row.get("fraud_score", 0.0)) > 0.85:
        candidates.append(("High model score", COLOR_DANGER))

    if not candidates:
        candidates = [
            ("Borderline score", COLOR_WARNING),
            ("Limited history", COLOR_INFO),
            ("Mixed signals", COLOR_INFO),
        ]

    h = hashlib.md5(str(row.get("event_id", "")).encode()).hexdigest()
    seed = int(h[:8], 16)
    candidates_sorted = sorted(candidates, key=lambda c: (h[len(c[0]) % 8], c[0]))
    return candidates_sorted[:3]


def _row_to_signal_card_case(row: pd.Series) -> dict:
    """Convert a Honkify event row into a case dict the Signal Card widget understands."""
    vpn = bool(row.get("vpn_detected", False))
    age = int(row.get("account_age_days", 0))
    duration_s = int(row.get("duration_ms", 0)) / 1000.0
    skip = float(row.get("skip_rate", 0.0))
    country = str(row.get("country", "??"))
    device = str(row.get("device_type", "??"))
    score = float(row.get("fraud_score", 0.0))

    high_risk_geo = country in {"RU", "CN", "VN", "TR", "PK"}

    signals = {
        "Account age": {"value": f"{age} days", "fraud_ground_truth": age < 30},
        "Devices used": {"value": device, "fraud_ground_truth": device == "web_player"},
        "Avg play duration": {"value": f"{duration_s:.0f} sec", "fraud_ground_truth": duration_s < 35},
        "Unique tracks/day": {"value": "—", "fraud_ground_truth": False},
        "Skip rate": {"value": f"{skip * 100:.0f}%", "fraud_ground_truth": skip < 0.05},
        "VPN detected": {"value": "Yes" if vpn else "No", "fraud_ground_truth": vpn},
        "Locations (24hr)": {"value": country, "fraud_ground_truth": high_risk_geo},
        "Same-IP accounts": {"value": "—", "fraud_ground_truth": False},
    }

    if score > 0.88:
        ai_rec = "Quarantine"
    elif score > 0.78:
        ai_rec = "Monitor"
    else:
        ai_rec = "Clear"

    return {
        "case_id": str(row.get("event_id", "CASE-?")),
        "fraud_score": score,
        "signals": signals,
        "ai_recommendation": ai_rec,
        "submitted": False,
        "analyst_signals": {},
        "analyst_decision": None,
    }


def _record_disposition(case: dict, attested: bool):
    st.session_state["fraud_ops_dispositions"].append({
        "event_id": case["case_id"],
        "decision": case["analyst_decision"],
        "decision_reason": case.get("analyst_reason", "—"),
        "ai_recommendation": case["ai_recommendation"],
        "fraud_count": case.get("fraud_count", 0),
        "attested": attested,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ----------------------------------------------------------------------------
# Header strip + ribbon
# ----------------------------------------------------------------------------

def _render_header_strip():
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #AF2896 0%, #121212 100%); border-radius:12px; padding:24px 32px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:11px; font-weight:700; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1.5px;">1st Line of Defense · Trust &amp; Safety</div>
                    <div style="font-size:30px; font-weight:900; color:{SPOTIFY_WHITE}; letter-spacing:-0.5px; line-height:1.1; margin-top:6px;">Fraud Operations — Review Queue</div>
                    <div style="font-size:13px; color:rgba(255,255,255,0.75); margin-top:6px;">Live cases from <code style="background:rgba(0,0,0,0.4); padding:1px 6px; border-radius:4px;">streamshield.honkify_live_events</code> · Switch tabs to compare workflow before and after audit recommendations.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ribbon(live_df: pd.DataFrame, source: str):
    review_df = _ensure_review_zone(live_df)

    today = pd.Timestamp.utcnow().date()
    if live_df is not None and len(live_df) > 0 and "timestamp" in live_df.columns:
        ts = pd.to_datetime(live_df["timestamp"], utc=True, errors="coerce")
        quarantined_today = int(((live_df["classification"] == "quarantine") & (ts.dt.date == today)).sum())
    else:
        quarantined_today = 0

    open_review = len(review_df) if review_df is not None else 0
    median_score = float(review_df["fraud_score"].median()) if open_review > 0 else 0.0
    queue_age = _queue_age_minutes(review_df)

    cols = st.columns([1, 1, 1, 1, 1])
    metrics = [
        ("Open Review Cases", f"{open_review}", COLOR_WARNING),
        ("Quarantined (24h)", f"{quarantined_today}", COLOR_DANGER),
        ("Median Score (Review)", f"{median_score:.2f}" if open_review else "—", COLOR_INFO),
        ("Oldest Open (min)", f"{queue_age:.0f}" if queue_age else "—", COLOR_WARNING),
    ]
    for col, (label, value, color) in zip(cols[:4], metrics):
        with col:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 18px; border:1px solid rgba(83,83,83,0.25); border-left:3px solid {color};">
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1.2px;">{label}</div>
                    <div style="color:{SPOTIFY_WHITE}; font-size:26px; font-weight:800; margin-top:4px;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with cols[4]:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("⟳ Refresh", use_container_width=True, key="fraud_ops_refresh"):
            load_honkify_live_events.clear()
            st.rerun()

    if source == "bigquery_empty":
        st.info("Queue is empty. Open Honkify and click an Edge Case track to populate. Events appear here within 60 seconds, or click Refresh.")
    elif source == "unavailable":
        st.warning("Live BigQuery table not reachable. Showing empty queue. Other panels still render from cached data.")


# ----------------------------------------------------------------------------
# Before tab
# ----------------------------------------------------------------------------

def _render_old_queue_rows(review_df: pd.DataFrame):
    if review_df is None or len(review_df) == 0:
        st.markdown(
            f'<div style="color:{SPOTIFY_GRAY}; font-style:italic; padding:20px; text-align:center;">No live review-zone events. Click an Edge Case track in Honkify to populate.</div>',
            unsafe_allow_html=True,
        )
        return

    for _, row in review_df.head(5).iterrows():
        score = float(row.get("fraud_score", 0))
        ai_verdict = "REJECT" if score > 0.85 else "MONITOR" if score > 0.78 else "REVIEW"
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; margin-bottom:10px; border:1px solid rgba(83,83,83,0.25); border-left:3px solid {COLOR_DANGER}; overflow:hidden;">
                <div style="background:linear-gradient(90deg, rgba(232,17,91,0.18), rgba(232,17,91,0.04)); padding:10px 18px; border-bottom:1px solid rgba(232,17,91,0.3);">
                    <span style="color:{COLOR_DANGER}; font-size:13px; font-weight:800; letter-spacing:1px;">▶ LLM RECOMMENDATION: {ai_verdict}</span>
                    <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; margin-left:12px;">confidence {score:.2f}</span>
                </div>
                <div style="padding:12px 18px;">
                    <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:600;">{row.get('track_name','—')} <span style="color:{SPOTIFY_LIGHT_GRAY}; font-weight:400;">by {row.get('artist_name','—')}</span></div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:6px;">{row.get('event_id','—')} &middot; user {row.get('user_id','—')} &middot; {row.get('country','??')} &middot; {row.get('device_type','??')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_analyst_agreement_chart(reviews_df: pd.DataFrame):
    if reviews_df is None or len(reviews_df) == 0:
        return
    grouped = (
        reviews_df.groupby("analyst_name")["agreed_with_llm"]
        .mean()
        .sort_values(ascending=True)
        .tail(8)
    )
    colors = [COLOR_DANGER if v > 0.96 else SPOTIFY_GREEN for v in grouped.values]
    fig = go.Figure(go.Bar(
        x=grouped.values,
        y=grouped.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v * 100:.0f}%" for v in grouped.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Analyst agreement with LLM (last 90 days)",
        xaxis=dict(range=[0, 1.05], tickformat=".0%"),
        margin=dict(l=120, r=40, t=50, b=40),
    )
    apply_spotify_style(fig, height=320)
    fig.add_vline(x=0.96, line_dash="dot", line_color=COLOR_DANGER)
    st.plotly_chart(fig, use_container_width=True)


def _render_circular_dependency():
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {COLOR_DANGER};">
            <div style="color:{COLOR_DANGER}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px;">Circular dependency · risk R3</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:700; margin-bottom:12px;">Training label quality depends on analyst independence</div>
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin:14px 0;">
                <div style="flex:1; background:#0f0f0f; border-radius:6px; padding:10px; text-align:center; color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;">AI recommends</div>
                <div style="color:{COLOR_DANGER}; font-weight:800;">→</div>
                <div style="flex:1; background:#0f0f0f; border-radius:6px; padding:10px; text-align:center; color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;">Analyst reviews<br><span style="color:{COLOR_WARNING};">LLM shown first</span></div>
                <div style="color:{COLOR_DANGER}; font-weight:800;">→</div>
                <div style="flex:1; background:#0f0f0f; border-radius:6px; padding:10px; text-align:center; color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;">Logged as<br>"human-verified"</div>
                <div style="color:{COLOR_DANGER}; font-weight:800;">→</div>
                <div style="flex:1; background:#0f0f0f; border-radius:6px; padding:10px; text-align:center; color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;">Training label</div>
                <div style="color:{COLOR_DANGER}; font-weight:800;">↺</div>
            </div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6; margin-top:8px;">
                95% of streams are handled automatically (92% pass, 3% quarantine) — the model is working well.
                The remaining 5% are genuine edge cases that need human judgment.
                The risk is not the model — it's that the current workflow shows the LLM's recommendation before the analyst
                forms their own view on these edge cases. If analyst decisions simply echo the LLM, those echoes
                become training labels for the next cycle. The Signal Card resolves this: the analyst assesses first,
                the LLM provides a second opinion after, and both perspectives are captured with clear provenance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_appeal_backlog_chart(appeals_df: pd.DataFrame):
    if appeals_df is None or len(appeals_df) == 0:
        return
    grouped = appeals_df.groupby("artist_type")["days_to_resolve"].mean().reset_index()
    grouped = grouped.sort_values("days_to_resolve", ascending=True)
    fig = go.Figure(go.Bar(
        x=grouped["days_to_resolve"],
        y=grouped["artist_type"],
        orientation="h",
        marker_color=[COLOR_DANGER if v > 20 else COLOR_WARNING if v > 10 else SPOTIFY_GREEN for v in grouped["days_to_resolve"]],
        text=[f"{v:.0f} days" for v in grouped["days_to_resolve"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Mean appeal resolution time by artist type",
        xaxis_title="Days to resolve",
        margin=dict(l=120, r=60, t=50, b=40),
    )
    apply_spotify_style(fig, height=300)
    fig.add_vline(x=10, line_dash="dot", line_color=SPOTIFY_GREEN, annotation_text="target SLA 10d", annotation_position="top")
    fig.add_vline(x=38, line_dash="dot", line_color=COLOR_DANGER, annotation_text="indie observed 38d", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)


def _render_drift_and_thresholds(perf_df):
    """Compact drift + threshold governance panel — baked into Before tab."""
    if perf_df is None or len(perf_df) == 0:
        return

    pf = perf_df.copy().sort_values("date")

    col_drift, col_thresh = st.columns(2)

    with col_drift:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pf["date"], y=pf["precision"], mode="lines",
            line=dict(color=COLOR_DANGER, width=2), name="Precision",
        ))
        fig.add_trace(go.Scatter(
            x=pf["date"], y=pf["psi_score"], mode="lines",
            line=dict(color=COLOR_INFO, width=1.5, dash="dot"), name="PSI",
            yaxis="y2",
        ))
        fig.update_layout(
            title="Model drift — precision declining, PSI rising",
            yaxis=dict(title="Precision", range=[0.7, 1.0]),
            yaxis2=dict(title="PSI", overlaying="y", side="right", range=[0, 0.35]),
            margin=dict(l=50, r=50, t=45, b=35),
            legend=dict(orientation="h", y=1.12, x=0.0),
            height=280,
        )
        apply_spotify_style(fig, height=280)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px;">Scenario modeling: precision declining post-acquisition, PSI elevated. <strong style="color:{COLOR_DANGER};">No automated alert exists — no continuous monitoring. Risk R1, R4.</strong> <em style="color:{SPOTIFY_GRAY};">(Illustrative data.)</em></div>',
            unsafe_allow_html=True,
        )

    with col_thresh:
        thresholds = pd.DataFrame({
            "Threshold": ["Auto-quarantine", "Review zone", "Auto-pass"],
            "Score range": ["> 0.95", "0.70 – 0.95", "< 0.70"],
            "Set by": ["Engineering", "Engineering", "Engineering"],
            "Business approval": ["None", "None", "None"],
            "Last reviewed": ["Never", "Never", "Never"],
            "Sensitivity analysis": ["Not performed", "Not performed", "Not performed"],
        })
        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700; margin-bottom:8px;">Threshold governance</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(thresholds, use_container_width=True, hide_index=True, height=180)
        st.markdown(
            f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px;">All three classification thresholds were set by engineering without Finance, Legal, or Content sign-off. No sensitivity analysis performed. <strong style="color:{COLOR_DANGER};">Risk R2 — SOX-relevant application control.</strong></div>',
            unsafe_allow_html=True,
        )


def _render_before_tab(live_df, reviews_df, appeals_df, perf_df=None):
    review_df = _ensure_review_zone(live_df)

    st.markdown(
        f'<div style="color:{COLOR_INFO}; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-top:8px;">Current State Assessment · Q3 2025</div>',
        unsafe_allow_html=True,
    )

    # Acknowledge what's working FIRST
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:16px 20px; border-left:4px solid {SPOTIFY_GREEN}; margin-bottom:18px;">
            <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px;">What's working well</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                <strong style="color:{SPOTIFY_WHITE};">StreamShield has achieved significant results in 6 months.</strong>
                The system processes billions of streams and classifies them in near-real-time —
                The model automatically handles 95% of all streams — 92% pass as verified, 3% are auto-quarantined.
                Only 5% are edge cases requiring human review.
                Fraudulent royalty payouts have been reduced by approximately <strong style="color:{SPOTIFY_GREEN};">40%</strong> compared to prior methods.
                The three-tier classification system, the 90-day quarantine hold, the LLM investigation assistant,
                and the appeal process through Content & Rights are all operational controls that demonstrate
                a strong foundation. The goal of this assessment is not to criticize — it is to <strong style="color:{SPOTIFY_WHITE};">optimize
                a system that is already delivering value</strong>, and to identify areas where the control
                environment can mature as StreamShield scales.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-bottom:18px;">The sections below identify specific areas for improvement. Green borders = working. Red borders = opportunities for strengthening.</div>',
        unsafe_allow_html=True,
    )

    # Section 1 — Model & threshold issues
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800; margin-top:8px;">1 · Model drift & ungoverned thresholds</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:12px;">Post-catalog-acquisition, our scenario modeling shows precision declining with no automated alert — the model was last retrained 4 months ago and a significant catalog acquisition has since changed content distribution. Thresholds set by engineering without business approval. <strong style="color:{COLOR_DANGER};">Risks R1, R2, R4.</strong> <em style="color:{SPOTIFY_GRAY};">(Precision figures based on illustrative scenario data.)</em></div>', unsafe_allow_html=True)
    _render_drift_and_thresholds(perf_df)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Section 2 — The old review queue
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">2 · Review queue (LLM-first workflow)</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:12px;">Each row places the LLM\'s verdict above all other information. The analyst sees the AI\'s recommendation BEFORE reading any raw signals — biasing their judgment. <strong style="color:{COLOR_DANGER};">Risk R3.</strong></div>', unsafe_allow_html=True)
    _render_old_queue_rows(review_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 3
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">3 · Human review workflow (5% of streams)</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:8px;">Only 5% of streams reach human review — these are genuine edge cases where the model\'s confidence is between 70-95%. The LLM assistant helps analysts investigate these cases, which is valuable. The workflow refinement opportunity: resequencing so the analyst forms a view before seeing the LLM summary, and introducing challenge cases to validate analyst independence. <strong style="color:{COLOR_WARNING};">Observation O-003.</strong></div>', unsafe_allow_html=True)
    _render_analyst_agreement_chart(reviews_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 4
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">4 · The circular dependency</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _render_circular_dependency()

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 5
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">5 · Appeals backlog</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:8px;">The case study confirms a 6-week appeal resolution for one indie label dispute. Our scenario data models a systemic pattern where resolution times vary by artist type, with no formal SLA in place. <strong style="color:{COLOR_DANGER};">Risks R5, R6.</strong> <em style="color:{SPOTIFY_GRAY};">(Resolution time breakdown based on illustrative data.)</em></div>', unsafe_allow_html=True)
    _render_appeal_backlog_chart(appeals_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 6 — Explainability gap
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">6 · Explainability gap — why was this stream flagged?</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {COLOR_WARNING}; margin-top:8px; margin-bottom:12px;">
            <div style="color:{COLOR_WARNING}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">The two-sided problem</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                <strong style="color:{SPOTIFY_WHITE};">For the business:</strong> The model outputs a fraud probability score (e.g., 0.84) but cannot explain
                <em>which signals</em> drove that score or <em>how the weights are distributed</em> across features.
                Analysts cannot learn from the model's decisions — they see the verdict but not the reasoning.
                If the model is picking up on new patterns (e.g., geographic clustering after a catalog acquisition),
                the team has no visibility into that evolution. This limits the team's ability to improve manual review
                and to calibrate their own judgment over time.<br><br>
                <strong style="color:{SPOTIFY_WHITE};">For compliance:</strong> When an artist or label complains — "why were my streams quarantined?" —
                the only answer today is the probability score. Under GDPR Article 22, individuals have the right to
                "meaningful information about the logic involved" in automated decisions with significant effects.
                Under the EU AI Act, high-risk AI systems require transparency about decision factors.
                A probability score is not an explanation. Without feature-level explainability (e.g., SHAP values showing
                "VPN usage contributed 35%, account age contributed 28%, play duration contributed 22%"),
                Spotify cannot defend its quarantine decisions in a regulatory inquiry or artist lawsuit.
                <strong style="color:{COLOR_WARNING};">Risk R11, Observation O-007.</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Section 7 — LLM assistant
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">7 · LLM assistant — valuable but needs workflow refinement</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.06), {SPOTIFY_CARD_BG}); border-radius:8px; padding:16px 20px; border-left:4px solid {SPOTIFY_GREEN}; margin-top:8px; margin-bottom:10px;">
            <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">What's working</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                The LLM investigation assistant is a genuine asset. It summarizes account activity, cross-references fraud indicators,
                and surfaces which aspects look problematic versus which look normal. This context helps analysts focus on what matters
                in each case rather than parsing raw data. <strong style="color:{SPOTIFY_WHITE};">AI assistance is the right direction — the goal is agentic workflows, not removing AI.</strong>
            </div>
        </div>
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {COLOR_WARNING}; margin-top:8px;">
            <div style="color:{COLOR_WARNING}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Opportunity for refinement</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                Two workflow adjustments would strengthen this control:
                (1) <strong style="color:{SPOTIFY_WHITE};">Resequence</strong> — show the LLM summary AFTER the analyst forms an initial view, not before. The LLM becomes a second opinion rather than the first impression.
                (2) <strong style="color:{SPOTIFY_WHITE};">Attest</strong> — require the analyst to confirm they independently reviewed the signals before the LLM summary is stored as the case record. This creates a verifiable audit trail.
                The LLM stays. The workflow improves. <strong style="color:{COLOR_WARNING};">Observation O-006.</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# After tab
# ----------------------------------------------------------------------------

def _render_new_queue_rows(review_df: pd.DataFrame):
    if review_df is None or len(review_df) == 0:
        st.markdown(
            f'<div style="color:{SPOTIFY_GRAY}; font-style:italic; padding:20px; text-align:center;">No live review-zone events. Click an Edge Case track in Honkify to populate.</div>',
            unsafe_allow_html=True,
        )
        return

    sorted_df = review_df.copy()
    sorted_df["_ts"] = pd.to_datetime(sorted_df["timestamp"], utc=True, errors="coerce")
    sorted_df = sorted_df.sort_values("_ts", ascending=True)

    for _, row in sorted_df.head(5).iterrows():
        chips = _top3_signals_for_row(row)
        chip_html = " ".join([
            f'<span style="background:rgba(83,83,83,0.18); color:{c}; border:1px solid {c}; padding:3px 10px; border-radius:500px; font-size:10px; font-weight:700; letter-spacing:0.5px; margin-right:6px;">{label}</span>'
            for label, c in chips
        ])

        age = int(row.get("account_age_days", 999))

        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; margin-bottom:2px; border:1px solid rgba(83,83,83,0.25); border-left:3px solid {SPOTIFY_GREEN}; padding:14px 18px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:600;">{row.get('track_name','—')} <span style="color:{SPOTIFY_LIGHT_GRAY}; font-weight:400;">by {row.get('artist_name','—')}</span></div>
                        <div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:4px;">{row.get('event_id','—')} · user {row.get('user_id','—')} · score {float(row.get('fraud_score',0)):.2f}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Top contributing signals</div>
                        <div style="margin-top:6px;">{chip_html}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if age < 90:
            st.markdown(
                f'<div style="margin:-2px 0 10px 0; padding:8px 12px; background:rgba(245,155,35,0.08); border-radius:0 0 8px 8px; border-left:3px solid {COLOR_WARNING};">'
                f'<span style="color:{COLOR_WARNING}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">NEW CATALOG · grace period day {age}/90</span>'
                f'<span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; margin-left:12px;">Threshold raised 0.95 → 0.98 · Provisional royalty paid · Retraining T-{30 - (age % 30)} days</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)


def _render_post_controls_bias_chart(reviews_df: pd.DataFrame):
    if reviews_df is None or len(reviews_df) == 0:
        return
    grouped = (
        reviews_df.groupby("analyst_name")["agreed_with_llm"]
        .mean()
        .sort_values(ascending=True)
        .tail(8)
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped.values, y=grouped.index, orientation="h",
        name="Observed (Before)",
        marker_color=COLOR_DANGER, opacity=0.55,
        text=[f"{v * 100:.0f}%" for v in grouped.values], textposition="outside",
    ))
    # Target band — NOT a prediction, shown as a shaded region
    fig.add_vrect(x0=0.70, x1=0.85, fillcolor="rgba(29,185,84,0.10)",
                  layer="below", line_width=0,
                  annotation_text="target band 70-85%",
                  annotation_position="top left",
                  annotation=dict(font=dict(color=SPOTIFY_GREEN, size=10)))
    fig.update_layout(
        title="Analyst agreement — observed vs target band after Signal Card rollout",
        xaxis=dict(range=[0, 1.1], tickformat=".0%"),
        margin=dict(l=120, r=40, t=50, b=40),
        legend=dict(orientation="h", y=1.12, x=0.0),
    )
    apply_spotify_style(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)


def _render_post_controls_appeal_chart(appeals_df: pd.DataFrame):
    if appeals_df is None or len(appeals_df) == 0:
        return
    grouped = appeals_df.groupby("artist_type")["days_to_resolve"].mean().reset_index()
    grouped = grouped.sort_values("days_to_resolve", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped["artist_type"], y=grouped["days_to_resolve"],
        name="Observed (Before Controls)",
        marker_color=[COLOR_DANGER if v > 10 else COLOR_WARNING for v in grouped["days_to_resolve"]],
        text=[f"{v:.0f}d" for v in grouped["days_to_resolve"]], textposition="outside",
    ))
    fig.update_layout(
        title="Mean appeal resolution time — observed vs proposed SLA target",
        yaxis_title="Days to resolve",
        margin=dict(l=60, r=40, t=50, b=40),
    )
    apply_spotify_style(fig, height=320)
    fig.add_hline(y=10, line_dash="dot", line_color=SPOTIFY_GREEN,
                  annotation_text="proposed 10-day SLA (Gap 7)",
                  annotation_position="top right")
    st.plotly_chart(fig, use_container_width=True)


def _render_signal_card_section(review_df: pd.DataFrame):
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:12px;">Open a live case below. Assess each signal independently before the AI recommendation is revealed. <strong style="color:{SPOTIFY_GREEN};">Gap 3, Gap 11.</strong></div>', unsafe_allow_html=True)

    if review_df is not None and len(review_df) > 0:
        options = list(review_df["event_id"].head(5))
        labels = {
            row["event_id"]: f"{row['track_name']} · {row['artist_name']} · score {row['fraud_score']:.2f}"
            for _, row in review_df.head(5).iterrows()
        }
        chosen = st.selectbox(
            "Select a live case",
            options=options,
            format_func=lambda eid: labels.get(eid, eid),
            key="fraud_ops_case_select",
        )
        active = st.session_state.get("fraud_ops_active_case")
        if active is None or active.get("case_id") != chosen:
            row = review_df[review_df["event_id"] == chosen].iloc[0]
            st.session_state["fraud_ops_active_case"] = _row_to_signal_card_case(row)
        case = st.session_state["fraud_ops_active_case"]
    else:
        st.markdown(
            f'<div style="color:{SPOTIFY_GRAY}; font-style:italic; padding:14px; background:{SPOTIFY_CARD_BG}; border-radius:8px; border:1px solid rgba(83,83,83,0.2); margin-bottom:12px;">No live cases — showing a synthetic example. Click an Edge Case track in Honkify to wire this section to a real event.</div>',
            unsafe_allow_html=True,
        )
        if "fraud_ops_synthetic_case" not in st.session_state:
            from modules.signal_card_demo import _generate_case
            st.session_state["fraud_ops_synthetic_case"] = _generate_case()
        case = st.session_state["fraud_ops_synthetic_case"]

    render_signal_card_widget(case, key_prefix=f"fraud_ops_card_{case['case_id']}")

    if case.get("submitted"):
        attested = st.checkbox(
            "I have reviewed signals independently and attest to this disposition (Gap 5)",
            key=f"fraud_ops_attest_{case['case_id']}",
        )
        already_logged = any(d["event_id"] == case["case_id"] for d in st.session_state["fraud_ops_dispositions"])
        if attested and not already_logged:
            _record_disposition(case, attested=True)
            st.success("Disposition logged with attestation. Internal Audit T3 + T4 will reflect this on next refresh.")
        elif already_logged:
            st.markdown(
                f'<div style="color:{SPOTIFY_GREEN}; font-size:12px; margin-top:8px;">✓ Disposition recorded — visible on the Internal Audit page.</div>',
                unsafe_allow_html=True,
            )


def _render_audit_trail_card():
    sample_json = """{
  "case_id": "hk_1738291204_417",
  "analyst_id": "an_2206",
  "signal_assessments": {
    "Account age":         "Yes — 12 days",
    "Devices used":        "No — desktop",
    "Avg play duration":   "Yes — 31 sec",
    "Skip rate":           "Yes — 2%",
    "VPN detected":        "Yes",
    "Locations (24hr)":    "Yes — RU",
    "Same-IP accounts":    "No"
  },
  "analyst_decision":  "Quarantine",
  "decision_reason":   "VPN + suspicious geography pattern",
  "ai_recommendation": "Quarantine",
  "agreed_with_ai":    true,
  "attested":          true,
  "llm_prompt_version":"sshield-prompt@v3.4.1",
  "timestamp":         "2026-04-09T11:41:32Z",
  "_training_eligible": true,
  "_knowledge_tags":   ["vpn_pattern", "geo_concentration", "new_account"]
}"""
    st.markdown(
        f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:8px;">Both perspectives — the analyst\'s independent assessment AND the LLM\'s summary — are captured in a single structured record. The <code>decision_reason</code> field captures human judgment; the <code>llm_recommendation</code> captures AI perspective. Together they enable: (1) quality training labels with provenance, (2) searchable case studies for onboarding, (3) auditable evidence showing human + AI collaboration. <strong style="color:{SPOTIFY_GREEN};">Observation O-006.</strong></div>',
        unsafe_allow_html=True,
    )
    st.code(sample_json, language="json")


def _render_after_tab(live_df, reviews_df, appeals_df):
    review_df = _ensure_review_zone(live_df)

    st.markdown(
        f'<div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-top:8px;">State After Controls · Live</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-bottom:18px;">Same live events, processed through the recommended workflow. Green borders mark active controls. Click through the Signal Card to flip Internal Audit\'s T3 and T4 controls live.</div>',
        unsafe_allow_html=True,
    )

    # Section 1
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800; margin-top:8px;">1 · Triaged review queue</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:12px;">Sorted by queue age (oldest first). Each row shows top-3 contributing signals before any AI verdict. New-catalog content enters the Catalog Onboarding Protocol with raised threshold and provisional royalties. <strong style="color:{SPOTIFY_GREEN};">Gaps 3, 6, 11.</strong></div>', unsafe_allow_html=True)
    _render_new_queue_rows(review_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 2
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">2 · Analyst agreement post-controls</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:8px;">Per-analyst LLM agreement rates for the 5% of streams that reach human review. The green band marks a healthy range for independent review. With the Signal Card resequencing, we can validate whether agreement reflects calibration or anchoring. <strong style="color:{SPOTIFY_GREEN};">Observation O-003.</strong></div>', unsafe_allow_html=True)
    _render_post_controls_bias_chart(reviews_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 3
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">3 · Signal Confirmation Card (interactive)</div>', unsafe_allow_html=True)
    _render_signal_card_section(review_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 4
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">4 · Appeals with SLA enforcement</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:8px;">The green line marks the proposed 10-day SLA. Provisional royalty payments initiate when an appeal is filed; SLA timer runs in a workflow engine; breaches alert Slack and the IAR exceptions inbox. Actual post-SLA performance requires rollout measurement. <strong style="color:{SPOTIFY_GREEN};">Gap 7.</strong></div>', unsafe_allow_html=True)
    _render_post_controls_appeal_chart(appeals_df)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Section 5 — Explainability (After)
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">5 · Explainability — what the analyst and artist now see</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.06), {SPOTIFY_CARD_BG}); border-radius:8px; padding:16px 20px; border-left:4px solid {SPOTIFY_GREEN}; margin-top:8px; margin-bottom:12px;">
            <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">After: explainability at the right level</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                <strong style="color:{SPOTIFY_WHITE};">During case review — analyst sees raw signals only.</strong>
                No model weights, no SHAP values, no LLM summary. The analyst makes an independent decision based on the actual data.
                Showing model feature importance during review would create a new anchoring problem — replacing one bias source with another.<br><br>
                <strong style="color:{SPOTIFY_WHITE};">Weekly team sessions — aggregate SHAP analysis.</strong>
                Across hundreds of cases: "What signal combinations is the model weighting most heavily? Where do analyst assessments
                diverge from each other?" This is where the team learns from the model's pattern recognition — at population level,
                not per-case "gotcha" moments. When a catalog acquisition shifts the distribution, the team can see exactly which new
                features are triggering and discuss calibration adjustments.<br><br>
                <strong style="color:{SPOTIFY_WHITE};">On artist appeal — feature-level explanation.</strong>
                When an artist asks "why was I flagged?", the response uses SHAP attribution: "VPN usage contributed 35%,
                play duration 28%, account age 22%." This satisfies GDPR Article 22 and gives the artist a meaningful,
                defensible explanation — not just a probability score.<br><br>
                <strong style="color:{SPOTIFY_WHITE};">For IAR — population-level comparison.</strong>
                The auditor compares analyst decisions against model recommendations across the full population for control testing (T3, T5).
                No individual analyst is told "the AI disagreed with you." The comparison is systemic, not personal.
                <strong style="color:{SPOTIFY_GREEN};">Risk R11 addressed at every level.</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Section 6 — Audit trail
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:800;">6 · Audit trail with attestation</div>', unsafe_allow_html=True)
    _render_audit_trail_card()


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def render(reviews_df, perf_df, appeals_df):
    _init_session_state()

    story_nav(
        step=2, total=3,
        title="The Problem & The Solution — What the 1st-line analyst sees",
        what_to_do="The <strong>Before</strong> tab shows the current workflow and areas for improvement: model drift, threshold governance, LLM sequencing. "
        "The <strong>After</strong> tab shows the same live events processed through "
        "the resequenced Signal Confirmation Card — assess signals first, receive LLM as second opinion, state your reasoning, then continue to Internal Audit.",
    )

    _render_header_strip()

    live_df, source = load_honkify_live_events()
    _render_ribbon(live_df, source)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    tab_before, tab_after = st.tabs(["Before Controls", "After Controls"])
    with tab_before:
        _render_before_tab(live_df, reviews_df, appeals_df, perf_df)
    with tab_after:
        _render_after_tab(live_df, reviews_df, appeals_df)

    story_next(
        "Internal Audit",
        "See how the 3rd-line auditor monitors everything continuously. If you completed the Signal Card above, "
        "controls T3 and T4 will be green — proving the cross-page handoff works live.",
    )
