"""Module: Data Pipelines — Real-time classification vs. ground truth assembly."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card,
)

PIPELINE_DIR = Path(__file__).parent.parent / "data" / "cached" / "pipelines"


def _load_pipeline_data():
    """Load all pipeline CSV files."""
    data = {}
    for f in PIPELINE_DIR.glob("*.csv"):
        data[f.stem] = pd.read_csv(f)
    return data


def render():
    st.markdown("## Data Pipelines")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Two fundamentally different data flows feed the StreamShield ecosystem. "
        "The real-time pipeline has minimal data and must decide in milliseconds. "
        "The ground truth pipeline assembles evidence over weeks to months from 6 independent sources."
        "</p>",
        unsafe_allow_html=True,
    )

    data = _load_pipeline_data()

    tab1, tab2, tab3 = st.tabs(["Real-Time Pipeline", "Ground Truth Pipeline", "Pipeline Comparison"])

    # ============================================
    # TAB 1: Real-Time Pipeline
    # ============================================
    with tab1:
        st.markdown("### Pipeline 1: Real-Time Stream Classification")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "What StreamShield sees when a stream happens. Raw event metadata, enriched with feature store lookups "
            "and network signals, scored by the ML model. Total latency: under 200ms. No ground truth available."
            "</p>",
            unsafe_allow_html=True,
        )

        # Pipeline stages
        stages = [
            {
                "name": "Raw Stream Event",
                "source": "Cloud Pub/Sub",
                "key": "p1_raw_stream_events",
                "color": COLOR_INFO,
                "latency": "0ms (event arrival)",
                "description": "Bare metadata from the streaming client. This is ALL that originates from the user's device.",
            },
            {
                "name": "Account Features",
                "source": "BigQuery Feature Store",
                "key": "p1_account_features",
                "color": COLOR_WARNING,
                "latency": "~50ms (lookup)",
                "description": "Pre-computed account-level features. Looked up by user_id from the feature store.",
            },
            {
                "name": "Track Metadata",
                "source": "Content Catalog (BigQuery)",
                "key": "p1_track_features",
                "color": SPOTIFY_GREEN,
                "latency": "~30ms (lookup)",
                "description": "Track and artist information from the content catalog. Includes new catalog flag.",
            },
            {
                "name": "Network Signals",
                "source": "Dataflow Streaming Aggregation",
                "key": "p1_network_signals",
                "color": "#AF2896",
                "latency": "~5s (streaming window)",
                "description": "Near-real-time aggregations: accounts per IP, VPN detection, geo mismatch.",
            },
            {
                "name": "ML Classification",
                "source": "StreamShield Model (GKE)",
                "key": "p1_ml_scores",
                "color": COLOR_DANGER,
                "latency": "~15ms (inference)",
                "description": "Fraud probability score + classification. This is the DECISION POINT — no ground truth exists here.",
            },
        ]

        for i, stage in enumerate(stages):
            df = data.get(stage["key"])
            if df is None:
                continue

            cols_list = list(df.columns)
            n_rows = len(df)
            n_cols = len(cols_list)

            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {stage['color']}; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <div>
                            <span style="color:{stage['color']}; font-size:12px; font-weight:700; letter-spacing:1px;">STAGE {i+1}</span>
                            <span style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-left:10px;">{stage['name']}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="color:{SPOTIFY_GRAY}; font-size:11px;">Source: </span>
                            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; font-weight:600;">{stage['source']}</span>
                            <br><span style="color:{SPOTIFY_GRAY}; font-size:11px;">Latency: </span>
                            <span style="color:{stage['color']}; font-size:12px; font-weight:600;">{stage['latency']}</span>
                        </div>
                    </div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-bottom:12px;">{stage['description']}</div>
                    <div style="background:#0a0a0a; border-radius:6px; padding:10px 14px; font-family:monospace; font-size:12px; color:{SPOTIFY_LIGHT_GRAY};">
                        <span style="color:{SPOTIFY_GRAY};">{n_rows:,} rows | {n_cols} columns:</span><br>
                        {', '.join([f'<span style="color:{SPOTIFY_WHITE};">{c}</span>' for c in cols_list])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Show sample data
            with st.expander(f"Preview: {stage['name']} ({n_rows:,} rows)", expanded=False):
                st.dataframe(df.head(8), use_container_width=True, hide_index=True)

        # Total fields available at decision time
        all_rt_cols = set()
        for key in ["p1_raw_stream_events", "p1_account_features", "p1_track_features", "p1_network_signals", "p1_ml_scores"]:
            if key in data:
                all_rt_cols.update(data[key].columns)

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(245,155,35,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); margin-top:8px;">
                <div style="color:{COLOR_WARNING}; font-weight:700; font-size:14px; margin-bottom:8px;">Total Data at Decision Time</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">
                    <strong style="color:{SPOTIFY_WHITE};">{len(all_rt_cols)} fields</strong> available across all enrichment sources.
                    Joined by user_id, track_id, and ip_hash.
                    Total pipeline latency: <strong style="color:{SPOTIFY_WHITE};">under 200ms</strong>.
                    <br><br>
                    <span style="color:{COLOR_DANGER}; font-weight:600;">What's NOT available:</span>
                    is_actually_fraudulent, label_source, label_confidence, analyst_decision, appeal_outcome, behavioral_decay_classification.
                    <strong>The system cannot know if its decision is correct at classification time.</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================
    # TAB 2: Ground Truth Pipeline
    # ============================================
    with tab2:
        st.markdown("### Pipeline 2: Ground Truth Assembly")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Evidence assembled AFTER classification from 6 independent sources. "
            "Each source has different latency, confidence, and coverage. "
            "Only ~14% of events ever receive a ground truth label."
            "</p>",
            unsafe_allow_html=True,
        )

        gt_sources = [
            {
                "name": "Heuristic Rules",
                "key": "p2_gt_heuristic_flags",
                "color": SPOTIFY_GREEN,
                "latency": "Real-time",
                "confidence": "90-95%",
                "coverage": "~2% of events",
                "description": "Rule-based flags for self-evident fraud: same IP burst, 24hr nonstop streaming, sequential track patterns.",
            },
            {
                "name": "Analyst Decisions",
                "key": "p2_gt_analyst_decisions",
                "color": COLOR_INFO,
                "latency": "Hours to 1 day",
                "confidence": "70-92%",
                "coverage": "Review-zone only (~5%)",
                "description": "Human analyst classifications for review-zone cases. Subject to automation bias — label quality depends on review thoroughness.",
            },
            {
                "name": "Appeal Outcomes",
                "key": "p2_gt_appeal_outcomes",
                "color": COLOR_WARNING,
                "latency": "11-38 days",
                "confidence": "75-95%",
                "coverage": "~15% of quarantined",
                "description": "Artists/labels contest quarantine decisions. Overturned = strong legitimate signal. Upheld = confirmed fraud.",
            },
            {
                "name": "Behavioral Decay",
                "key": "p2_gt_behavioral_decay",
                "color": "#AF2896",
                "latency": "30-90 days",
                "confidence": "55-85%",
                "coverage": "~5% of accounts",
                "description": "Retrospective analysis: accounts that stream intensely then go permanently silent are probable bots.",
            },
            {
                "name": "Confirmed Takedowns",
                "key": "p2_gt_confirmed_takedowns",
                "color": COLOR_DANGER,
                "latency": "Months",
                "confidence": "99%",
                "coverage": "Very low (investigation-driven)",
                "description": "Highest confidence. Fraud operations confirmed by Trust & Safety investigation or law enforcement.",
            },
            {
                "name": "Distributor Flags",
                "key": "p2_gt_distributor_flags",
                "color": SPOTIFY_GRAY,
                "latency": "Months",
                "confidence": "75-90%",
                "coverage": "Distributor-level (not per-event)",
                "description": "Distributors with repeated violations. All content from flagged distributors gets risk-elevated.",
            },
        ]

        for i, source in enumerate(gt_sources):
            df = data.get(source["key"])
            n_rows = len(df) if df is not None else 0
            n_cols = len(df.columns) if df is not None else 0
            cols_list = list(df.columns) if df is not None else []

            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {source['color']}; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <div>
                            <span style="color:{source['color']}; font-size:12px; font-weight:700; letter-spacing:1px;">SOURCE {i+1}</span>
                            <span style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-left:10px;">{source['name']}</span>
                        </div>
                        <div style="text-align:right; font-size:12px;">
                            <span style="color:{SPOTIFY_GRAY};">Latency: </span><span style="color:{source['color']}; font-weight:600;">{source['latency']}</span>
                            <br><span style="color:{SPOTIFY_GRAY};">Confidence: </span><span style="color:{SPOTIFY_WHITE}; font-weight:600;">{source['confidence']}</span>
                            <br><span style="color:{SPOTIFY_GRAY};">Coverage: </span><span style="color:{SPOTIFY_LIGHT_GRAY};">{source['coverage']}</span>
                        </div>
                    </div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-bottom:12px;">{source['description']}</div>
                    <div style="background:#0a0a0a; border-radius:6px; padding:10px 14px; font-family:monospace; font-size:12px; color:{SPOTIFY_LIGHT_GRAY};">
                        <span style="color:{SPOTIFY_GRAY};">{n_rows:,} rows | {n_cols} columns:</span><br>
                        {', '.join([f'<span style="color:{SPOTIFY_WHITE};">{c}</span>' for c in cols_list])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if df is not None and len(df) > 0:
                with st.expander(f"Preview: {source['name']} ({n_rows:,} rows)", expanded=False):
                    st.dataframe(df.head(8), use_container_width=True, hide_index=True)

        # Collated ground truth
        collated = data.get("p2_collated_ground_truth")
        if collated is not None:
            st.markdown("### Collated Ground Truth")

            col1, col2, col3, col4 = st.columns(4)
            has_gt = collated["has_ground_truth"].sum() if "has_ground_truth" in collated.columns else 0
            no_gt = len(collated) - has_gt
            multi = (collated["n_label_sources"] > 1).sum() if "n_label_sources" in collated.columns else 0

            with col1:
                st.markdown(metric_card("Total Events", f"{len(collated):,}"), unsafe_allow_html=True)
            with col2:
                st.markdown(metric_card("With Ground Truth", f"{has_gt:,} ({has_gt/len(collated):.1%})"), unsafe_allow_html=True)
            with col3:
                st.markdown(metric_card("No Ground Truth", f"{no_gt:,} ({no_gt/len(collated):.1%})"), unsafe_allow_html=True)
            with col4:
                st.markdown(metric_card("Multi-Source Labels", f"{multi:,}"), unsafe_allow_html=True)

            # Label source breakdown
            if has_gt > 0 and "label_source" in collated.columns:
                source_counts = collated[collated["has_ground_truth"]].groupby("label_source").size().sort_values(ascending=True)

                fig = go.Figure(go.Bar(
                    x=source_counts.values,
                    y=source_counts.index,
                    orientation="h",
                    marker_color=[SPOTIFY_GREEN, COLOR_INFO, COLOR_WARNING, "#AF2896", COLOR_DANGER][:len(source_counts)],
                    text=source_counts.values,
                    textposition="auto",
                    textfont=dict(color=SPOTIFY_WHITE, size=12),
                ))
                apply_spotify_style(fig, height=300)
                fig.update_layout(
                    title="Ground Truth Labels by Primary Source",
                    xaxis_title="Number of Events",
                )
                st.plotly_chart(fig, use_container_width=True)

    # ============================================
    # TAB 3: Pipeline Comparison
    # ============================================
    with tab3:
        st.markdown("### Pipeline Comparison: Real-Time vs. Ground Truth")

        comparison = [
            ("Purpose", "Classify streams as they happen", "Evaluate if classifications were correct"),
            ("Timing", "Real-time (under 200ms)", "Retrospective (hours to months)"),
            ("Data Available", f"{len(all_rt_cols)} fields from 5 sources", "30+ fields from 6 ground truth sources"),
            ("Ground Truth", "NOT AVAILABLE", "Assembled from multiple sources"),
            ("Metrics Possible", "Quarantine rate, score distribution, PSI", "Precision, recall, F1, ROC, confusion matrix"),
            ("Self-Evaluation", "Cannot know if decisions are correct", "Can compare decisions against labels"),
            ("Latency Constraint", "Must decide in milliseconds", "Can take weeks to assemble"),
            ("Coverage", "100% of streams scored", f"~13.6% of streams receive labels"),
            ("Label Confidence", "N/A (no labels)", "55-99% depending on source"),
            ("GCP Services", "Pub/Sub, Dataflow, GKE, Feature Store", "BigQuery, Cloud SQL, Kubeflow"),
        ]

        st.markdown(
            f"""
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <tr style="border-bottom:2px solid {SPOTIFY_GRAY};">
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:12px; width:25%;"></td>
                    <td style="color:{COLOR_WARNING}; padding:12px; font-weight:700; width:37.5%;">Real-Time Pipeline</td>
                    <td style="color:{SPOTIFY_GREEN}; padding:12px; font-weight:700; width:37.5%;">Ground Truth Pipeline</td>
                </tr>
                {"".join([
                    f'<tr style="border-bottom:1px solid rgba(83,83,83,0.2);">'
                    f'<td style="color:{SPOTIFY_WHITE}; padding:10px 12px; font-weight:600;">{row[0]}</td>'
                    f'<td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 12px;">{row[1]}</td>'
                    f'<td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 12px;">{row[2]}</td>'
                    f'</tr>'
                    for row in comparison
                ])}
            </table>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # The key insight
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(232,17,91,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:24px; border-left:4px solid {COLOR_DANGER};">
                <div style="color:{COLOR_DANGER}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Critical Audit Insight</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:15px; line-height:1.6;">
                    <strong>86.4% of streams are never independently validated.</strong><br><br>
                    The model classifies every stream, but only ~13.6% ever receive a ground truth label from any source.
                    For the remaining 86.4%, the model's classification is the only assessment that exists —
                    there is no feedback signal to indicate whether those decisions were correct.<br><br>
                    This means model drift could affect the majority of classifications without generating any observable error signal.
                    The only way to detect degradation in the unlabeled majority is through distributional proxies (PSI, score distribution shifts, quarantine rate changes) —
                    which is exactly what our Drift Monitor module does.<br><br>
                    <strong>Recommendation:</strong> Expand ground truth coverage through targeted sampling of the "pass" category (streams scored below 70%).
                    Currently, no ground truth source systematically evaluates streams that the model classified as legitimate.
                    A periodic random audit of passed streams would provide the only visibility into false negative rates.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
