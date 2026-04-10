"""Module 5: Data Lineage & Ground Truth — How labeled data is created and validated."""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card, CHART_COLORS,
)


def render(events_df: pd.DataFrame, reviews_df: pd.DataFrame, appeals_df: pd.DataFrame):
    st.markdown("## Data Lineage & Ground Truth")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Understanding how ground truth labels are established, validated, and maintained. "
        "Model accuracy metrics are only as reliable as the labels they're measured against."
        "</p>",
        unsafe_allow_html=True,
    )

    # System architecture diagram
    st.markdown("### Ground Truth Label Sources")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "In production, ground truth is assembled from multiple imperfect sources. No single source is authoritative — "
        "confidence increases when multiple sources converge on the same classification."
        "</p>",
        unsafe_allow_html=True,
    )

    # Architecture cards
    sources = [
        {
            "name": "Confirmed Takedowns",
            "icon": "1",
            "description": "When Spotify identifies and dismantles a fraud operation (bot farm, fake distributor), all associated streams are retroactively labeled as confirmed fraud.",
            "confidence": "Highest",
            "confidence_color": SPOTIFY_GREEN,
            "volume": "Low",
            "latency": "Weeks to months",
            "spotify_system": "Trust & Safety + Law Enforcement coordination",
            "example": "The Michael Smith case: 1,040 bot accounts, hundreds of thousands of AI tracks — all labeled as confirmed fraud after investigation.",
        },
        {
            "name": "Analyst Decisions",
            "icon": "2",
            "description": "Human analysts in the review zone (70-95%) classify streams as quarantine, monitor, or clear. These decisions become labels for model retraining.",
            "confidence": "Medium-High",
            "confidence_color": COLOR_INFO,
            "volume": "~200/day",
            "latency": "Same day",
            "spotify_system": "StreamShield Review Console + LLM Assistant",
            "example": "Analyst reviews account with 589 tracks/day, 1 device, VPN active — classifies as fraud. This label enters the retraining dataset.",
        },
        {
            "name": "Appeal Outcomes",
            "icon": "3",
            "description": "When artists appeal quarantine decisions and win, the streams are re-labeled as legitimate. Denied appeals reinforce the fraud label.",
            "confidence": "High",
            "confidence_color": SPOTIFY_GREEN,
            "volume": "~200 total in sample",
            "latency": "Weeks (avg 29 days)",
            "spotify_system": "Content & Rights team appeal workflow",
            "example": "Indie label appeals viral campaign quarantine — overturned after 6 weeks. All associated streams re-labeled as legitimate.",
        },
        {
            "name": "Distributor Accountability",
            "icon": "4",
            "description": "Distributors flagged for repeated artificial streaming violations. All content from suspended distributors can be retroactively labeled.",
            "confidence": "Medium-High",
            "confidence_color": COLOR_INFO,
            "volume": "Low (distributor-level)",
            "latency": "Months",
            "spotify_system": "Distributor Portal + Penalty System (€10/track)",
            "example": "Distributor with 5+ fraud incidents gets suspended. Historical streams from their catalog are labeled as high-risk.",
        },
        {
            "name": "Heuristic Rules",
            "icon": "5",
            "description": "Some fraud is self-evident: 500 accounts from one IP streaming the same 50 tracks 24/7. Rule-based systems flag these with near-certainty.",
            "confidence": "High (for clear cases)",
            "confidence_color": SPOTIFY_GREEN,
            "volume": "High",
            "latency": "Real-time",
            "spotify_system": "Pub/Sub event stream + Dataflow rule engine",
            "example": "47 accounts on same IP subnet, all created within 2 hours, streaming identical track sequences — auto-labeled as coordinated fraud.",
        },
        {
            "name": "Behavioral Decay Analysis",
            "icon": "6",
            "description": "Accounts that stream intensely for 2 weeks then go permanently silent are retrospectively labeled as likely bots. Sustained accounts are labeled legitimate.",
            "confidence": "Medium",
            "confidence_color": COLOR_WARNING,
            "volume": "High (time-delayed)",
            "latency": "30-90 days retrospective",
            "spotify_system": "BigQuery scheduled queries + account lifecycle tracking",
            "example": "Account streams 600 tracks/day for 14 days, then zero activity for 60 days. Retrospectively labeled as probable bot account.",
        },
    ]

    for i in range(0, len(sources), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(sources):
                s = sources[i + j]
                with col:
                    st.markdown(
                        f"""
                        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {s['confidence_color']}; margin-bottom:12px; min-height:320px;">
                            <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                                <span style="background:{s['confidence_color']}22; color:{s['confidence_color']}; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px;">{s['icon']}</span>
                                <span style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700;">{s['name']}</span>
                            </div>
                            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5; margin-bottom:12px;">{s['description']}</div>
                            <div style="font-size:12px; color:{SPOTIFY_LIGHT_GRAY}; line-height:1.8;">
                                <span style="color:{SPOTIFY_GRAY};">Confidence:</span> <span style="color:{s['confidence_color']}; font-weight:600;">{s['confidence']}</span><br>
                                <span style="color:{SPOTIFY_GRAY};">Volume:</span> <span style="color:{SPOTIFY_WHITE};">{s['volume']}</span><br>
                                <span style="color:{SPOTIFY_GRAY};">Latency:</span> <span style="color:{SPOTIFY_WHITE};">{s['latency']}</span><br>
                                <span style="color:{SPOTIFY_GRAY};">Spotify System:</span> <span style="color:{SPOTIFY_WHITE};">{s['spotify_system']}</span>
                            </div>
                            <div style="margin-top:10px; padding:8px 12px; background:rgba(83,83,83,0.15); border-radius:6px; font-size:12px; color:{SPOTIFY_LIGHT_GRAY}; font-style:italic;">
                                {s['example']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Ground truth convergence diagram
    st.markdown("### Label Confidence Model")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "Ground truth confidence increases when multiple independent sources agree on a classification. "
        "A stream confirmed by both a heuristic rule AND an analyst decision is a stronger label than either alone."
        "</p>",
        unsafe_allow_html=True,
    )

    fig_convergence = go.Figure()

    convergence_data = {
        "Single source\n(analyst only)": 0.72,
        "Two sources\n(analyst + heuristic)": 0.88,
        "Three sources\n(analyst + heuristic\n+ behavioral)": 0.94,
        "Confirmed\ntakedown": 0.99,
    }

    colors = [COLOR_WARNING, COLOR_INFO, SPOTIFY_GREEN, SPOTIFY_GREEN]

    fig_convergence.add_trace(go.Bar(
        x=list(convergence_data.keys()),
        y=list(convergence_data.values()),
        marker_color=colors,
        text=[f"{v:.0%}" for v in convergence_data.values()],
        textposition="auto",
        textfont=dict(color=SPOTIFY_WHITE, size=14, family="Inter"),
    ))

    apply_spotify_style(fig_convergence, height=400)
    fig_convergence.update_layout(
        title="Estimated Label Confidence by Source Convergence",
        yaxis_title="Label Confidence",
        yaxis=dict(range=[0, 1.05], tickformat=".0%"),
        bargap=0.35,
    )
    st.plotly_chart(fig_convergence, use_container_width=True)

    # Spotify's data pipeline architecture
    st.markdown("### StreamShield Data Architecture (Spotify Stack)")
    arch_html = f"""
    <html><head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background: #121212; color: #fff; margin: 0; padding: 16px; }}
    </style>
    </head><body>
    <div style="display:grid; grid-template-columns:1fr auto 1fr auto 1fr; gap:8px; align-items:center; text-align:center;">
        <div style="background:rgba(80,155,245,0.15); border:1px solid #509BF5; border-radius:8px; padding:14px;">
            <div style="color:#509BF5; font-weight:700; font-size:13px;">EVENT INGESTION</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">Cloud Pub/Sub</div>
            <div style="color:#535353; font-size:10px;">~8M events/sec</div>
        </div>
        <div style="color:#535353; font-size:20px;">&#8594;</div>
        <div style="background:rgba(29,185,84,0.15); border:1px solid #1DB954; border-radius:8px; padding:14px;">
            <div style="color:#1DB954; font-weight:700; font-size:13px;">ML SCORING</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">Kubeflow + TFX on GKE</div>
            <div style="color:#535353; font-size:10px;">Model served via Salem</div>
        </div>
        <div style="color:#535353; font-size:20px;">&#8594;</div>
        <div style="background:rgba(245,155,35,0.15); border:1px solid #F59B23; border-radius:8px; padding:14px;">
            <div style="color:#F59B23; font-weight:700; font-size:13px;">CLASSIFICATION</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">Cloud Dataflow</div>
            <div style="color:#535353; font-size:10px;">Quarantine / Review / Pass</div>
        </div>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-top:20px;">
        <div style="background:rgba(175,40,150,0.15); border:1px solid #AF2896; border-radius:8px; padding:14px; text-align:center;">
            <div style="color:#AF2896; font-weight:700; font-size:13px;">HUMAN REVIEW</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">Review Console + LLM</div>
            <div style="color:#535353; font-size:10px;">Signal Card (proposed)</div>
        </div>
        <div style="background:rgba(232,17,91,0.15); border:1px solid #E8115B; border-radius:8px; padding:14px; text-align:center;">
            <div style="color:#E8115B; font-weight:700; font-size:13px;">QUARANTINE</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">Bigtable + Cloud Storage</div>
            <div style="color:#535353; font-size:10px;">90-day hold</div>
        </div>
        <div style="background:rgba(80,155,245,0.15); border:1px solid #509BF5; border-radius:8px; padding:14px; text-align:center;">
            <div style="color:#509BF5; font-weight:700; font-size:13px;">DOWNSTREAM</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">BigQuery &rarr; Finance / Ads / Analytics</div>
            <div style="color:#535353; font-size:10px;">Treated as authoritative</div>
        </div>
    </div>
    <div style="display:grid; grid-template-columns:1fr; gap:16px; margin-top:20px;">
        <div style="background:rgba(29,185,84,0.10); border:1px dashed #1DB954; border-radius:8px; padding:14px; text-align:center;">
            <div style="color:#1DB954; font-weight:700; font-size:13px;">GROUND TRUTH FEEDBACK LOOP</div>
            <div style="color:#B3B3B3; font-size:11px; margin-top:4px;">
                Confirmed takedowns + Analyst decisions + Appeal outcomes + Distributor penalties + Heuristic rules + Behavioral decay
                &rarr; BigQuery labeled dataset &rarr; Kubeflow retraining pipeline
            </div>
            <div style="color:#E8115B; font-size:10px; margin-top:4px; font-weight:600;">Gap: No automated trigger. Retraining is manual, planned next quarter.</div>
        </div>
    </div>
    </body></html>
    """
    components.html(arch_html, height=340, scrolling=False)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Production vs Audit View
    st.markdown("### Production View vs. Audit View")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "A critical architectural distinction: the production system and the audit system see different data. "
        "StreamShield classifies streams in real-time with <strong>no access to ground truth</strong>. "
        "Ground truth is assembled retroactively from multiple sources and is only available to the audit layer."
        "</p>",
        unsafe_allow_html=True,
    )

    prod_col, audit_col = st.columns(2)

    # Load production data
    from pathlib import Path
    prod_path = Path(__file__).parent.parent / "data" / "cached" / "streaming_events_production.csv"
    prod_df = pd.read_csv(prod_path) if prod_path.exists() else None

    with prod_col:
        prod_columns = list(prod_df.columns) if prod_df is not None else [c for c in events_df.columns if c != "is_actually_fraudulent"]
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {COLOR_WARNING};">
                <div style="color:{COLOR_WARNING}; font-size:14px; font-weight:700; margin-bottom:12px;">Production System (Real-Time)</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6; margin-bottom:16px;">
                    What StreamShield sees when classifying a stream. No ground truth — the system does not know
                    if a stream is actually fraudulent. It only has the ML model's score and the metadata signals.
                </div>
                <div style="color:{SPOTIFY_WHITE}; font-size:12px; font-family:monospace; background:#0a0a0a; border-radius:6px; padding:12px; line-height:1.8;">
                    {"<br>".join([f'<span style="color:{SPOTIFY_GREEN};">&#10003;</span> {c}' for c in prod_columns])}
                    <br><span style="color:{COLOR_DANGER};">&#10007;</span> <span style="color:{COLOR_DANGER}; text-decoration:line-through;">is_actually_fraudulent</span>
                    <span style="color:{SPOTIFY_GRAY};"> (not available at classification time)</span>
                </div>
                <div style="margin-top:12px; color:{SPOTIFY_GRAY}; font-size:11px;">
                    {len(prod_columns)} features available | Ground truth: NOT AVAILABLE
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with audit_col:
        audit_columns = list(events_df.columns)
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {SPOTIFY_GREEN};">
                <div style="color:{SPOTIFY_GREEN}; font-size:14px; font-weight:700; margin-bottom:12px;">Audit System (Retrospective)</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6; margin-bottom:16px;">
                    What IAR sees when evaluating model performance. Includes ground truth labels assembled
                    from analyst decisions, appeal outcomes, confirmed takedowns, and behavioral analysis.
                </div>
                <div style="color:{SPOTIFY_WHITE}; font-size:12px; font-family:monospace; background:#0a0a0a; border-radius:6px; padding:12px; line-height:1.8;">
                    {"<br>".join([f'<span style="color:{SPOTIFY_GREEN};">&#10003;</span> {c}' for c in audit_columns])}
                </div>
                <div style="margin-top:12px; color:{SPOTIFY_GRAY}; font-size:11px;">
                    {len(audit_columns)} features available | Ground truth: AVAILABLE (retrospective)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); margin-top:16px;">
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                <strong style="color:{COLOR_INFO};">Why this distinction matters for the audit:</strong><br>
                <span style="color:{SPOTIFY_LIGHT_GRAY};">
                Precision, recall, F1, and ROC curves all require ground truth. These metrics can only be computed in the audit view —
                meaning they are retrospective evaluations, not real-time monitoring.
                The production system can only monitor <strong>proxy metrics</strong>: quarantine rates, score distributions, PSI drift scores.
                When those proxies shift, it signals that ground truth validation is needed — but the production system cannot
                self-diagnose whether it is making correct decisions. This is why continuous audit monitoring is essential,
                and why the drift detection alerts in our tool are based on distributional metrics (PSI) that don't require labels,
                while the accuracy assessments in the threshold analyzer use the audit dataset with assembled ground truth.
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Synthetic data transparency
    st.markdown("### Synthetic Data Transparency")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "This prototype uses synthetic data with a known ground truth column (<code>is_actually_fraudulent</code>). "
        "In production, ground truth would be assembled from the sources above with varying confidence levels."
        "</p>",
        unsafe_allow_html=True,
    )

    synth_col1, synth_col2, synth_col3 = st.columns(3)

    with synth_col1:
        total = len(events_df)
        fraud = events_df["is_actually_fraudulent"].sum()
        st.markdown(metric_card("Total Synthetic Streams", f"{total:,}"), unsafe_allow_html=True)
    with synth_col2:
        st.markdown(metric_card("Ground Truth Fraud Rate", f"{fraud/total:.1%}"), unsafe_allow_html=True)
    with synth_col3:
        new_cat = events_df["is_new_catalog"].sum()
        st.markdown(metric_card("New Catalog Streams", f"{new_cat:,}"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Embedded patterns table
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2);">
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:700; margin-bottom:12px;">Patterns Embedded in Synthetic Data</div>
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <tr style="border-bottom:1px solid rgba(83,83,83,0.3);">
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0; width:30%;">PATTERN</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0; width:40%;">WHAT IT SIMULATES</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0; width:30%;">SOURCE JUSTIFICATION</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
                    <td style="color:{SPOTIFY_WHITE}; padding:10px 0;">Precision drops after day 120</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Model drift post-catalog acquisition</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Case study: "catalog acquisition changed content distribution"</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
                    <td style="color:{SPOTIFY_WHITE}; padding:10px 0;">New catalog FP rate 6.6x higher</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Model misclassifies unfamiliar content</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Research: distribution shift → elevated false positives on new data</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
                    <td style="color:{SPOTIFY_WHITE}; padding:10px 0;">3 analysts agree >97%, <80s/case</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Automation bias / rubber-stamping</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Case study: "92% agreement rate"; automation bias research (Springer 2025)</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
                    <td style="color:{SPOTIFY_WHITE}; padding:10px 0;">Indie appeals: 38 days vs major: 11 days</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Process inequity by artist size</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Case study: "appeal process took 6 weeks"; industry reports on indie vs major treatment</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
                    <td style="color:{SPOTIFY_WHITE}; padding:10px 0;">New catalog fraud rate: 3% vs existing: 7%</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">New catalog is mostly legitimate content being misclassified</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Logical: acquired catalogs come from vetted labels, not fraud operations</td>
                </tr>
                <tr>
                    <td style="color:{SPOTIFY_WHITE}; padding:10px 0;">Viral campaign cluster (days 135-145)</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Legitimate viral activity incorrectly flagged</td>
                    <td style="color:{SPOTIFY_LIGHT_GRAY}; padding:10px 0;">Case study: "viral marketing campaign incorrectly quarantined"</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Audit observation
    st.markdown("---")
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(80,155,245,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:24px; border-left:4px solid {COLOR_INFO};">
            <div style="color:{COLOR_INFO}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Observation: Ground Truth Label Governance</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; line-height:1.6;">
                <strong>Condition:</strong> The ML model was trained on historical data labeled by the Fraud team.
                Based on the information provided, we did not identify documentation of the labeling methodology,
                inter-rater reliability metrics, label quality assurance procedures, or a process for updating labels
                as new information emerges (e.g., when appeal outcomes reverse prior classifications).<br><br>
                <strong>Criteria:</strong> NIST AI RMF and ISACA AI governance guidance emphasize that data quality —
                including the accuracy and consistency of training labels — is foundational to model reliability.
                Leading practices include documented labeling criteria, inter-rater agreement measurement, periodic label audits,
                and feedback loops that incorporate new ground truth sources (appeal outcomes, confirmed takedowns) into the training dataset.<br><br>
                <strong>Cause:</strong> Label governance was not identified as a formal control within the StreamShield framework.
                The ground truth dataset appears to be assembled from multiple sources (analyst decisions, confirmed cases, heuristic rules)
                but the process for reconciling conflicting labels, weighting confidence levels, and validating label accuracy is not documented.<br><br>
                <strong>Effect:</strong> If training labels contain systematic biases — for example, if the Fraud team historically
                labeled certain genres or regional content patterns as fraud more aggressively — the model would inherit and amplify those biases.
                This could contribute to the observed pattern where newly acquired catalog content in specific genres is disproportionately flagged.
                Without label quality metrics, the precision and recall figures reported by the model may themselves be unreliable.<br><br>
                <strong>Recommendation:</strong> (1) Document the ground truth labeling methodology, including criteria, sources, and confidence weighting.
                (2) Measure inter-rater reliability for analyst-generated labels.
                (3) Establish a feedback loop that automatically incorporates appeal outcomes and confirmed takedown data into the retraining dataset.
                (4) Conduct periodic label audits — sample labeled data and independently validate classifications against raw evidence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
