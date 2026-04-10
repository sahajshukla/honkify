"""Audit Journey — The WOW moment page.

Combines three interactive experiences:
1. Scenario Mode: Guided walkthrough of a complete audit lifecycle
2. Financial Impact Calculator: Live dollar counter showing the cost of inaction
3. What-If Simulator: Toggle controls to see projected impact
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY,
)


# Impact constants — illustrative estimates derived from the case study brief
# and publicly reported Spotify scale data. Used for financial materiality
# analysis; actual values would come from Finance during a real engagement.
STREAMS_PER_DAY = 18_000_000  # Spotify's scale, proportional
AVG_ROYALTY_PER_STREAM = 0.004  # $0.003-$0.005 (industry benchmark)
PRE_ACQUISITION_FPR = 0.028  # 2.8%
POST_ACQUISITION_FPR = 0.085  # 8.5%
EXCESS_FP_RATE = POST_ACQUISITION_FPR - PRE_ACQUISITION_FPR
DAYS_SINCE_ACQUISITION = 120  # 4 months
DAILY_EXCESS_FPS = int(STREAMS_PER_DAY * EXCESS_FP_RATE)  # excess legitimate streams being quarantined
DAILY_ROYALTY_HARM = DAILY_EXCESS_FPS * AVG_ROYALTY_PER_STREAM
TOTAL_HARM_TO_DATE = DAILY_ROYALTY_HARM * DAYS_SINCE_ACQUISITION
ANNUAL_PROJECTED_HARM = DAILY_ROYALTY_HARM * 365


def render():
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(29,185,84,0.12) 0%, rgba(232,17,91,0.08) 100%); border-radius:12px; padding:28px 32px; margin-bottom:24px; border:1px solid rgba(83,83,83,0.3);">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="{SPOTIFY_GREEN}">
                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                </svg>
                <span style="font-size:28px; font-weight:800; color:{SPOTIFY_WHITE}; letter-spacing:-0.5px;">The Audit Journey</span>
            </div>
            <p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; max-width:900px; line-height:1.6; margin:0 0 8px 0;">
                The full lifecycle of an AI audit: detect the drift, quantify the harm, project the residual risk, contrast the current vs. proposed process, and operate continuous controls monitoring. Demonstrates how IAR supports an AI system end-to-end.
            </p>
            <div style="color:{SPOTIFY_GRAY}; font-size:12px; margin-top:8px;">
                Regulatory framing: Spotify is a VLOP under the EU Digital Services Act. StreamShield falls within DSA Article 34 (systemic risk assessment), Article 35 (mitigation measures), and Article 37 (independent third-party audit) scope.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Create tabs for the experiences
    tab_scenario, tab_impact, tab_whatif, tab_maturity, tab_ccm = st.tabs([
        "Scenario Walkthrough",
        "Financial Impact",
        "Residual Risk Simulator",
        "Process Maturity (Before/After)",
        "Continuous Controls Monitoring",
    ])

    with tab_scenario:
        _render_scenario()

    with tab_impact:
        _render_impact_calculator()

    with tab_whatif:
        _render_whatif_simulator()

    with tab_maturity:
        _render_process_maturity()

    with tab_ccm:
        _render_continuous_controls_monitoring()


def _render_scenario():
    """Scenario walkthrough — multiple guided journeys through different audit scenarios."""

    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:20px; font-weight:700; margin-bottom:6px;">Scenario Walkthroughs</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "Six scenarios demonstrating different audit situations. Each one tells a complete story from initial event through resolution, showing how the controls operate in practice."
        "</p>",
        unsafe_allow_html=True,
    )

    scenario_choice = st.selectbox(
        "Select a scenario to walk through",
        options=[
            "A. Catalog Drift (Current State Failure)",
            "B. Sophisticated Fraud Evasion (Defense in Depth)",
            "C. Data Poisoning Attack (Adversarial AI Risk)",
            "D. DSA Regulatory Inquiry (Article 37 Walkthrough)",
            "E. New Catalog Onboarding (Success Path After Controls)",
            "F. Analyst Bias Detection (Continuous Monitoring in Action)",
        ],
        index=0,
    )

    st.markdown("---")

    if scenario_choice.startswith("A."):
        _render_scenario_a_catalog_drift()
    elif scenario_choice.startswith("B."):
        _render_scenario_b_fraud_evasion()
    elif scenario_choice.startswith("C."):
        _render_scenario_c_data_poisoning()
    elif scenario_choice.startswith("D."):
        _render_scenario_d_dsa_inquiry()
    elif scenario_choice.startswith("E."):
        _render_scenario_e_success_path()
    elif scenario_choice.startswith("F."):
        _render_scenario_f_bias_detection()


def _render_scenario_a_catalog_drift():
    """Scenario A: The original catalog drift scenario — current state failure."""

    st.markdown(
        f'<div style="color:{COLOR_DANGER}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:4px;">Scenario A &middot; Current State Failure</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:8px;">Catalog Acquisition Drift</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "A regional catalog acquisition causes the model to misclassify legitimate content. The drift goes undetected for 4 months because no continuous monitoring exists. An indie label files a complaint, the appeal takes 38 days, the label goes public, and IAR is engaged. "
        "<strong style='color:" + SPOTIFY_WHITE + ";'>Use the slider to advance through the timeline.</strong>"
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:10px 14px; border-radius:6px; margin-bottom:16px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">DSA ANGLE:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> Spotify failed to perform proportionate Article 35 mitigation when introducing new content into the AI system. Article 34 systemic risk assessment did not detect this because no continuous mechanism existed.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Timeline slider
    day = st.slider(
        "Timeline (days since catalog acquisition)",
        min_value=0,
        max_value=170,
        value=0,
        step=5,
        help="Drag to advance through the scenario",
    )

    # Compute state based on day
    scenario_state = _get_scenario_state(day)

    # Status card
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:12px; padding:24px 28px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {scenario_state['color']}; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="background:rgba(255,255,255,0.06); color:{scenario_state['color']}; padding:4px 14px; border-radius:500px; font-size:11px; font-weight:700; letter-spacing:1px;">DAY {day} &middot; {scenario_state['phase']}</span>
                <span style="color:{SPOTIFY_GRAY}; font-size:12px;">{scenario_state['date']}</span>
            </div>
            <div style="color:{SPOTIFY_WHITE}; font-size:22px; font-weight:700; margin-bottom:8px;">{scenario_state['title']}</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; line-height:1.6;">{scenario_state['description']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metrics strip
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _metric_box(
            "Model Precision",
            f"{scenario_state['precision']:.1%}",
            delta=scenario_state['precision_delta'],
            delta_color="bad" if scenario_state['precision_delta'] < 0 else "good",
        )
    with c2:
        _metric_box(
            "False Positive Rate",
            f"{scenario_state['fpr']:.1%}",
            delta=scenario_state['fpr_delta'],
            delta_color="bad" if scenario_state['fpr_delta'] > 0 else "good",
        )
    with c3:
        _metric_box(
            "Daily Royalty Harm",
            f"${scenario_state['daily_harm']:,.0f}",
            delta=None,
        )
    with c4:
        _metric_box(
            "Affected Artists",
            f"{scenario_state['affected_artists']:,}",
            delta=None,
        )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Timeline visualization
    st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:12px;">Timeline</div>', unsafe_allow_html=True)
    _render_timeline(day)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Detail cards for this phase
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; border:1px solid rgba(83,83,83,0.2);">
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700; margin-bottom:10px;">What the auditor does at this moment</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; line-height:1.7;">{scenario_state['auditor_action']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if scenario_state.get('tool_used'):
        st.markdown(
            f"""
            <div style="margin-top:12px; background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; border:1px solid rgba(29,185,84,0.25); border-left:3px solid {SPOTIFY_GREEN};">
                <div style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Tool Used in Our Prototype</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:14px;">{scenario_state['tool_used']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _get_scenario_state(day):
    """Return the state of the scenario at a given day."""

    base_date = datetime(2025, 12, 9)
    current_date = base_date + timedelta(days=day)
    date_str = current_date.strftime("%b %d, %Y")

    if day == 0:
        return {
            "phase": "Baseline",
            "color": COLOR_INFO,
            "title": "Day 0: Catalog Acquisition Announced",
            "description": "Spotify announces the acquisition of a regional music catalog (50,000 tracks, 300 artists, primarily Latin, Classical, and Regional Folk genres). The new content is onboarded to the platform. No adjustments are made to StreamShield — the model continues to run with existing thresholds trained on pre-acquisition content.",
            "date": date_str,
            "precision": 0.940,
            "precision_delta": 0.0,
            "fpr": 0.028,
            "fpr_delta": 0.0,
            "daily_harm": 0,
            "affected_artists": 0,
            "auditor_action": "Catalog acquisition is a known drift trigger. If continuous monitoring and catalog onboarding protocols existed, this would automatically trigger a model evaluation. Currently, neither exists — the acquisition proceeds without IAR visibility.",
            "tool_used": None,
        }
    elif day <= 30:
        return {
            "phase": "Drift Begins",
            "color": COLOR_WARNING,
            "title": f"Day {day}: Model Drift Undetected",
            "description": "New catalog content begins flowing through StreamShield. The model, trained on pre-acquisition data, starts misclassifying legitimate new catalog streams as fraudulent. New Latin, Classical, and Regional Folk content is flagged at elevated rates. No alert fires because there is no continuous monitoring.",
            "date": date_str,
            "precision": 0.940 - (0.03 * day / 30),
            "precision_delta": -(3.0 * day / 30),
            "fpr": 0.028 + (0.015 * day / 30),
            "fpr_delta": (1.5 * day / 30),
            "daily_harm": (DAILY_ROYALTY_HARM * 0.3 * day / 30),
            "affected_artists": int(50 * day / 30),
            "auditor_action": "Without continuous monitoring, this period passes invisibly. The Fraud team sees quarantine rates rising but attributes it to 'more fraud.' The only metric being watched is output (quarantine count), not model health (precision, PSI).",
            "tool_used": None,
        }
    elif day <= 60:
        return {
            "phase": "Drift Confirmed",
            "color": COLOR_DANGER,
            "title": f"Day {day}: Drift Reaches Critical",
            "description": "PSI would now exceed 0.20 if anyone were measuring it. Precision has dropped to approximately 87%. False positive rate is approximately double the pre-acquisition baseline. New catalog content is being flagged at 3-4x the rate of existing content. Legitimate artists are losing royalties daily.",
            "date": date_str,
            "precision": 0.910 - (0.03 * (day - 30) / 30),
            "precision_delta": -3.0 - (3.0 * (day - 30) / 30),
            "fpr": 0.043 + (0.020 * (day - 30) / 30),
            "fpr_delta": 1.5 + (2.0 * (day - 30) / 30),
            "daily_harm": (DAILY_ROYALTY_HARM * 0.3 + DAILY_ROYALTY_HARM * 0.4 * (day - 30) / 30),
            "affected_artists": int(50 + 150 * (day - 30) / 30),
            "auditor_action": "In a well-monitored system, the Drift Monitor would have fired PSI alerts 30 days ago. IAR would have been notified. Fraud team would have initiated expedited retraining. None of this is happening because the continuous monitoring control does not exist.",
            "tool_used": "Our Drift Monitor page would have detected this at Day ~15 based on PSI trends.",
        }
    elif day <= 90:
        return {
            "phase": "Artist Dispute",
            "color": COLOR_DANGER,
            "title": f"Day {day}: Indie Label Files Complaint",
            "description": "An indie label notices that a viral marketing campaign for one of their Latin artists has been systematically quarantined. They file a formal appeal. The appeal enters the Content & Rights queue with a 38-day resolution time. During these 38 days, the artist loses streaming momentum and continues to receive zero royalties. The label begins contacting music press.",
            "date": date_str,
            "precision": 0.880 - (0.01 * (day - 60) / 30),
            "precision_delta": -6.5 - (1.5 * (day - 60) / 30),
            "fpr": 0.063 + (0.010 * (day - 60) / 30),
            "fpr_delta": 3.5 + (1.0 * (day - 60) / 30),
            "daily_harm": (DAILY_ROYALTY_HARM * 0.7 + DAILY_ROYALTY_HARM * 0.2 * (day - 60) / 30),
            "affected_artists": int(200 + 200 * (day - 60) / 30),
            "auditor_action": "This is the moment the organization becomes aware there is a problem. But even now, the awareness is narrow — the Fraud team sees 'one label complaining' rather than 'systematic drift affecting hundreds of artists.' Without ground truth coverage across passed streams, the scale of the issue remains hidden.",
            "tool_used": "The Bias Detector and False Positive Analysis in our tool would have flagged this pattern 45 days earlier.",
        }
    elif day <= 120:
        return {
            "phase": "Public Dispute",
            "color": COLOR_DANGER,
            "title": f"Day {day}: Label Goes Public",
            "description": "After 38+ days without resolution, the label publishes their complaint on social media and music industry press. Other indie artists begin questioning whether Spotify's AI is trustworthy. Reputational damage begins to compound. The Head of Fraud realizes this is no longer contained — IAR is called in.",
            "date": date_str,
            "precision": 0.870,
            "precision_delta": -7.0,
            "fpr": 0.073,
            "fpr_delta": 4.5,
            "daily_harm": DAILY_ROYALTY_HARM * 0.9,
            "affected_artists": 400,
            "auditor_action": "This is where the case study begins. The Head of Fraud has approached IAR. A leadership review is upcoming. We are now performing the engagement. Everything up to this point could have been prevented by continuous monitoring.",
            "tool_used": "This is the moment our prototype becomes valuable — both to demonstrate what happened and to prevent it from happening again.",
        }
    elif day <= 135:
        return {
            "phase": "IAR Engagement",
            "color": COLOR_INFO,
            "title": f"Day {day}: IAR Engagement Begins",
            "description": "IAR launches the engagement. The advisory memo is delivered within 2 weeks. The Drift Monitor page shows the full drift history. The Threshold Lab demonstrates sensitivity to business stakeholders. The Signal Card prototype demonstrates the proposed human review workflow. Test procedures T1 through T11 run in parallel.",
            "date": date_str,
            "precision": 0.870,
            "precision_delta": -7.0,
            "fpr": 0.073,
            "fpr_delta": 4.5,
            "daily_harm": DAILY_ROYALTY_HARM * 0.9,
            "affected_artists": 450,
            "auditor_action": "During this phase, the prototype is used as the primary analytical tool. Drift is documented. Thresholds are sensitivity-tested. Analyst patterns are examined. Findings are drafted. Management responses are obtained.",
            "tool_used": "Drift Monitor, Threshold Lab, Review Integrity (Bias Analysis + Signal Card), Data Observatory, AI Audit Agent — every module is used in this phase.",
        }
    elif day <= 150:
        return {
            "phase": "Remediation",
            "color": COLOR_WARNING,
            "title": f"Day {day}: Controls Being Implemented",
            "description": "Based on the audit findings, management implements expedited remediation. The model is retrained on post-acquisition data. PSI monitoring is deployed. The Signal Confirmation Card is piloted with a subset of analysts. The Catalog Onboarding Protocol is drafted. Appeal SLA is established at 10 business days.",
            "date": date_str,
            "precision": 0.870 + (0.05 * (day - 135) / 15),
            "precision_delta": -7.0 + (5.0 * (day - 135) / 15),
            "fpr": 0.073 - (0.030 * (day - 135) / 15),
            "fpr_delta": 4.5 - (3.0 * (day - 135) / 15),
            "daily_harm": DAILY_ROYALTY_HARM * (0.9 - 0.6 * (day - 135) / 15),
            "affected_artists": 480,
            "auditor_action": "Remediation is happening in parallel with continued audit testing. The prototype is being handed off as an ongoing monitoring capability. IAR transitions from periodic engagement to continuous assurance for this system.",
            "tool_used": "The prototype becomes permanent IAR infrastructure. Drift alerts now fire proactively. Analyst bias is monitored daily.",
        }
    else:
        return {
            "phase": "Stable State",
            "color": SPOTIFY_GREEN,
            "title": f"Day {day}: Improved Operating State",
            "description": "All critical controls are in place. Model precision has recovered to 92%. False positive rate is back near baseline. PSI is green. No new label disputes. IAR continues continuous monitoring. The catalog onboarding protocol ensures this scenario cannot recur with the next acquisition.",
            "date": date_str,
            "precision": 0.920,
            "precision_delta": -2.0,
            "fpr": 0.033,
            "fpr_delta": 0.5,
            "daily_harm": DAILY_ROYALTY_HARM * 0.2,
            "affected_artists": 500,
            "auditor_action": "The engagement has transitioned to steady-state monitoring. The prototype continues to run against live BigQuery data. IAR has visibility into model health, analyst independence, and appeal process metrics on an ongoing basis.",
            "tool_used": "The prototype is now a permanent part of Spotify's IAR function for AI system monitoring.",
        }


def _metric_box(label, value, delta=None, delta_color="normal"):
    """Render a metric box with optional delta indicator."""
    delta_html = ""
    if delta is not None:
        color = SPOTIFY_GREEN if delta_color == "good" else COLOR_DANGER if delta_color == "bad" else SPOTIFY_LIGHT_GRAY
        arrow = "&#9650;" if delta > 0 else "&#9660;" if delta < 0 else "&#8212;"
        delta_html = f'<div style="color:{color}; font-size:13px; margin-top:4px;">{arrow} {abs(delta):.1f}pp</div>'

    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 22px; border:1px solid rgba(83,83,83,0.2);">
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">{label}</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:24px; font-weight:800; line-height:1.1;">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_timeline(current_day):
    """Render a timeline showing scenario phases."""
    phases = [
        {"day": 0, "label": "Catalog\nAcquired", "color": COLOR_INFO},
        {"day": 15, "label": "Drift\nStarts", "color": COLOR_WARNING},
        {"day": 45, "label": "Drift\nCritical", "color": COLOR_DANGER},
        {"day": 75, "label": "Artist\nComplaint", "color": COLOR_DANGER},
        {"day": 105, "label": "Public\nDispute", "color": COLOR_DANGER},
        {"day": 120, "label": "IAR\nEngagement", "color": COLOR_INFO},
        {"day": 140, "label": "Remediation", "color": COLOR_WARNING},
        {"day": 165, "label": "Stable\nState", "color": SPOTIFY_GREEN},
    ]

    fig = go.Figure()

    # Background line
    fig.add_shape(
        type="line", x0=0, x1=170, y0=0, y1=0,
        line=dict(color="rgba(83,83,83,0.4)", width=2),
    )

    # Progress line
    fig.add_shape(
        type="line", x0=0, x1=current_day, y0=0, y1=0,
        line=dict(color=SPOTIFY_GREEN, width=4),
    )

    # Phase markers
    for phase in phases:
        is_past = phase["day"] <= current_day
        color = phase["color"] if is_past else "rgba(83,83,83,0.5)"
        size = 18 if phase["day"] <= current_day else 12

        fig.add_trace(go.Scatter(
            x=[phase["day"]],
            y=[0],
            mode="markers+text",
            marker=dict(size=size, color=color, line=dict(color=SPOTIFY_WHITE, width=2)),
            text=[phase["label"]],
            textposition="top center",
            textfont=dict(size=10, color=SPOTIFY_LIGHT_GRAY if not is_past else SPOTIFY_WHITE),
            showlegend=False,
            hovertemplate=f"Day {phase['day']}: {phase['label'].replace(chr(10),' ')}<extra></extra>",
        ))

    # Current position marker
    fig.add_trace(go.Scatter(
        x=[current_day],
        y=[0],
        mode="markers",
        marker=dict(size=24, color=SPOTIFY_GREEN, symbol="diamond", line=dict(color=SPOTIFY_WHITE, width=2)),
        showlegend=False,
        hovertemplate=f"Day {current_day} (current)<extra></extra>",
    ))

    apply_spotify_style(fig, height=180)
    fig.update_layout(
        xaxis=dict(range=[-5, 180], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[-0.5, 1.5], showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_impact_calculator():
    """Financial impact calculator with live ticker."""

    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:20px; font-weight:700; margin-bottom:6px;">Estimated Financial Impact</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:12px;">'
        "Indicative financial impact of the current drift, based on synthetic data and industry benchmark assumptions. "
        "These figures illustrate the potential scale of the issue — they are estimates, not validated production figures. "
        "Actual financial impact would require validation against real Spotify data and royalty calculations."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">ESTIMATE DISCLAIMER:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> Calculations use proportional assumptions and industry-standard royalty rates ($0.003-$0.005 per stream). These are illustrative figures to demonstrate the magnitude of the issue, not audited financial impact statements.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Headline metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(232,17,91,0.12), {SPOTIFY_CARD_BG}); border-radius:12px; padding:24px 28px; border:1px solid rgba(232,17,91,0.3);">
                <div style="color:{COLOR_DANGER}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Daily Royalty Harm</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:34px; font-weight:800; line-height:1.1;">${DAILY_ROYALTY_HARM:,.0f}</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:6px;">Legitimate royalties withheld per day due to drift</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(255,100,55,0.12), {SPOTIFY_CARD_BG}); border-radius:12px; padding:24px 28px; border:1px solid rgba(255,100,55,0.3);">
                <div style="color:#FF6437; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Cumulative Since Acquisition</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:34px; font-weight:800; line-height:1.1;">${TOTAL_HARM_TO_DATE:,.0f}</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:6px;">{DAYS_SINCE_ACQUISITION} days of undetected drift</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(245,155,35,0.12), {SPOTIFY_CARD_BG}); border-radius:12px; padding:24px 28px; border:1px solid rgba(245,155,35,0.3);">
                <div style="color:{COLOR_WARNING}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Annual Projection (No Fix)</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:34px; font-weight:800; line-height:1.1;">${ANNUAL_PROJECTED_HARM:,.0f}</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:6px;">If drift continues unaddressed for 12 months</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Breakdown by component
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:14px;">How We Calculated This</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; border:1px solid rgba(83,83,83,0.2); font-family:monospace;">
            <table style="width:100%; font-size:13px; color:{SPOTIFY_LIGHT_GRAY};">
                <tr style="border-bottom:1px solid rgba(83,83,83,0.3);">
                    <td style="padding:8px 0;">Streams processed per day</td>
                    <td style="text-align:right; color:{SPOTIFY_WHITE};">{STREAMS_PER_DAY:,}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Pre-acquisition false positive rate</td>
                    <td style="text-align:right; color:{SPOTIFY_GREEN};">{PRE_ACQUISITION_FPR:.1%}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Post-acquisition false positive rate</td>
                    <td style="text-align:right; color:{COLOR_DANGER};">{POST_ACQUISITION_FPR:.1%}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Excess false positive rate (drift)</td>
                    <td style="text-align:right; color:{COLOR_WARNING};">{EXCESS_FP_RATE:.1%}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Additional legitimate streams quarantined per day</td>
                    <td style="text-align:right; color:{SPOTIFY_WHITE};">{DAILY_EXCESS_FPS:,}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Average royalty per stream</td>
                    <td style="text-align:right; color:{SPOTIFY_WHITE};">${AVG_ROYALTY_PER_STREAM:.4f}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Daily financial harm to legitimate artists</td>
                    <td style="text-align:right; color:{COLOR_DANGER}; font-weight:700;">${DAILY_ROYALTY_HARM:,.0f}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(83,83,83,0.2);">
                    <td style="padding:8px 0;">Days since catalog acquisition (undetected)</td>
                    <td style="text-align:right; color:{SPOTIFY_WHITE};">{DAYS_SINCE_ACQUISITION}</td>
                </tr>
                <tr>
                    <td style="padding:12px 0; font-weight:700; color:{SPOTIFY_WHITE};">Total harm to date</td>
                    <td style="text-align:right; color:{COLOR_DANGER}; font-weight:800; font-size:16px;">${TOTAL_HARM_TO_DATE:,.0f}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Indirect costs
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:14px;">Indirect Costs Not Quantified Above</div>',
        unsafe_allow_html=True,
    )

    indirect_cols = st.columns(3)
    indirect = [
        ("Reputational Damage", "Public disputes erode trust with the creator community. A single viral complaint can influence thousands of artists' platform choices.", COLOR_DANGER),
        ("Legal Exposure", "Withholding royalties from legitimate artists creates potential breach-of-contract claims and GDPR Article 22 exposure for automated decisions.", COLOR_WARNING),
        ("Chart & Recommendation Impact", "Lost chart momentum and reduced algorithmic recommendation cannot be recovered even after appeal. Long-term revenue impact extends beyond the direct royalty harm.", COLOR_INFO),
    ]
    for i, (title, desc, color) in enumerate(indirect):
        with indirect_cols[i]:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 20px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {color}; min-height:180px;">
                    <div style="color:{color}; font-size:13px; font-weight:700; margin-bottom:8px;">{title}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; line-height:1.6;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_whatif_simulator():
    """Residual Risk Simulator — toggle controls to see projected RISK REDUCTION (not elimination)."""

    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:20px; font-weight:700; margin-bottom:6px;">Residual Risk Simulator</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:20px;">'
        "Toggle the proposed controls ON to see how each one reduces risk. Important: no control eliminates risk completely. "
        "Every implementation leaves residual risk. The objective is to reduce inherent risk to a level that is acceptable to management — "
        "not to claim zero exposure."
        "</p>",
        unsafe_allow_html=True,
    )

    # Important framing card
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(80,155,245,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:16px 20px; border-left:4px solid {COLOR_INFO}; margin-bottom:20px;">
            <div style="color:{COLOR_INFO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Audit Principle</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                Internal audit cannot guarantee elimination of risk. Controls reduce the likelihood and impact of risk events, but residual risk always remains. The figures below represent
                <strong style="color:{SPOTIFY_WHITE};">estimated reductions based on industry benchmarks and our analysis</strong>, not guarantees. Actual results would depend on implementation quality, organizational readiness, and external factors. Management should accept the residual risk explicitly.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:14px;">Toggle Proposed Controls</div>',
        unsafe_allow_html=True,
    )

    # Control toggles with realistic estimated reductions
    # Reductions are estimates based on the specific risk each control addresses
    # No control achieves 100% — residual risk always remains
    controls = [
        {
            "id": "psi",
            "label": "Automated PSI monitoring + event-triggered evaluation",
            "gap": "Gap 1",
            "estimated_reduction": 0.20,
            "description": "Estimated 15-25% reduction in undetected drift duration. Does not prevent drift, but reduces detection latency from months to hours.",
            "residual_risk": "Drift may still occur between PSI checks. Some drift types (concept drift not visible in input distributions) may evade PSI detection.",
        },
        {
            "id": "catalog",
            "label": "Catalog onboarding protocol (grace period + adjusted thresholds)",
            "gap": "Gap 6",
            "estimated_reduction": 0.18,
            "description": "Estimated 15-22% reduction in false positives on new catalog content during the grace period. Reduces but does not eliminate misclassification of unfamiliar content.",
            "residual_risk": "Genuinely fraudulent activity may slip through during the grace period due to relaxed thresholds. New catalog content fundamentally different from training data may still be misclassified after the grace period ends.",
        },
        {
            "id": "signal_card",
            "label": "Signal confirmation card for analyst review",
            "gap": "Gap 3",
            "estimated_reduction": 0.08,
            "description": "Estimated 5-12% reduction in automation bias effects. Reduces but does not eliminate analyst tendency to defer to AI recommendations.",
            "residual_risk": "Analysts may still align with AI recommendations even after independent assessment if both reach the same conclusion. Workflow redesign cannot fully eliminate cognitive biases.",
        },
        {
            "id": "thresholds",
            "label": "Formal threshold governance with business approval",
            "gap": "Gap 2",
            "estimated_reduction": 0.05,
            "description": "Estimated 3-8% improvement through better-calibrated thresholds. Adds governance and accountability but does not directly improve model accuracy.",
            "residual_risk": "Thresholds may still be inappropriate even after business approval if the underlying model is poorly calibrated. Governance does not fix technical issues.",
        },
        {
            "id": "appeals",
            "label": "Appeal SLA + provisional royalty payments",
            "gap": "Gap 7",
            "estimated_reduction": 0.10,
            "description": "Estimated 8-12% reduction in financial harm to legitimate artists during the appeal process. Does not reduce false positive rate, but limits the financial damage when false positives occur.",
            "residual_risk": "Provisional payments do not address chart momentum loss, recommendation algorithm exclusion, or reputational harm during the appeal period.",
        },
        {
            "id": "change_mgmt",
            "label": "Change management for model, threshold, prompt updates",
            "gap": "Gap 9",
            "estimated_reduction": 0.04,
            "description": "Estimated 2-6% improvement through preventing ungoverned changes. Primarily reduces the likelihood of new issues being introduced rather than fixing existing ones.",
            "residual_risk": "Change management cannot prevent issues that arise from approved changes. Documentation does not equal correctness.",
        },
    ]

    # Track which are enabled
    enabled = {}
    for ctrl in controls:
        col_check, col_info = st.columns([3, 2])
        with col_check:
            enabled[ctrl["id"]] = st.checkbox(
                f"**{ctrl['label']}** ({ctrl['gap']})",
                value=False,
                key=f"ctrl_{ctrl['id']}",
            )
        with col_info:
            if enabled[ctrl["id"]]:
                st.markdown(
                    f'<span style="color:{SPOTIFY_GREEN}; font-size:12px;">Estimated reduction: ~{ctrl["estimated_reduction"]:.0%}</span>',
                    unsafe_allow_html=True,
                )

    # Calculate aggregate reduction
    # Use a diminishing returns model — controls overlap somewhat
    selected = [ctrl for ctrl in controls if enabled.get(ctrl["id"], False)]
    if not selected:
        total_reduction = 0.0
    else:
        # Compound the reductions with overlap (each successive control captures less of the remaining risk)
        remaining = 1.0
        for ctrl in sorted(selected, key=lambda c: c["estimated_reduction"], reverse=True):
            remaining *= (1 - ctrl["estimated_reduction"])
        total_reduction = 1.0 - remaining

    # Hard cap at 75% — auditors do NOT claim more than this is realistic
    MAX_REALISTIC_REDUCTION = 0.75
    capped = total_reduction > MAX_REALISTIC_REDUCTION
    if capped:
        total_reduction = MAX_REALISTIC_REDUCTION

    # Residual harm
    residual_daily = DAILY_ROYALTY_HARM * (1 - total_reduction)
    residual_annual = ANNUAL_PROJECTED_HARM * (1 - total_reduction)
    savings_annual = ANNUAL_PROJECTED_HARM - residual_annual

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Impact summary — REFRAMED to emphasize residual
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:14px;">Projected Risk Reduction (Estimates Only)</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:12px; padding:22px 26px; border:1px solid rgba(29,185,84,0.3); border-top:4px solid {SPOTIFY_GREEN};">
                <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Estimated Risk Reduction</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:36px; font-weight:800; line-height:1.1;">~{total_reduction:.0%}</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:6px;">Range may vary based on implementation</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:12px; padding:22px 26px; border:1px solid rgba(80,155,245,0.3); border-top:4px solid {COLOR_INFO};">
                <div style="color:{COLOR_INFO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Estimated Annual Savings</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:36px; font-weight:800; line-height:1.1;">~${savings_annual:,.0f}</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:6px;">Indicative figure based on current drift estimate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:12px; padding:22px 26px; border:1px solid rgba(245,155,35,0.3); border-top:4px solid {COLOR_WARNING};">
                <div style="color:{COLOR_WARNING}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Residual Daily Risk</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:36px; font-weight:800; line-height:1.1;">~${residual_daily:,.0f}</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:6px;">Always remains — to be accepted by management</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if capped:
        st.markdown(
            f"""
            <div style="background:rgba(245,155,35,0.08); border-left:3px solid {COLOR_WARNING}; padding:12px 16px; border-radius:6px; margin-top:12px;">
                <span style="color:{COLOR_WARNING}; font-size:12px; font-weight:700;">Realistic ceiling applied:</span>
                <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px;"> Combined controls have been capped at 75% reduction. Internal audit does not project risk reductions above this level — residual risk always remains and additional reduction would require fundamental system redesign, not controls layering.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Comparison chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Inherent Risk\n(Current)"],
        y=[ANNUAL_PROJECTED_HARM],
        name="Inherent Risk",
        marker_color=COLOR_DANGER,
        text=[f"~${ANNUAL_PROJECTED_HARM:,.0f}"],
        textposition="outside",
        textfont=dict(color=SPOTIFY_WHITE, size=13),
    ))

    fig.add_trace(go.Bar(
        x=["Residual Risk\n(With Selected Controls)"],
        y=[residual_annual],
        name="Residual Risk",
        marker_color=COLOR_WARNING,
        text=[f"~${residual_annual:,.0f}"],
        textposition="outside",
        textfont=dict(color=SPOTIFY_WHITE, size=13),
    ))

    apply_spotify_style(fig, height=400)
    fig.update_layout(
        title="Inherent vs. Residual Risk — Annual (Estimates)",
        showlegend=False,
        yaxis=dict(title="USD"),
        bargap=0.5,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Show residual risks for enabled controls
    if selected:
        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin:16px 0 12px;">Residual Risks That Remain</div>',
            unsafe_allow_html=True,
        )
        for ctrl in selected:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px 18px; border:1px solid rgba(83,83,83,0.2); border-left:3px solid {COLOR_WARNING}; margin-bottom:8px;">
                    <div style="color:{COLOR_WARNING}; font-size:12px; font-weight:700; margin-bottom:4px;">After implementing: {ctrl['label']}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5;">{ctrl['residual_risk']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Overall message
    if total_reduction == 0:
        message_color = COLOR_DANGER
        message = "No controls selected. Inherent risk remains at full level."
    elif total_reduction < 0.30:
        message_color = COLOR_WARNING
        message = f"Limited remediation. Estimated risk reduction of ~{total_reduction:.0%}. Substantial residual risk remains and additional controls should be considered."
    elif total_reduction < 0.55:
        message_color = COLOR_INFO
        message = f"Meaningful remediation. Estimated risk reduction of ~{total_reduction:.0%}. Material residual risk still requires acceptance by management or further mitigation."
    else:
        message_color = SPOTIFY_GREEN
        message = f"Comprehensive control implementation with estimated reduction of ~{total_reduction:.0%}. Residual risk remains and should be formally accepted by management. This represents the practical ceiling for control-based remediation."

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba({_hex_rgb(message_color)},0.12), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {message_color}; margin-top:16px;">
            <div style="color:{message_color}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Audit Assessment</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _hex_rgb(hex_color):
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# =========================================
# TAB 4: PROCESS MATURITY (BEFORE / AFTER)
# =========================================
def _render_process_maturity():
    """Side-by-side comparison of the current process and the proposed process with control hooks."""

    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:20px; font-weight:700; margin-bottom:6px;">Process Maturity: Before vs. After</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:20px;">'
        "Compare the current StreamShield process to the proposed mature state with control hooks and API-driven validation embedded in the workflow."
        "</p>",
        unsafe_allow_html=True,
    )

    process_steps = [
        {
            "step": "1. Catalog Acquisition",
            "before": {
                "description": "Catalog is added to the platform. No notification to Fraud team or IAR. No model evaluation triggered.",
                "control": "None",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Catalog acquisition automatically triggers a webhook to StreamShield. Content tagged with new_catalog flag and acquisition date. Model evaluation pipeline scheduled within 14 days.",
                "control": "API hook: catalog-acquisition-event → triggers model-evaluation-pipeline",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "2. Stream Classification",
            "before": {
                "description": "Model scores all streams using thresholds set at deployment. New catalog content gets the same treatment as existing content.",
                "control": "Manual threshold (no governance)",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Model scores streams. Catalog onboarding API applies adjusted thresholds (95% to 98%) for new content during 90-day grace period. Threshold values pulled from a configuration register with version control and approval metadata.",
                "control": "Config API: GET /thresholds/{content_type} returns governed values with audit metadata",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "3. Drift Detection",
            "before": {
                "description": "No automated drift detection. PSI is not computed. Performance metrics are manually reviewed quarterly during planned retraining.",
                "control": "None",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "PSI is computed continuously. When PSI exceeds warning (0.10) or critical (0.20), an alert API fires to PagerDuty and Slack. IAR continuous monitoring dashboard receives the same alert.",
                "control": "Alert API: POST /alerts/drift triggers PagerDuty + Slack + IAR dashboard",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "4. Human Review",
            "before": {
                "description": "Analyst opens case. LLM summary and recommendation are displayed. Analyst reads, often agrees, clicks Approve. Decision logged.",
                "control": "Manual review (subject to automation bias)",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Analyst opens case. Signal Confirmation Card displays raw signal values only. Analyst makes Y/N assessment per signal. Analyst submits classification. AI recommendation revealed. Structured audit trail produced automatically.",
                "control": "Workflow API: POST /reviews/{case_id} requires structured signal assessments before submission",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "5. Quarantine Action",
            "before": {
                "description": "Streams quarantined immediately. Royalties withheld for the entire 90-day hold + appeal period. Affected artist not proactively notified.",
                "control": "Hard exclusion only",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Streams quarantined. For new catalog content in grace period, provisional royalty payments enabled with clawback. Affected artist notified via API webhook with explanation (top 3 contributing signals from SHAP values).",
                "control": "Notification API: POST /artists/{artist_id}/notifications with explainability payload",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "6. Appeal Process",
            "before": {
                "description": "Appeal filed via Content & Rights team. No SLA. Major labels resolve in ~11 days, indie artists wait ~38 days. Outcome logged manually.",
                "control": "Manual workflow, no SLA",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Appeal filed via API. SLA timer starts (10 business days). Provisional payment automatically initiated. Resolution recorded via API with structured outcome data feeding back to ground truth.",
                "control": "Workflow API: POST /appeals + GET /appeals/{id}/sla-status with breach alerting",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "7. Ground Truth Feedback",
            "before": {
                "description": "Analyst decisions and appeal outcomes accumulate in BigQuery. Manual export to retraining dataset on quarterly cadence. No quality weighting.",
                "control": "Manual ETL",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Decisions stream into ground truth pipeline via Pub/Sub. Quality-weighted (review time, signal completeness, source confidence). Automated daily updates to training dataset. Drift in label distribution monitored via separate PSI.",
                "control": "Streaming API: Pub/Sub topic ground-truth-events → BigQuery training table",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "8. Model Retraining",
            "before": {
                "description": "Quarterly manual retraining. No event triggers. No champion/challenger comparison. Deployment is all-or-nothing.",
                "control": "Manual, no champion/challenger",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "Retraining triggered by drift alerts or scheduled monthly, whichever comes first. Champion/challenger evaluation runs automatically. Canary deployment to 5% of traffic, expanded to 100% only if metrics improve. Rollback capability via model registry.",
                "control": "Pipeline API: POST /models/retrain with auto-canary and rollback hooks",
                "color": SPOTIFY_GREEN,
            },
        },
        {
            "step": "9. Continuous Audit",
            "before": {
                "description": "Annual or biennial IAR audit. Findings raised, remediation tracked manually until next audit cycle.",
                "control": "Periodic engagement only",
                "color": COLOR_DANGER,
            },
            "after": {
                "description": "IAR continuous monitoring dashboard polls control APIs daily. Test procedures execute as scheduled API calls. Exceptions flow into the findings register automatically. Annual engagement focuses on emerging risks rather than re-testing the same controls.",
                "control": "Audit APIs: GET /controls/{id}/status returns current state, evidence, and last test date",
                "color": SPOTIFY_GREEN,
            },
        },
    ]

    for ps in process_steps:
        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:700; margin:18px 0 10px;">{ps["step"]}</div>',
            unsafe_allow_html=True,
        )

        col_before, col_after = st.columns(2)

        with col_before:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); border-left:3px solid {COLOR_DANGER}; min-height:160px;">
                    <div style="color:{COLOR_DANGER}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Before (Current State)</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6; margin-bottom:10px;">{ps["before"]["description"]}</div>
                    <div style="background:rgba(232,17,91,0.10); border-radius:4px; padding:8px 12px; font-family:monospace; font-size:11px; color:{COLOR_DANGER};">
                        Control: {ps["before"]["control"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_after:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); border-left:3px solid {SPOTIFY_GREEN}; min-height:160px;">
                    <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">After (Proposed State)</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6; margin-bottom:10px;">{ps["after"]["description"]}</div>
                    <div style="background:rgba(29,185,84,0.10); border-radius:4px; padding:8px 12px; font-family:monospace; font-size:11px; color:{SPOTIFY_GREEN};">
                        {ps["after"]["control"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================
# TAB 5: CONTINUOUS CONTROLS MONITORING
# =========================================
def _render_continuous_controls_monitoring():
    """API-driven continuous controls monitoring dashboard — the future of SOX testing."""

    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:20px; font-weight:700; margin-bottom:6px;">Continuous Controls Monitoring (CCM)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:12px;">'
        "API-driven continuous testing of StreamShield controls. Each control has a defined test endpoint that returns its current state, last test date, and evidence. "
        "This is what control testing looks like when automated — periodic manual workpapers replaced by continuous API polling."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(29,185,84,0.08); border-left:3px solid {SPOTIFY_GREEN}; padding:12px 16px; border-radius:6px; margin-bottom:12px;">
            <span style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700;">REGULATORY CONTEXT:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> Spotify is designated a Very Large Online Platform (VLOP) under the EU Digital Services Act (DSA). Article 34 requires annual systemic risk assessments of AI systems. Article 35 requires proportionate mitigation measures. Article 37 requires independent third-party audits. The DSA explicitly calls for an "active and preventive" governance paradigm — exactly what this dashboard enables. Continuous controls monitoring is not optional for VLOPs; it is the regulatory direction of travel.</span>
        </div>
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:12px 16px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">SOX CONNECTION:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> For the SOX-relevant controls (marked with the SOX badge below), this approach replaces periodic manual sample-based testing with continuous full-population assurance. Exceptions become real-time tickets routed to control owners. External auditors can rely on continuous evidence rather than quarterly snapshots.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Simulated CCM dashboard — each row is a SOX-relevant control
    controls = [
        {
            "id": "CCM-001",
            "control": "Threshold values match approved configuration",
            "endpoint": "GET /api/streamshield/controls/thresholds/status",
            "frequency": "Hourly",
            "last_test": "8 minutes ago",
            "result": "PASS",
            "result_color": SPOTIFY_GREEN,
            "sox": True,
            "evidence": "Current: 70% / 95%. Approved: 70% / 95%. Last change: 2025-10-15 by ml-engineering.",
        },
        {
            "id": "CCM-002",
            "control": "Model PSI within acceptable range",
            "endpoint": "GET /api/streamshield/controls/model-drift/psi",
            "frequency": "Hourly",
            "last_test": "8 minutes ago",
            "result": "FAIL",
            "result_color": COLOR_DANGER,
            "sox": False,
            "evidence": "PSI: 0.23 (Critical threshold: 0.20). Trend: increasing since 2026-01-29. Auto-ticket: JIRA SHIELD-1247.",
        },
        {
            "id": "CCM-003",
            "control": "Analyst review SLA met (15 minutes per case)",
            "endpoint": "GET /api/streamshield/controls/review-sla/status",
            "frequency": "Daily",
            "last_test": "6 hours ago",
            "result": "PASS",
            "result_color": SPOTIFY_GREEN,
            "sox": False,
            "evidence": "Avg review time: 8.4 min. SLA: 15 min. Cases reviewed today: 197.",
        },
        {
            "id": "CCM-004",
            "control": "LLM-generated reports have analyst attestation",
            "endpoint": "GET /api/streamshield/controls/llm-attestation/coverage",
            "frequency": "Daily",
            "last_test": "6 hours ago",
            "result": "FAIL",
            "result_color": COLOR_DANGER,
            "sox": True,
            "evidence": "Attestation rate: 0%. Required: 100%. Control not implemented. Auto-ticket: JIRA SHIELD-1198.",
        },
        {
            "id": "CCM-005",
            "control": "Data reconciliation: total streams in = passed + quarantined + review",
            "endpoint": "GET /api/streamshield/controls/data-reconciliation/daily",
            "frequency": "Daily",
            "last_test": "2 hours ago",
            "result": "PASS",
            "result_color": SPOTIFY_GREEN,
            "sox": True,
            "evidence": "In: 17,845,231. Out: 17,845,231 (passed: 16,769,720, quarantined: 142,762, review: 932,749). Variance: 0.",
        },
        {
            "id": "CCM-006",
            "control": "Appeal SLA met (10 business days for initial review)",
            "endpoint": "GET /api/streamshield/controls/appeal-sla/status",
            "frequency": "Daily",
            "last_test": "6 hours ago",
            "result": "FAIL",
            "result_color": COLOR_DANGER,
            "sox": False,
            "evidence": "SLA breach rate: 67%. Most affected: indie artists (avg 38 days vs 10-day SLA). Auto-ticket: JIRA SHIELD-1156.",
        },
        {
            "id": "CCM-007",
            "control": "Model version in production matches approved registry version",
            "endpoint": "GET /api/streamshield/controls/model-version/status",
            "frequency": "Hourly",
            "last_test": "8 minutes ago",
            "result": "PASS",
            "result_color": SPOTIFY_GREEN,
            "sox": True,
            "evidence": "Production: streamshield-v2.3.1. Approved: streamshield-v2.3.1. Last change: 2025-12-09 (approved by ml-eng-lead).",
        },
        {
            "id": "CCM-008",
            "control": "All change requests have authorization, testing, and rollback plan",
            "endpoint": "GET /api/streamshield/controls/change-management/coverage",
            "frequency": "Weekly",
            "last_test": "2 days ago",
            "result": "FAIL",
            "result_color": COLOR_DANGER,
            "sox": True,
            "evidence": "Changes in past 7 days: 14. Compliant with change management policy: 0. Coverage: 0%. Auto-ticket: JIRA SHIELD-1098.",
        },
        {
            "id": "CCM-009",
            "control": "Catalog onboarding protocol applied to new content",
            "endpoint": "GET /api/streamshield/controls/catalog-onboarding/coverage",
            "frequency": "Daily",
            "last_test": "6 hours ago",
            "result": "FAIL",
            "result_color": COLOR_DANGER,
            "sox": False,
            "evidence": "New catalog acquired 2026-01-29. Onboarding protocol: not implemented. New content getting standard thresholds. Auto-ticket: JIRA SHIELD-1247.",
        },
        {
            "id": "CCM-010",
            "control": "Ground truth feedback loop ingesting appeal outcomes",
            "endpoint": "GET /api/streamshield/controls/ground-truth-feedback/status",
            "frequency": "Daily",
            "last_test": "6 hours ago",
            "result": "WARN",
            "result_color": COLOR_WARNING,
            "sox": False,
            "evidence": "Manual ETL still in use. Last update: 8 days ago. Recommendation: implement streaming ingestion via Pub/Sub.",
        },
    ]

    # Summary stats
    total = len(controls)
    passing = sum(1 for c in controls if c["result"] == "PASS")
    failing = sum(1 for c in controls if c["result"] == "FAIL")
    warnings = sum(1 for c in controls if c["result"] == "WARN")
    sox_relevant = sum(1 for c in controls if c["sox"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(83,83,83,0.25); text-align:center;">
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Total Controls</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:28px; font-weight:800; margin-top:4px;">{total}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(29,185,84,0.3); text-align:center;">
                <div style="color:{SPOTIFY_GREEN}; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Passing</div>
                <div style="color:{SPOTIFY_GREEN}; font-size:28px; font-weight:800; margin-top:4px;">{passing}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(232,17,91,0.3); text-align:center;">
                <div style="color:{COLOR_DANGER}; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Failing</div>
                <div style="color:{COLOR_DANGER}; font-size:28px; font-weight:800; margin-top:4px;">{failing}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(80,155,245,0.3); text-align:center;">
                <div style="color:{COLOR_INFO}; font-size:11px; text-transform:uppercase; letter-spacing:1px;">SOX Relevant</div>
                <div style="color:{COLOR_INFO}; font-size:28px; font-weight:800; margin-top:4px;">{sox_relevant}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Controls table
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:14px;">Live Control Status</div>',
        unsafe_allow_html=True,
    )

    # Use components.html to bypass Streamlit HTML sanitization issues with conditional badges
    controls_html_parts = ['''
    <html><head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body { font-family: 'Inter', -apple-system, sans-serif; background: #121212; color: #fff; margin: 0; padding: 0; }
        .control-card { background: #181818; border-radius: 8px; padding: 16px 20px; border: 1px solid rgba(83,83,83,0.2); margin-bottom: 10px; }
        .row-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
        .id-line { color: #535353; font-size: 11px; font-family: monospace; }
        .sox-badge { background: rgba(80,155,245,0.2); color: #509BF5; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; margin-left: 8px; }
        .control-name { color: #fff; font-size: 14px; font-weight: 600; margin-top: 4px; }
        .right-block { text-align: right; }
        .result-badge { padding: 4px 14px; border-radius: 500px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; display: inline-block; }
        .last-test { color: #535353; font-size: 10px; margin-top: 4px; }
        .endpoint { background: #0a0a0a; border-radius: 4px; padding: 8px 12px; font-family: monospace; font-size: 11px; color: #B3B3B3; margin-top: 8px; }
        .evidence { color: #B3B3B3; font-size: 12px; margin-top: 8px; line-height: 1.5; }
        .evidence strong { color: #fff; }
    </style>
    </head><body>
    ''']

    for ctrl in controls:
        sox_badge = '<span class="sox-badge">SOX</span>' if ctrl["sox"] else ""
        result_bg = f"rgba({_hex_rgb(ctrl['result_color'])},0.18)"
        controls_html_parts.append(f'''
        <div class="control-card" style="border-left: 4px solid {ctrl['result_color']};">
            <div class="row-top">
                <div>
                    <span class="id-line">{ctrl['id']}</span>{sox_badge}
                    <div class="control-name">{ctrl['control']}</div>
                </div>
                <div class="right-block">
                    <div class="result-badge" style="background: {result_bg}; color: {ctrl['result_color']};">{ctrl['result']}</div>
                    <div class="last-test">{ctrl['last_test']}</div>
                </div>
            </div>
            <div class="endpoint">{ctrl['endpoint']}</div>
            <div class="evidence"><strong>Evidence:</strong> {ctrl['evidence']}</div>
        </div>
        ''')

    controls_html_parts.append('</body></html>')
    components.html("".join(controls_html_parts), height=1700, scrolling=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {SPOTIFY_GREEN};">
            <div style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Why This Matters</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                In a traditional SOX audit, each of these controls would be tested by pulling a sample of evidence once per quarter. With API-driven continuous monitoring, every control is tested every hour or every day. Exceptions become real-time tickets routed to the control owner.
                The audit function shifts from periodic sample-based testing to continuous full-population assurance. This is the direction Spotify and other technology-forward organizations are moving for both ICFR controls and operational controls.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# SCENARIO B: Sophisticated Fraud Evasion
# =========================================
def _render_scenario_b_fraud_evasion():
    """Defense in depth catches what Layer 1 missed."""

    st.markdown(
        f'<div style="color:{COLOR_WARNING}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:4px;">Scenario B &middot; Defense in Depth</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:8px;">Sophisticated Fraud Evasion — The Limits of Layer 1</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "A fraudster studies StreamShield and adapts. They use aged dark-web accounts, residential proxies, realistic listening durations, and a low-and-slow distribution. The ML model misses them entirely. Six months later, they have earned ~$400,000. The Defense in Depth framework catches them at Layer 3 (network analysis), not Layer 1 (the model)."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:10px 14px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">DSA ANGLE:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> Article 34 requires VLOPs to assess systemic risks including risks from adversarial adaptation. A model that catches yesterday's fraud is not a sufficient mitigation under Article 35. Defense in depth across multiple control layers is the proportionate response.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show the 5 layers and which catches the attack
    layers = [
        {"layer": "Layer 1 — ML Model (real-time)", "result": "MISS", "color": COLOR_DANGER, "explanation": "Aged accounts, residential proxies, varied durations, low volume per account. Score: 0.62 (below 0.70 threshold). Stream classified as legitimate."},
        {"layer": "Layer 2 — Human Review", "result": "NOT TRIGGERED", "color": SPOTIFY_GRAY, "explanation": "Score below 70% — never enters review zone. Human eyes never see this case."},
        {"layer": "Layer 3 — Network/Entity Analysis", "result": "CATCH", "color": SPOTIFY_GREEN, "explanation": "Daily entity-level analysis identifies 47 accounts streaming the same 200 tracks at coordinated times across the same IP subnet. Pattern flagged after 14 days. Investigation initiated."},
        {"layer": "Layer 4 — Distributor Accountability", "result": "ENFORCE", "color": COLOR_INFO, "explanation": "Distributor associated with the fraud accounts is suspended. €10/track penalty applied. Distributor's full catalog is risk-elevated."},
        {"layer": "Layer 5 — Retroactive Clawback", "result": "RECOVER", "color": SPOTIFY_GREEN, "explanation": "Royalties paid out from the past 14 days are clawed back from the fraudster's payment destination. ~$140,000 recovered. Remaining ~$260,000 written off."},
    ]

    for layer in layers:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {layer['color']}; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700;">{layer['layer']}</span>
                    <span style="background:rgba({_hex_rgb(layer['color'])},0.18); color:{layer['color']}; padding:3px 12px; border-radius:500px; font-size:11px; font-weight:700;">{layer['result']}</span>
                </div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5;">{layer['explanation']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(245,155,35,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {COLOR_WARNING}; margin-top:16px;">
            <div style="color:{COLOR_WARNING}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Lesson</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                The ML model was unable to catch this attack — by design, no model can stay ahead of every adaptive adversary. This is exactly why defense in depth matters and why the catalog onboarding protocol's leniency is viable. The system tolerates some false negatives at Layer 1 because Layers 3-5 still operate. The total loss of ~$260,000 is an acceptable cost compared to the harm of false positives (lost royalties for legitimate artists, public disputes, regulatory exposure).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# SCENARIO C: Data Poisoning Attack
# =========================================
def _render_scenario_c_data_poisoning():
    """Adversarial AI risk via training data manipulation."""

    st.markdown(
        f'<div style="color:{COLOR_DANGER}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:4px;">Scenario C &middot; Adversarial AI Risk</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:8px;">Data Poisoning Attack on the Training Pipeline</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "A sophisticated bad actor targets the ground truth feedback loop. They behave legitimately for 90 days to build up trusted account history, then file a strategic appeal to get fraud streams relabeled as legitimate. The relabeled data feeds into model retraining. The model now tolerates their fraud pattern. The bias compounds."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:10px 14px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">DSA ANGLE:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> Article 34 explicitly includes adversarial AI risks within the systemic risk obligations of VLOPs. The DSA does not just want VLOPs to detect organic AI failures — it wants them to defend against deliberate manipulation. Data poisoning is a known attack vector that any AI governance framework must address.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # The attack timeline
    timeline = [
        {"day": "Day 0-90", "phase": "Reconnaissance & Reputation Building", "action": "Bad actor creates 12 accounts. Streams normal music, varied durations, normal skip rates, residential IPs, real device fingerprints. Looks indistinguishable from legitimate users. Accounts accumulate clean history.", "color": COLOR_INFO},
        {"day": "Day 91", "phase": "Trigger Event", "action": "Bad actor begins streaming AI-generated content from new artist profiles they control. Streams are flagged as suspicious by the model (correct decision). Quarantined.", "color": COLOR_WARNING},
        {"day": "Day 92-120", "phase": "Strategic Appeal", "action": "Bad actor files appeals citing 'I am a real listener with 90 days of normal activity, I just discovered this artist.' Appeals are reviewed by Content & Rights team. Because the accounts have clean history, ~60% of appeals are overturned.", "color": COLOR_DANGER},
        {"day": "Day 130", "phase": "Label Contamination", "action": "Overturned appeals enter the ground truth pipeline as 'high-confidence legitimate' labels. The fraud streams are now labeled as legitimate in the training data. Other similar fraud streams from the same network also benefit from the relabeling.", "color": COLOR_DANGER},
        {"day": "Day 150", "phase": "Model Retraining", "action": "Quarterly retraining incorporates the contaminated labels. The model learns that this fraud pattern is legitimate. False negative rate increases for this attack vector. The bad actor's coordinated activity now scores below 0.70 by default.", "color": COLOR_DANGER},
        {"day": "Day 180+", "phase": "Compounding Bias", "action": "The bad actor scales up. Their attack pattern is now considered legitimate by the model. They earn an estimated ~$1.2M before any other defense layer catches them.", "color": COLOR_DANGER},
    ]

    for event in timeline:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {event['color']}; margin-bottom:10px;">
                <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:6px;">
                    <span style="color:{event['color']}; font-size:11px; font-weight:700; min-width:80px;">{event['day']}</span>
                    <span style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700;">{event['phase']}</span>
                </div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5; margin-left:92px;">{event['action']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(232,17,91,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {COLOR_DANGER}; margin-top:16px;">
            <div style="color:{COLOR_DANGER}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Why This Connects to the Circular Dependency Insight</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                This is the data poisoning version of the circular dependency we identified in Risk 3. There, the threat was unintentional — analysts rubber-stamping AI recommendations that became labels. Here, the threat is deliberate — a bad actor specifically engineering the inputs that become labels. Both attacks succeed for the same structural reason: there is no quality gate between analyst/appeal decisions and the training pipeline. The same control fixes both: quality-weighted labels, source verification, anomaly detection on the ground truth pipeline itself.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {SPOTIFY_GREEN}; margin-top:12px;">
            <div style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Recommended Mitigation</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                1. Apply anomaly detection to the ground truth pipeline itself — flag clusters of overturned appeals from similar accounts.<br>
                2. Quality-weight labels by confidence — overturned appeals from accounts with limited history carry lower weight than confirmed takedowns.<br>
                3. Hold relabeled data in quarantine for a cooling-off period before incorporating into training.<br>
                4. Cross-reference appeal patterns against network-level entity analysis (Layer 3) before trusting labels.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# SCENARIO D: DSA Regulatory Inquiry
# =========================================
def _render_scenario_d_dsa_inquiry():
    """A regulator asks for evidence under DSA Articles 34/35/37."""

    st.markdown(
        f'<div style="color:{COLOR_INFO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:4px;">Scenario D &middot; Regulatory Walkthrough</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:8px;">DSA Coordinator Inquiry — Article 37 Independent Audit Walkthrough</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "The Digital Services Coordinator (the EU regulatory body) sends a formal inquiry to Spotify's DSA Compliance Officer. They are conducting an independent audit under Article 37 and want to assess StreamShield's compliance with Article 34 (systemic risk assessment) and Article 35 (mitigation measures). They request specific evidence."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(232,17,91,0.08); border-left:3px solid {COLOR_DANGER}; padding:10px 14px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_DANGER}; font-size:11px; font-weight:700;">REGULATORY URGENCY:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> A DSA inquiry is not a request for cooperation — it is a legal obligation. Failure to respond adequately can result in fines up to 6% of global annual turnover. For Spotify, that would be approximately $850M+. The questions below are paraphrased from real DSA audit frameworks.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    requests = [
        {
            "id": "Q1",
            "article": "Article 34",
            "question": "Provide your most recent systemic risk assessment for StreamShield, including identified risks, likelihood, and impact ratings.",
            "current_state": "No formal systemic risk assessment exists for StreamShield. The case study identified risks ad hoc but no Article 34 document has been produced.",
            "with_controls": "Quarterly systemic risk assessment generated automatically by the prototype, exported to the DSA Compliance team, signed off by Head of Fraud and Internal Audit.",
            "evidence_now": "None",
            "evidence_after": "Audit Agent finding generation + Risk Heatmap + dated assessment exports",
        },
        {
            "id": "Q2",
            "article": "Article 35",
            "question": "Describe the proportionate mitigation measures in place for the risk that the AI system incorrectly excludes legitimate content.",
            "current_state": "No documented mitigation measures. Reactive appeal process only. Major label appeals resolve in 11 days, indie in 38 days.",
            "with_controls": "Documented mitigation framework: catalog onboarding protocol with adjusted thresholds; signal confirmation card for human review; appeal SLA with provisional payments; explainability output for affected artists.",
            "evidence_now": "None — Content & Rights queue only",
            "evidence_after": "Process Maturity tab + Continuous Controls Monitoring API endpoints",
        },
        {
            "id": "Q3",
            "article": "Article 14 (AI Act intersection)",
            "question": "Demonstrate the meaningful human oversight applied to automated decisions that significantly affect users.",
            "current_state": "Human review exists for the 5% of streams in the 70-95% review zone. The LLM assistant helps analysts investigate, which is valuable. The workflow currently shows the LLM summary before the analyst forms an independent view.",
            "with_controls": "Signal Confirmation Card resequences the workflow: analysts assess raw signals first, LLM summary appears as a second opinion. Both perspectives captured in the audit trail. Challenge cases validate independence quarterly.",
            "evidence_now": "Decision logs only — no evidence of independent assessment",
            "evidence_after": "Structured signal cards per case with audit trail + bias monitoring dashboard",
        },
        {
            "id": "Q4",
            "article": "Article 34",
            "question": "Provide evidence that you continuously monitor your AI system for emerging risks, including model drift and adversarial adaptation.",
            "current_state": "No continuous monitoring exists. Model performance is reviewed quarterly during planned retraining cycles. The current 12% precision drop has gone undetected for 4 months.",
            "with_controls": "Automated PSI monitoring with alerts at warning (0.10) and critical (0.20) thresholds. Drift dashboard updated hourly. Event-triggered model evaluation after platform changes within 14 days.",
            "evidence_now": "Quarterly retraining notes only",
            "evidence_after": "Drift Monitor dashboard + alert log + retraining trigger history",
        },
        {
            "id": "Q5",
            "article": "Article 35",
            "question": "Describe how you handle disparate impact across user groups, particularly geographic and demographic groups.",
            "current_state": "No segment-level analysis exists. Our prototype identified that new catalog content (predominantly Latin, Classical, Regional Folk genres) is flagged at 6.6x the rate of existing content. This pattern was not detected by Spotify before our analysis.",
            "with_controls": "Segment-level performance reporting by genre, geography, and artist tier. Disparate impact monitoring with regulatory reporting. Catalog onboarding protocol prevents new content from being disproportionately affected.",
            "evidence_now": "None — segment performance not measured",
            "evidence_after": "Drift Monitor catalog impact analysis + Audit Agent disparate impact reports",
        },
        {
            "id": "Q6",
            "article": "Article 37",
            "question": "Provide your most recent third-party independent audit of StreamShield's AI governance.",
            "current_state": "No third-party audit has been performed. Internal audit engagement has not yet occurred. Case study indicates this engagement is the first formal IAR review.",
            "with_controls": "Annual third-party audit performed against Article 34/35 requirements, supported by continuous monitoring evidence. Audit report filed with the DSA Coordinator.",
            "evidence_now": "None",
            "evidence_after": "Annual audit report + remediation tracker + continuous monitoring evidence",
        },
    ]

    for req in requests:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 22px; border:1px solid rgba(83,83,83,0.2); margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">{req['id']} &middot; {req['article']}</span>
                </div>
                <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:600; line-height:1.5; margin-bottom:14px;">"{req['question']}"</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
                    <div style="background:rgba(232,17,91,0.08); border-radius:6px; padding:12px 14px; border-left:3px solid {COLOR_DANGER};">
                        <div style="color:{COLOR_DANGER}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">Current Response</div>
                        <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; line-height:1.5; margin-bottom:6px;">{req['current_state']}</div>
                        <div style="color:{COLOR_DANGER}; font-size:11px; font-style:italic;">Evidence available: {req['evidence_now']}</div>
                    </div>
                    <div style="background:rgba(29,185,84,0.08); border-radius:6px; padding:12px 14px; border-left:3px solid {SPOTIFY_GREEN};">
                        <div style="color:{SPOTIFY_GREEN}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:4px;">Response with Recommended Controls</div>
                        <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; line-height:1.5; margin-bottom:6px;">{req['with_controls']}</div>
                        <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-style:italic;">Evidence from prototype: {req['evidence_after']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(232,17,91,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {COLOR_DANGER}; margin-top:8px;">
            <div style="color:{COLOR_DANGER}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Audit Conclusion</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                If a DSA inquiry came today, Spotify could not provide adequate evidence for any of these six questions. The current state would be assessed as non-compliant with Articles 34, 35, and 37. With the recommended controls in place — and our prototype as the evidence backbone — Spotify could respond to each question with continuous, current evidence rather than retrospective claims. This is the regulatory reason continuous controls monitoring is not optional for VLOPs.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# SCENARIO E: New Catalog Onboarding (Success Path)
# =========================================
def _render_scenario_e_success_path():
    """The proposed controls operating in production — what success looks like."""

    st.markdown(
        f'<div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:4px;">Scenario E &middot; Success Path</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:8px;">New Catalog Onboarding — How It Works After the Controls Are In Place</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "Six months after implementing all the recommended controls, Spotify acquires another regional catalog (this time from a Brazilian label specializing in samba and bossa nova). This walkthrough shows what happens — step by step — when the controls actually operate."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:10px 14px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">DSA ANGLE:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> This scenario demonstrates Article 35 proportionate mitigation in practice. The controls activate automatically without manual intervention. Evidence is generated continuously. A DSA Coordinator could observe this entire flow and find it compliant.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        {"day": "Day 0", "title": "Catalog Acquired", "what": "Brazilian samba label catalog acquired. 25,000 tracks, 180 artists.", "happens": "Catalog acquisition webhook fires. Content tagged with new_catalog flag and acquisition_date. Catalog Onboarding Protocol activates automatically. Auto-quarantine threshold raised from 95% to 98% for new content. Default routing for review-zone cases set to 'monitor with provisional royalty payments' instead of quarantine.", "color": SPOTIFY_GREEN},
        {"day": "Day 1", "title": "First Streams Arrive", "what": "Listeners in Brazil and Portugal start streaming the new content.", "happens": "Streams flow through StreamShield. The model scores them. Some score in the 75-90% range due to: new accounts, concentrated geography, longer track durations. With the new threshold, these enter 'monitor' state instead of being quarantined. Provisional royalties begin accumulating.", "color": COLOR_INFO},
        {"day": "Day 2", "title": "PSI Alert", "what": "PSI on the input distribution starts to rise.", "happens": "Continuous PSI monitoring detects distribution shift due to new content. PSI rises to 0.13 (above warning threshold). Alert fires to ML Engineering team and IAR continuous monitoring dashboard. Acknowledged immediately — this is expected because of the catalog acquisition.", "color": COLOR_WARNING},
        {"day": "Day 7", "title": "Model Evaluation", "what": "Mandatory model evaluation runs.", "happens": "Per the catalog onboarding policy, model performance is evaluated within 14 days. Sample of new catalog streams reviewed by Fraud team using Signal Confirmation Card. Independent assessment confirms the scoring is overcautious — most flagged content is legitimate.", "color": COLOR_INFO},
        {"day": "Day 14", "title": "Retraining Initiated", "what": "Model retraining triggered by event protocol.", "happens": "Kubeflow pipeline starts. Training data updated with new catalog samples (correctly labeled). Retraining runs. New model evaluated by TFX Evaluator against precision/recall gates. Champion/challenger comparison vs current production model.", "color": COLOR_INFO},
        {"day": "Day 21", "title": "Canary Deployment", "what": "Retrained model deployed to 5% of traffic.", "happens": "Salem deploys new model version to 5% canary. Performance monitored. After 24 hours, metrics confirm improvement. Expanded to 50%. After another 24 hours, expanded to 100%. Rollback capability retained for 7 days.", "color": COLOR_INFO},
        {"day": "Day 28", "title": "Grace Period Continues", "what": "New model running with adjusted thresholds.", "happens": "PSI returns to baseline (0.04). Precision returns to 93.5%. Catalog onboarding protocol still applying adjusted thresholds — they will normalize over the remaining 60 days of the grace period.", "color": SPOTIFY_GREEN},
        {"day": "Day 90", "title": "Grace Period Ends", "what": "Standard thresholds resumed.", "happens": "Auto-quarantine threshold returns to 95%. The new catalog has been fully integrated into the model. Provisional royalty payments are reconciled. No artist disputes occurred. No public complaints. Continuous monitoring continues.", "color": SPOTIFY_GREEN},
    ]

    for i, step in enumerate(steps):
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {step['color']}; margin-bottom:10px;">
                <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:6px;">
                    <span style="color:{step['color']}; font-size:11px; font-weight:700; min-width:60px;">{step['day']}</span>
                    <span style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700;">{step['title']}</span>
                    <span style="color:{SPOTIFY_GRAY}; font-size:12px;">— {step['what']}</span>
                </div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6; margin-left:72px;">{step['happens']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Compare with the failure scenario
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    cmp_col1, cmp_col2 = st.columns(2)
    with cmp_col1:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 22px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {COLOR_DANGER};">
                <div style="color:{COLOR_DANGER}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">Without Controls (Scenario A)</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                    &bull; Drift undetected for 120 days<br>
                    &bull; Artist dispute filed at Day 90<br>
                    &bull; 38-day appeal resolution<br>
                    &bull; Public complaint at Day 105<br>
                    &bull; Estimated $X harm to legitimate artists<br>
                    &bull; Reputational damage<br>
                    &bull; IAR engagement triggered reactively<br>
                    &bull; DSA non-compliance exposure
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cmp_col2:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 22px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {SPOTIFY_GREEN};">
                <div style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">With Controls (Scenario E)</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                    &bull; Drift detected within 48 hours<br>
                    &bull; Zero artist disputes<br>
                    &bull; Provisional payments throughout<br>
                    &bull; Model retrained within 21 days<br>
                    &bull; No legitimate artists harmed<br>
                    &bull; Reputational position strengthened<br>
                    &bull; IAR engagement is preventive, not reactive<br>
                    &bull; DSA Article 35 compliance demonstrable
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {SPOTIFY_GREEN}; margin-top:16px;">
            <div style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">The Headline</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                The controls do not eliminate risk. PSI still rose to 0.13. Some streams were still flagged. Some artists still had reduced visibility during the grace period. But the difference is that the system <strong>knew</strong> these things were happening, <strong>responded</strong> automatically, and <strong>recovered</strong> within 30 days. This is what proportionate mitigation under DSA Article 35 actually looks like in practice — not perfection, but rapid detection, rapid response, and demonstrable evidence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# SCENARIO F: Analyst Bias Detection
# =========================================
def _render_scenario_f_bias_detection():
    """Continuous monitoring catches an analyst showing automation bias."""

    st.markdown(
        f'<div style="color:{COLOR_WARNING}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:4px;">Scenario F &middot; Continuous Monitoring</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:8px;">New Analyst Shows Automation Bias — Caught in Real Time</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "A new fraud analyst joins the team. In their first month, they show concerning patterns: 99% agreement rate with the AI, average review time of 60 seconds per case. The continuous monitoring dashboard catches it. The manager intervenes before the analyst's decisions contaminate the ground truth pipeline."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:rgba(80,155,245,0.08); border-left:3px solid {COLOR_INFO}; padding:10px 14px; border-radius:6px; margin-bottom:20px;">
            <span style="color:{COLOR_INFO}; font-size:11px; font-weight:700;">DSA + EU AI ACT ANGLE:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;"> EU AI Act Article 14 requires meaningful human oversight for AI systems with material impact. A rubber-stamping analyst does not constitute meaningful oversight. Continuous monitoring of analyst behavior is what makes Article 14 compliance verifiable rather than aspirational.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    timeline = [
        {"week": "Week 1", "title": "New Analyst Onboarded", "what": "Sara joins the Fraud team. Completes onboarding training. Begins reviewing review-zone cases.", "metrics": "Cases reviewed: 45 | Agreement: 100% | Avg time: 75s", "color": COLOR_INFO},
        {"week": "Week 2", "title": "Pattern Emerges", "what": "Sara's metrics start to look different from the team baseline. The Bias Detector dashboard automatically computes per-analyst metrics daily.", "metrics": "Cases reviewed: 180 | Agreement: 99% | Avg time: 65s", "color": COLOR_WARNING},
        {"week": "Week 3", "title": "Threshold Breach", "what": "Bias Detector flags Sara's metrics as exceeding the bias threshold (>95% agreement AND <90s review time). Alert fires to Fraud Team Lead and IAR continuous monitoring dashboard.", "metrics": "Cases reviewed: 195 | Agreement: 99% | Avg time: 60s", "color": COLOR_DANGER},
        {"week": "Week 3 Day 2", "title": "Manager Notified", "what": "Fraud Team Lead receives the alert. Reviews Sara's recent decisions. Notices that Sara has not used the Signal Confirmation Card properly — she clicks Y/N rapidly without looking at the data.", "metrics": "Investigation triggered", "color": COLOR_WARNING},
        {"week": "Week 3 Day 3", "title": "Quarantine Hold", "what": "Sara's labels are marked as 'low confidence' in the ground truth pipeline. They will not be used for model retraining until quality is verified. This protects the model from contamination.", "metrics": "Sara's labels: quarantined from training pipeline", "color": COLOR_INFO},
        {"week": "Week 3 Day 4", "title": "Coaching Session", "what": "Fraud Team Lead meets with Sara. Reviews 10 of her recent cases together. Discusses the importance of independent assessment. Re-explains the Signal Confirmation Card workflow.", "metrics": "Coaching delivered", "color": COLOR_INFO},
        {"week": "Week 4", "title": "Improvement", "what": "Sara's metrics improve. She is now spending appropriate time per case and showing more independent judgment. Her review time has tripled, her agreement rate has dropped to a healthy range.", "metrics": "Cases reviewed: 165 | Agreement: 87% | Avg time: 195s", "color": SPOTIFY_GREEN},
        {"week": "Week 6", "title": "Confidence Restored", "what": "After 2 weeks of consistent improvement, Sara's labels are unmarked from the quarantine status. They flow back into the training pipeline. Continuous monitoring continues.", "metrics": "Sara's metrics: within healthy range", "color": SPOTIFY_GREEN},
    ]

    for event in timeline:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px 20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {event['color']}; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <div>
                        <span style="color:{event['color']}; font-size:11px; font-weight:700;">{event['week']}</span>
                        <span style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700; margin-left:10px;">{event['title']}</span>
                    </div>
                    <span style="color:{SPOTIFY_GRAY}; font-size:11px; font-family:monospace;">{event['metrics']}</span>
                </div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5;">{event['what']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.10), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 24px; border-left:4px solid {SPOTIFY_GREEN}; margin-top:16px;">
            <div style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">What This Demonstrates</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                Without continuous monitoring, Sara's pattern would have gone undetected for months. Her decisions would have entered the training pipeline as "human-verified" labels, contaminating the ground truth. The model would have inherited her biases. This is exactly the circular dependency we identified in Risk 3 — but caught before it could compound. Continuous bias detection protects not just analyst quality but the integrity of the entire training pipeline. This is what proactive governance looks like.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

