"""Module 2: Analyst Behavior & Automation Bias Detector."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card, CHART_COLORS,
)


def render(reviews_df: pd.DataFrame):
    st.markdown("## Automation Bias Detector")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Analyzes analyst review patterns to detect automation bias. "
        "For the 5% of streams reaching human review, validates whether analyst decisions reflect independent judgment or anchoring to the LLM summary."
        "</p>",
        unsafe_allow_html=True,
    )

    # Overall metrics
    overall_agreement = reviews_df["agreed_with_llm"].mean()
    avg_time = reviews_df["time_to_decision_sec"].mean()
    total_cases = len(reviews_df)
    n_analysts = reviews_df["analyst_id"].nunique()

    cols = st.columns(4)
    with cols[0]:
        st.markdown(metric_card("Overall Agreement Rate", f"{overall_agreement:.1%}"), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(metric_card("Avg Time per Case", f"{avg_time:.0f}s"), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(metric_card("Total Cases Reviewed", f"{total_cases:,}"), unsafe_allow_html=True)
    with cols[3]:
        high_bias = (reviews_df.groupby("analyst_id")["agreed_with_llm"].mean() > 0.96).sum()
        badge = "RISK" if high_bias >= 3 else "OK"
        badge_color = COLOR_DANGER if high_bias >= 3 else SPOTIFY_GREEN
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; border:1px solid {SPOTIFY_GRAY}33;">
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">High-Bias Analysts</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:32px; font-weight:700; line-height:1.1;">{high_bias} / {n_analysts}</div>
                <div style="margin-top:6px;">
                    <span style="background:{badge_color}22; color:{badge_color}; padding:3px 10px; border-radius:500px; font-size:11px; font-weight:700;">{badge}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Per-analyst agreement rate + time
    st.markdown("### Per-Analyst Agreement Rate vs. Review Time")

    analyst_stats = reviews_df.groupby(["analyst_id", "analyst_name"]).agg(
        agreement_rate=("agreed_with_llm", "mean"),
        avg_time_sec=("time_to_decision_sec", "mean"),
        total_reviews=("case_id", "count"),
    ).reset_index().sort_values("agreement_rate", ascending=False)

    fig_analysts = go.Figure()

    # Agreement rate bars
    colors = [
        COLOR_DANGER if r > 0.96 else COLOR_WARNING if r > 0.93 else SPOTIFY_GREEN
        for r in analyst_stats["agreement_rate"]
    ]

    fig_analysts.add_trace(go.Bar(
        x=analyst_stats["analyst_name"],
        y=analyst_stats["agreement_rate"] * 100,
        name="Agreement Rate %",
        marker_color=colors,
        text=[f"{r:.1%}" for r in analyst_stats["agreement_rate"]],
        textposition="auto",
        textfont=dict(color=SPOTIFY_WHITE, size=13, family="Inter"),
        yaxis="y",
    ))

    # Average time line
    fig_analysts.add_trace(go.Scatter(
        x=analyst_stats["analyst_name"],
        y=analyst_stats["avg_time_sec"],
        name="Avg Time (sec)",
        mode="lines+markers",
        line=dict(color=COLOR_INFO, width=3),
        marker=dict(size=10, color=COLOR_INFO, line=dict(color=SPOTIFY_WHITE, width=2)),
        yaxis="y2",
    ))

    apply_spotify_style(fig_analysts, height=450)
    fig_analysts.update_layout(
        yaxis=dict(title="Agreement Rate (%)", side="left", range=[70, 102]),
        yaxis2=dict(title="Avg Review Time (sec)", side="right", overlaying="y",
                    gridcolor="rgba(0,0,0,0)", tickfont=dict(color=COLOR_INFO),
                    title_font=dict(color=COLOR_INFO)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        bargap=0.3,
    )

    # Add danger zone annotation
    fig_analysts.add_hline(y=96, line_dash="dash", line_color=COLOR_DANGER, line_width=1,
                           annotation_text="Bias Threshold (96%)", annotation_font_color=COLOR_DANGER)

    st.plotly_chart(fig_analysts, use_container_width=True)

    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid {SPOTIFY_GRAY}33;">
            <span style="color:{COLOR_DANGER}; font-weight:700;">Pattern detected:</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY};"> Analysts with >96% agreement rates spend an average of
            <strong style="color:{SPOTIFY_WHITE};">{analyst_stats[analyst_stats['agreement_rate'] > 0.96]['avg_time_sec'].mean():.0f} seconds</strong> per case,
            compared to <strong style="color:{SPOTIFY_WHITE};">{analyst_stats[analyst_stats['agreement_rate'] <= 0.96]['avg_time_sec'].mean():.0f} seconds</strong>
            for independent reviewers. This {analyst_stats[analyst_stats['agreement_rate'] <= 0.96]['avg_time_sec'].mean() / max(analyst_stats[analyst_stats['agreement_rate'] > 0.96]['avg_time_sec'].mean(), 1):.1f}x difference suggests high-agreement analysts are not performing thorough independent review.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Time distribution
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### Review Time Distribution")
        fig_time = go.Figure()

        # Split into high-bias and low-bias analysts
        high_bias_ids = analyst_stats[analyst_stats["agreement_rate"] > 0.96]["analyst_id"].values
        low_bias_ids = analyst_stats[analyst_stats["agreement_rate"] <= 0.96]["analyst_id"].values

        fig_time.add_trace(go.Histogram(
            x=reviews_df[reviews_df["analyst_id"].isin(high_bias_ids)]["time_to_decision_sec"],
            name="High-Bias Analysts (>96%)",
            marker_color=COLOR_DANGER, opacity=0.7, nbinsx=40,
        ))
        fig_time.add_trace(go.Histogram(
            x=reviews_df[reviews_df["analyst_id"].isin(low_bias_ids)]["time_to_decision_sec"],
            name="Independent Analysts (<=96%)",
            marker_color=SPOTIFY_GREEN, opacity=0.7, nbinsx=40,
        ))

        fig_time.add_vline(x=120, line_dash="dash", line_color=COLOR_WARNING,
                           annotation_text="2 min threshold", annotation_font_color=COLOR_WARNING)

        apply_spotify_style(fig_time, height=400)
        fig_time.update_layout(barmode="overlay", xaxis_title="Seconds", yaxis_title="Count")
        st.plotly_chart(fig_time, use_container_width=True)

    with chart_col2:
        st.markdown("### Agreement by Time of Day")

        hourly = reviews_df.groupby(["analyst_id", "review_hour"]).agg(
            agreement=("agreed_with_llm", "mean"),
        ).reset_index()

        # Pivot for heatmap
        pivot = hourly.pivot(index="analyst_id", columns="review_hour", values="agreement")
        pivot = pivot.reindex(index=analyst_stats["analyst_id"].values)

        # Use analyst names for display
        name_map = dict(zip(analyst_stats["analyst_id"], analyst_stats["analyst_name"]))
        pivot.index = [name_map.get(x, x) for x in pivot.index]

        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values * 100,
            x=[f"{h}:00" for h in pivot.columns],
            y=pivot.index,
            colorscale=[
                [0, SPOTIFY_GREEN],
                [0.5, COLOR_WARNING],
                [1, COLOR_DANGER],
            ],
            text=[[f"{v:.0f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values * 100],
            texttemplate="%{text}",
            textfont=dict(size=11, color=SPOTIFY_WHITE),
            colorbar=dict(
                title="Agree %",
                tickfont=dict(color=SPOTIFY_LIGHT_GRAY),
                title_font=dict(color=SPOTIFY_LIGHT_GRAY),
            ),
            zmin=70, zmax=100,
        ))

        apply_spotify_style(fig_heat, height=400)
        fig_heat.update_layout(xaxis_title="Hour of Day", yaxis_title="")
        st.plotly_chart(fig_heat, use_container_width=True)

    # Disagreement analysis
    st.markdown("### Disagreement Case Analysis")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "Examining the 8% of cases where analysts disagreed with the LLM — are they random or clustered?"
        "</p>",
        unsafe_allow_html=True,
    )

    disagreements = reviews_df[~reviews_df["agreed_with_llm"]]

    dis_col1, dis_col2 = st.columns(2)

    with dis_col1:
        # By analyst
        dis_by_analyst = disagreements.groupby("analyst_name").size().reset_index(name="count")
        total_by_analyst = reviews_df.groupby("analyst_name").size().reset_index(name="total")
        dis_by_analyst = dis_by_analyst.merge(total_by_analyst, on="analyst_name")
        dis_by_analyst["pct"] = dis_by_analyst["count"] / dis_by_analyst["total"] * 100

        fig_dis = go.Figure(go.Bar(
            x=dis_by_analyst["analyst_name"],
            y=dis_by_analyst["pct"],
            marker_color=[SPOTIFY_GREEN if p > 8 else COLOR_WARNING if p > 4 else COLOR_DANGER for p in dis_by_analyst["pct"]],
            text=[f"{p:.1f}%" for p in dis_by_analyst["pct"]],
            textposition="auto",
            textfont=dict(color=SPOTIFY_WHITE),
        ))
        apply_spotify_style(fig_dis, height=350)
        fig_dis.update_layout(title="Override Rate by Analyst", yaxis_title="Override %")
        st.plotly_chart(fig_dis, use_container_width=True)

    with dis_col2:
        # By fraud score range
        disagreements_with_bins = disagreements.copy()
        disagreements_with_bins["score_bin"] = pd.cut(
            disagreements_with_bins["fraud_score"],
            bins=[0.70, 0.75, 0.80, 0.85, 0.90, 0.95],
            labels=["70-75%", "75-80%", "80-85%", "85-90%", "90-95%"],
        )
        dis_by_score = disagreements_with_bins.groupby("score_bin", observed=True).size().reset_index(name="count")

        fig_score = go.Figure(go.Bar(
            x=dis_by_score["score_bin"].astype(str),
            y=dis_by_score["count"],
            marker_color=[SPOTIFY_GREEN, SPOTIFY_GREEN, COLOR_INFO, COLOR_WARNING, COLOR_DANGER],
            text=dis_by_score["count"],
            textposition="auto",
            textfont=dict(color=SPOTIFY_WHITE),
        ))
        apply_spotify_style(fig_score, height=350)
        fig_score.update_layout(title="Overrides by Fraud Score Range", xaxis_title="Score Range", yaxis_title="Count")
        st.plotly_chart(fig_score, use_container_width=True)

    # Audit finding
    st.markdown("---")
    high_bias_avg_time = analyst_stats[analyst_stats['agreement_rate'] > 0.96]['avg_time_sec'].mean()
    independent_avg_time = analyst_stats[analyst_stats['agreement_rate'] <= 0.96]['avg_time_sec'].mean()
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(245,155,35,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:24px; border-left:4px solid {COLOR_WARNING};">
            <div style="color:{COLOR_WARNING}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Observation: Potential Automation Bias in Human Review Process</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; line-height:1.6;">
                <strong>Condition:</strong> Our analysis of analyst review data identified that {high_bias} of {n_analysts} analysts exhibit agreement rates above 96% with LLM-generated recommendations,
                with an average review duration of {high_bias_avg_time:.0f} seconds per case.
                The remaining {len(low_bias_ids)} analysts, who demonstrate lower agreement rates, spend an average of {independent_avg_time:.0f} seconds per case.
                Analyst override decisions are disproportionately concentrated among this latter group.<br><br>
                <strong>Criteria:</strong> The design intent of the human review zone (scores between 70-95%) is to provide independent human judgment for cases where the ML model has insufficient confidence to make an automated determination.
                Emerging regulatory frameworks, including the EU AI Act (Article 14), emphasize the importance of effective human oversight for AI systems involved in consequential decision-making.
                Additionally, academic research on automation bias identifies high agreement rates combined with short review durations as indicators warranting further investigation.<br><br>
                <strong>Cause:</strong> Based on our review, no formal automation bias monitoring program exists. Challenge cases with known outcomes are not seeded into the review queue to independently assess analyst judgment.
                The current review workflow and user interface design have not been evaluated for potential anchoring effects (e.g., whether analysts see the LLM recommendation before forming an independent assessment).<br><br>
                <strong>Effect:</strong> The observed patterns raise questions about whether the human review control is operating as designed for cases handled by high-agreement analysts.
                If the human review is not providing meaningful independent oversight, the effectiveness of this key control layer may be diminished.
                This warrants attention given the financial impact of review-zone decisions on royalty payments and the importance of demonstrable human oversight for regulatory compliance purposes.<br><br>
                <strong>Recommendation:</strong> (1) <strong>Replace narrative-based review with a structured signal confirmation card.</strong>
                Instead of presenting analysts with a completed LLM summary and recommendation, present the raw signal values (account age, device diversity, VPN status, play duration, skip rate, geographic concentration, IP clustering, track count)
                as a lightweight card with binary Y/N assessments per signal. The analyst evaluates each signal independently, records their classification, and only then sees the AI recommendation.
                This takes approximately the same time as reading an LLM summary (~60-90 seconds), eliminates anchoring bias, requires zero free-text writing, and produces structured auditable data per case.<br><br>
                (2) <strong>Implement a challenge case program</strong> — periodically seed the review queue (e.g., 5% of cases) with pre-labeled cases of known outcomes to objectively measure analyst independence.
                This provides the ground truth needed to distinguish between genuine calibration and over-reliance.<br><br>
                (3) <strong>Establish per-analyst performance monitoring</strong> as a standard management practice, tracking agreement rates, review duration, signal-level assessment patterns, and override rates.
                The signal confirmation card naturally produces this data without additional reporting burden on analysts.<br><br>
                (4) <strong>Conduct periodic quality reviews</strong> on a random sample of completed signal cards to verify that analyst assessments are consistent with the displayed signal values.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Signal Confirmation Card mockup
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("### Proposed: Signal Confirmation Card")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "Replace the current LLM-summary-first workflow with a structured signal card. "
        "Analysts assess each signal independently before seeing the AI recommendation."
        "</p>",
        unsafe_allow_html=True,
    )

    import streamlit.components.v1 as components
    signal_card_html = """
    <html><head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body { font-family: 'Inter', monospace; background: #181818; color: #fff; margin: 0; padding: 24px; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        td { padding: 10px 0; }
        .yes { background: rgba(232,17,91,0.2); color: #E8115B; padding: 3px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .no { background: rgba(29,185,84,0.2); color: #1DB954; padding: 3px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .btn-q { background: #E8115B; color: #000; padding: 6px 20px; border-radius: 500px; font-weight: 700; font-size: 13px; margin-right: 8px; cursor: pointer; border: none; }
        .btn-m { background: rgba(83,83,83,0.4); color: #fff; padding: 6px 20px; border-radius: 500px; font-weight: 600; font-size: 13px; margin-right: 8px; cursor: pointer; border: none; }
    </style>
    </head><body>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid rgba(83,83,83,0.3); padding-bottom:12px;">
        <span style="font-size:16px; font-weight:700;">CASE #12345</span>
        <span style="color:#B3B3B3; font-size:13px;">Fraud Score: 87.3%</span>
    </div>
    <table>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.3);">
            <td style="color:#B3B3B3; width:35%;">SIGNAL</td>
            <td style="color:#B3B3B3; width:30%;">VALUE</td>
            <td style="color:#B3B3B3; width:35%;">FRAUD INDICATOR?</td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Account age</td><td style="color:#E8115B; font-weight:600;">12 days</td><td><span class="yes">YES</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Devices used</td><td style="color:#E8115B; font-weight:600;">1</td><td><span class="yes">YES</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Avg play duration</td><td style="font-weight:600;">185 sec</td><td><span class="no">NO</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Unique tracks/day</td><td style="color:#E8115B; font-weight:600;">589</td><td><span class="yes">YES</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Skip rate</td><td style="color:#F59B23; font-weight:600;">4%</td><td><span class="yes">YES</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>VPN detected</td><td style="color:#E8115B; font-weight:600;">Yes</td><td><span class="yes">YES</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Locations (24hr)</td><td style="color:#E8115B; font-weight:600;">8 countries</td><td><span class="yes">YES</span></td>
        </tr>
        <tr style="border-bottom:1px solid rgba(83,83,83,0.15);">
            <td>Same-IP accounts</td><td style="color:#E8115B; font-weight:600;">47</td><td><span class="yes">YES</span></td>
        </tr>
    </table>
    <div style="margin-top:16px; padding-top:16px; border-top:1px solid rgba(83,83,83,0.3); display:flex; justify-content:space-between; align-items:center;">
        <span style="color:#B3B3B3;">Fraud signals: <strong style="color:#E8115B;">7/8</strong></span>
        <div>
            <button class="btn-q">Quarantine</button>
            <button class="btn-m">Monitor</button>
            <button class="btn-m">Clear</button>
        </div>
    </div>
    <div style="margin-top:12px; padding:12px; background:rgba(83,83,83,0.15); border-radius:6px;">
        <span style="color:#B3B3B3; font-size:12px; font-style:italic;">AI recommendation revealed after analyst submits their decision</span>
    </div>
    <div style="margin-top:20px; padding:16px; background:#121212; border-radius:8px;">
        <strong style="color:#1DB954;">Why this works under volume constraints:</strong><br>
        <span style="color:#B3B3B3; font-size:13px; line-height:1.6;">
        8 binary clicks + 1 decision button = ~60-90 seconds per case. No free-text writing required.
        At 200 cases/day, this represents approximately 3.5 hours of focused review time &mdash; comparable to the current workflow,
        but with verifiable evidence of independent signal assessment.
        </span>
    </div>
    </body></html>
    """
    components.html(signal_card_html, height=620, scrolling=False)
