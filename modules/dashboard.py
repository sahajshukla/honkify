"""Dashboard — Overview with live metrics, findings, and defense-in-depth."""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card,
)
from utils.data_loader import get_data_source_badge


def render(events_df, reviews_df, perf_df, appeals_df, events_src):
    # Header with gradient
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(29,185,84,0.12) 0%, rgba(18,18,18,0) 60%); border-radius:12px; padding:32px 32px 24px 32px; margin-bottom:24px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="{SPOTIFY_GREEN}">
                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                </svg>
                <span style="font-size:32px; font-weight:800; color:{SPOTIFY_WHITE}; letter-spacing:-0.5px;">StreamShield Audit Assistant</span>
            </div>
            <p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; max-width:800px; line-height:1.6; margin:0;">
                AI-powered audit tool for Spotify's StreamShield fraud detection platform.
                Monitoring model health, detecting automation bias, analyzing threshold sensitivity, and generating data-driven audit findings.
                {get_data_source_badge(events_src)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key metrics
    pre_precision = perf_df.iloc[:120]["precision"].mean()
    current_precision = perf_df.iloc[-7:]["precision"].mean()
    agreement_rate = reviews_df["agreed_with_llm"].mean()
    avg_appeal_days = appeals_df["days_to_resolve"].mean()
    overturn = (appeals_df["outcome"] == "overturned").mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card("Model Precision", f"{current_precision:.1%}", delta=round((current_precision - pre_precision) * 100, 1), delta_color="bad"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Analyst Agreement", f"{agreement_rate:.1%}"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Avg Appeal Resolution", f"{avg_appeal_days:.0f} days"), unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card("Appeal Overturn Rate", f"{overturn:.0%}"), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Key observations
    st.markdown(f'<div style="font-size:20px; font-weight:700; color:{SPOTIFY_WHITE}; margin-bottom:16px;">Key Observations</div>', unsafe_allow_html=True)

    findings = [
        ("Model Performance — Drift Detected", "HIGH", "#FF6437",
         f"Scenario modeling shows precision declining post-catalog-acquisition. New catalog content flagged at elevated rate. (Illustrative data.)"),
        ("Threshold Governance", "HIGH", "#FF6437",
         "Classification thresholds (70%/95%) set by engineering without business stakeholder review. Opportunity for formal governance framework."),
        ("Analyst Workflow Sequencing", "MEDIUM", COLOR_WARNING,
         "LLM recommendation shown before analyst forms independent view. Signal Card resequencing recommended to validate independence."),
        ("Appeal Process Timeliness", "MEDIUM", COLOR_WARNING,
         f"Case study confirms 6-week appeal for one indie label. Scenario data models resolution time variations by artist type. SLA recommended. (Illustrative data.)"),
    ]

    for i in range(0, len(findings), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(findings):
                title, sev, color, desc = findings[i + j]
                with col:
                    st.markdown(
                        f"""
                        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:24px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {color}; min-height:160px;">
                            <span style="background:rgba(255,255,255,0.06); color:{color}; padding:3px 10px; border-radius:500px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{sev}</span>
                            <div style="color:{SPOTIFY_WHITE}; font-size:17px; font-weight:700; margin:10px 0 8px;">{title}</div>
                            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; line-height:1.5;">{desc}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Defense in Depth
    st.markdown(f'<div style="font-size:20px; font-weight:700; color:{SPOTIFY_WHITE}; margin-bottom:16px;">Defense in Depth</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px; margin-bottom:16px;">'
        "No single control solves fraud. Five layers compensate for each other's weaknesses."
        "</p>",
        unsafe_allow_html=True,
    )

    layers = [
        ("1", "ML Model", "Real-time per-stream scoring", SPOTIFY_GREEN, "Real-time"),
        ("2", "Human Review", "Signal confirmation card", COLOR_INFO, "Hours"),
        ("3", "Network Analysis", "Entity-level patterns", COLOR_WARNING, "Days"),
        ("4", "Distributor", "Accountability + penalties", "#AF2896", "Months"),
        ("5", "Clawback", "Retroactive recovery", COLOR_DANGER, "Retroactive"),
    ]

    layer_cols = st.columns(5)
    for i, (num, title, desc, color, speed) in enumerate(layers):
        with layer_cols[i]:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {color}; min-height:150px;">
                    <div style="color:{SPOTIFY_GRAY}; font-size:10px; letter-spacing:1px; margin-bottom:4px;">LAYER {num}</div>
                    <div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:700; margin-bottom:6px;">{title}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; line-height:1.4;">{desc}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:10px; margin-top:8px;">{speed}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Quick precision trend
    st.markdown(f'<div style="font-size:20px; font-weight:700; color:{SPOTIFY_WHITE}; margin-bottom:16px;">Model Health — 180 Day Trend</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=perf_df["date"], y=perf_df["precision"],
        name="Precision", line=dict(color=SPOTIFY_GREEN, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=perf_df["date"], y=perf_df["false_positive_rate"],
        name="False Positive Rate", line=dict(color=COLOR_DANGER, width=2),
        yaxis="y2",
    ))

    acq_date = perf_df["date"].iloc[120]
    fig.add_vline(x=acq_date, line_dash="dash", line_color=COLOR_DANGER, line_width=2)
    fig.add_annotation(
        x=acq_date, y=perf_df["precision"].max(),
        text="Catalog Acquisition", showarrow=True, arrowhead=2,
        arrowcolor=COLOR_DANGER, font=dict(color=COLOR_DANGER, size=11),
        bgcolor=SPOTIFY_CARD_BG, bordercolor=COLOR_DANGER, borderwidth=1, borderpad=4,
    )

    apply_spotify_style(fig, height=380)
    fig.update_layout(
        yaxis=dict(title="Precision", side="left"),
        yaxis2=dict(title="FP Rate", side="right", overlaying="y",
                    gridcolor="rgba(0,0,0,0)", tickfont=dict(color=COLOR_DANGER),
                    title_font=dict(color=COLOR_DANGER)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
