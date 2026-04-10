"""Module 3: Model Drift Monitor — The most critical finding."""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card,
)

CATALOG_ACQUISITION_DAY = 120
LAST_RETRAIN_DAY = 0  # Model was retrained at the start of our data window


def render(perf_df: pd.DataFrame, events_df: pd.DataFrame = None):
    st.markdown("## Model Drift Monitor")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Continuous monitoring of ML model health. Detects performance degradation "
        "after the catalog acquisition that changed platform content distribution."
        "</p>",
        unsafe_allow_html=True,
    )

    # Key dates
    dates = pd.to_datetime(perf_df["date"])
    acq_date = dates.iloc[CATALOG_ACQUISITION_DAY]

    # Pre/Post metrics
    pre = perf_df.iloc[:CATALOG_ACQUISITION_DAY]
    post = perf_df.iloc[CATALOG_ACQUISITION_DAY:]

    # Top metrics row
    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            metric_card(
                "Current Precision",
                f"{post['precision'].iloc[-7:].mean():.1%}",
                delta=round((post['precision'].iloc[-7:].mean() - pre['precision'].mean()) * 100, 1),
                delta_color="bad",
            ),
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            metric_card(
                "Current Recall",
                f"{post['recall'].iloc[-7:].mean():.1%}",
                delta=round((post['recall'].iloc[-7:].mean() - pre['recall'].mean()) * 100, 1),
                delta_color="bad",
            ),
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            metric_card(
                "False Positive Rate",
                f"{post['false_positive_rate'].iloc[-7:].mean():.1%}",
                delta=round((post['false_positive_rate'].iloc[-7:].mean() - pre['false_positive_rate'].mean()) * 100, 1),
                delta_color="bad",
            ),
            unsafe_allow_html=True,
        )
    with cols[3]:
        psi_current = post['psi_score'].iloc[-7:].mean()
        psi_status = "CRITICAL" if psi_current > 0.15 else "WARNING" if psi_current > 0.10 else "OK"
        badge_color = COLOR_DANGER if psi_status == "CRITICAL" else COLOR_WARNING if psi_status == "WARNING" else SPOTIFY_GREEN
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; border:1px solid {SPOTIFY_GRAY}33;">
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">PSI Drift Score</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:32px; font-weight:700; line-height:1.1;">{psi_current:.3f}</div>
                <div style="margin-top:6px;">
                    <span style="background:{badge_color}22; color:{badge_color}; padding:3px 10px; border-radius:500px; font-size:11px; font-weight:700; letter-spacing:0.5px;">{psi_status}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Main performance chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
        subplot_titles=("Model Performance Metrics", "Population Stability Index (PSI)"),
    )

    # Precision
    fig.add_trace(
        go.Scatter(
            x=dates, y=perf_df["precision"],
            name="Precision", line=dict(color=SPOTIFY_GREEN, width=2),
            hovertemplate="Precision: %{y:.3f}<extra></extra>",
        ), row=1, col=1,
    )
    # Recall
    fig.add_trace(
        go.Scatter(
            x=dates, y=perf_df["recall"],
            name="Recall", line=dict(color=COLOR_INFO, width=2),
            hovertemplate="Recall: %{y:.3f}<extra></extra>",
        ), row=1, col=1,
    )
    # F1
    fig.add_trace(
        go.Scatter(
            x=dates, y=perf_df["f1_score"],
            name="F1 Score", line=dict(color=COLOR_WARNING, width=2, dash="dot"),
            hovertemplate="F1: %{y:.3f}<extra></extra>",
        ), row=1, col=1,
    )

    # PSI
    fig.add_trace(
        go.Scatter(
            x=dates, y=perf_df["psi_score"],
            name="PSI", line=dict(color="#AF2896", width=2),
            fill="tozeroy", fillcolor="rgba(175,40,150,0.15)",
            hovertemplate="PSI: %{y:.3f}<extra></extra>",
        ), row=2, col=1,
    )

    # PSI threshold lines
    fig.add_hline(y=0.10, line_dash="dash", line_color=COLOR_WARNING, line_width=1,
                  annotation_text="Warning (0.10)", annotation_font_color=COLOR_WARNING, row=2, col=1)
    fig.add_hline(y=0.20, line_dash="dash", line_color=COLOR_DANGER, line_width=1,
                  annotation_text="Critical (0.20)", annotation_font_color=COLOR_DANGER, row=2, col=1)

    # Catalog acquisition vertical line on both subplots
    for row in [1, 2]:
        fig.add_vline(
            x=acq_date, line_dash="dash", line_color=COLOR_DANGER, line_width=2,
            row=row, col=1,
        )

    # Annotation for catalog acquisition
    fig.add_annotation(
        x=acq_date, y=0.96,
        text="Catalog Acquisition",
        showarrow=True, arrowhead=2, arrowcolor=COLOR_DANGER,
        font=dict(color=COLOR_DANGER, size=12, family="Inter"),
        bgcolor=f"{SPOTIFY_CARD_BG}",
        bordercolor=COLOR_DANGER,
        borderwidth=1,
        borderpad=6,
        row=1, col=1,
    )

    apply_spotify_style(fig, height=580)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_yaxes(title_text="Score", row=1, col=1)
    fig.update_yaxes(title_text="PSI", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # False positive rate over time
    st.markdown("### False Positive Rate Trend")

    fig_fpr = go.Figure()
    fig_fpr.add_trace(
        go.Scatter(
            x=dates, y=perf_df["false_positive_rate"] * 100,
            name="False Positive Rate %",
            line=dict(color=COLOR_DANGER, width=2),
            fill="tozeroy", fillcolor="rgba(232,17,91,0.12)",
        )
    )
    fig_fpr.add_vline(x=acq_date, line_dash="dash", line_color=COLOR_DANGER, line_width=2)
    fig_fpr.add_annotation(
        x=acq_date, y=perf_df["false_positive_rate"].max() * 100,
        text="Catalog Acquisition", showarrow=True, arrowhead=2,
        arrowcolor=COLOR_DANGER,
        font=dict(color=COLOR_DANGER, size=12),
        bgcolor=SPOTIFY_CARD_BG, bordercolor=COLOR_DANGER, borderwidth=1, borderpad=6,
    )
    apply_spotify_style(fig_fpr, height=350)
    fig_fpr.update_layout(yaxis_title="False Positive Rate (%)", xaxis_title="Date")
    st.plotly_chart(fig_fpr, use_container_width=True)

    # Quarantine volume trend
    st.markdown("### Stream Classification Volume")

    fig_vol = go.Figure()
    fig_vol.add_trace(
        go.Scatter(
            x=dates, y=perf_df["quarantine_count"],
            name="Quarantined", stackgroup="one",
            line=dict(color=COLOR_DANGER, width=0), fillcolor="rgba(232,17,91,0.6)",
        )
    )
    fig_vol.add_trace(
        go.Scatter(
            x=dates, y=perf_df["review_count"],
            name="Review Zone", stackgroup="one",
            line=dict(color=COLOR_WARNING, width=0), fillcolor="rgba(245,155,35,0.6)",
        )
    )
    fig_vol.add_vline(x=acq_date, line_dash="dash", line_color=SPOTIFY_WHITE, line_width=1)

    apply_spotify_style(fig_vol, height=350)
    fig_vol.update_layout(yaxis_title="Stream Count", xaxis_title="Date")
    st.plotly_chart(fig_vol, use_container_width=True)

    # Catalog Impact Analysis
    if events_df is not None:
        st.markdown("### Catalog Acquisition Impact Analysis")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Comparing false positive rates between existing content and newly acquired catalog content. "
            "New catalog content — particularly in acquired genres — is disproportionately flagged by the model."
            "</p>",
            unsafe_allow_html=True,
        )

        post_acq_events = events_df[events_df["timestamp"] >= acq_date]
        if len(post_acq_events) > 0:
            # FP rates by catalog status
            legit_events = post_acq_events[~post_acq_events["is_actually_fraudulent"]]

            existing_legit = legit_events[~legit_events["is_new_catalog"]]
            new_cat_legit = legit_events[legit_events["is_new_catalog"]]

            existing_fp = (existing_legit["classification"].isin(["quarantine", "review"])).mean() if len(existing_legit) > 0 else 0
            new_cat_fp = (new_cat_legit["classification"].isin(["quarantine", "review"])).mean() if len(new_cat_legit) > 0 else 0

            cat_col1, cat_col2 = st.columns(2)

            with cat_col1:
                # FP rate comparison
                fig_cat = go.Figure()
                fig_cat.add_trace(go.Bar(
                    x=["Existing Content", "New Catalog Content"],
                    y=[existing_fp * 100, new_cat_fp * 100],
                    marker_color=[SPOTIFY_GREEN, COLOR_DANGER],
                    text=[f"{existing_fp:.1%}", f"{new_cat_fp:.1%}"],
                    textposition="auto",
                    textfont=dict(color=SPOTIFY_WHITE, size=14),
                ))
                apply_spotify_style(fig_cat, height=380)
                fig_cat.update_layout(
                    title="False Flag Rate: Existing vs. New Catalog (Legitimate Streams Only)",
                    yaxis_title="% Legitimate Streams Incorrectly Flagged",
                    bargap=0.4,
                )
                st.plotly_chart(fig_cat, use_container_width=True)

            with cat_col2:
                # FP rate by genre for new catalog
                acquired_genres = {"latin", "classical", "regional-folk", "cumbia"}
                genre_groups = legit_events.groupby("genre")
                genre_fp_records = []
                for genre_name, group in genre_groups:
                    if len(group) > 50:
                        genre_fp_records.append({
                            "genre": genre_name,
                            "fp_rate": group["classification"].isin(["quarantine", "review"]).mean(),
                            "count": len(group),
                            "is_acquired_genre": genre_name in acquired_genres,
                        })
                genre_fp = pd.DataFrame(genre_fp_records).sort_values("fp_rate", ascending=True)

                fig_genre = go.Figure()
                fig_genre.add_trace(go.Bar(
                    x=genre_fp["fp_rate"] * 100,
                    y=genre_fp["genre"],
                    orientation="h",
                    marker_color=[COLOR_DANGER if v else SPOTIFY_GREEN for v in genre_fp["is_acquired_genre"]],
                    text=[f"{r:.1%}" for r in genre_fp["fp_rate"]],
                    textposition="auto",
                    textfont=dict(color=SPOTIFY_WHITE, size=12),
                ))
                apply_spotify_style(fig_genre, height=380)
                fig_genre.update_layout(
                    title="False Flag Rate by Genre (Post-Acquisition)",
                    xaxis_title="% Legitimate Streams Incorrectly Flagged",
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_genre, use_container_width=True)

            # Explanation card
            ratio = new_cat_fp / existing_fp if existing_fp > 0 else 0
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2);">
                    <span style="color:{COLOR_DANGER}; font-weight:700;">Key insight:</span>
                    <span style="color:{SPOTIFY_LIGHT_GRAY};"> Legitimate streams from newly acquired catalog content are flagged at
                    <strong style="color:{SPOTIFY_WHITE};">{ratio:.1f}x the rate</strong> of existing content.
                    Acquired genres (Latin, Classical, Regional Folk, Cumbia) show the highest false flag rates.
                    This is consistent with the model applying pre-acquisition patterns to content with legitimately different characteristics —
                    different listening durations, concentrated regional fanbases, and new artist profiles that the model has not been trained on.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # How catalog breaks each signal category
        st.markdown("#### Why New Catalog Content Triggers False Positives")
        st.markdown(
            f"""
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:8px;">
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px; border:1px solid rgba(83,83,83,0.2);">
                    <div style="color:{COLOR_INFO}; font-weight:700; font-size:13px; margin-bottom:8px;">Listening Behavior</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                        <span style="color:{SPOTIFY_WHITE};">Model learned:</span> Normal play duration is 120-180s, skip rate 15-30%<br>
                        <span style="color:{COLOR_DANGER};">New catalog reality:</span> Folk songs run 200s+, classical pieces 280s+. Regional fans play long playlists with low skip rates — looks identical to bot behavior
                    </div>
                </div>
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px; border:1px solid rgba(83,83,83,0.2);">
                    <div style="color:{COLOR_WARNING}; font-weight:700; font-size:13px; margin-bottom:8px;">Account Characteristics</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                        <span style="color:{SPOTIFY_WHITE};">Model learned:</span> Legitimate accounts are months/years old with filled profiles<br>
                        <span style="color:{COLOR_DANGER};">New catalog reality:</span> Artists are new to platform, minimal profiles, zero history — indistinguishable from bot accounts
                    </div>
                </div>
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px; border:1px solid rgba(83,83,83,0.2);">
                    <div style="color:{SPOTIFY_GREEN}; font-weight:700; font-size:13px; margin-bottom:8px;">Geographic Signals</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                        <span style="color:{SPOTIFY_WHITE};">Model learned:</span> Geographic clustering = bot farm in one location<br>
                        <span style="color:{COLOR_DANGER};">New catalog reality:</span> Regional artist with real concentrated fanbase (e.g., Colombian cumbia popular only in Colombia/Ecuador)
                    </div>
                </div>
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px; border:1px solid rgba(83,83,83,0.2);">
                    <div style="color:#AF2896; font-weight:700; font-size:13px; margin-bottom:8px;">Network Signals</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                        <span style="color:{SPOTIFY_WHITE};">Model learned:</span> Many accounts from same IP range = coordinated bot operation<br>
                        <span style="color:{COLOR_DANGER};">New catalog reality:</span> In some regions, hundreds of legitimate users share ISP infrastructure — apartment buildings, universities, shared networks
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Audit finding summary
    st.markdown("---")
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(232,17,91,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:24px; border-left:4px solid {COLOR_DANGER};">
            <div style="color:{COLOR_DANGER}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Observation: ML Model Performance Degradation</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; line-height:1.6;">
                <strong>Condition:</strong> Based on our analysis, model precision has declined from <strong>94.0%</strong> to <strong>{post['precision'].iloc[-7:].mean():.1%}</strong>
                (a decrease of {abs(post['precision'].iloc[-7:].mean() - pre['precision'].mean()) * 100:.1f} percentage points) following the catalog acquisition on {acq_date.strftime('%B %d, %Y')}.
                The Population Stability Index (PSI) of <strong>{psi_current:.3f}</strong> exceeds the commonly accepted threshold of 0.20, indicating significant distribution shift in the model's input data.<br><br>
                <strong>Criteria:</strong> The NIST AI Risk Management Framework (Measure function) calls for continuous monitoring of AI system performance metrics, with re-evaluation triggered when material changes occur in the operating environment.
                ISACA guidance on AI model lifecycle governance similarly emphasizes the need for retraining protocols when underlying data distributions change materially.<br><br>
                <strong>Cause:</strong> The ML model has not been retrained since its last update approximately four months ago. Following the catalog acquisition, which altered the distribution of content on the platform, no model performance evaluation or retraining was initiated. Management has indicated that retraining is planned for next quarter.<br><br>
                <strong>Effect:</strong> The observed false positive rate has increased from approximately 2.8% to {post['false_positive_rate'].iloc[-7:].mean() * 100:.1f}% in our sample data.
                If this pattern holds at production scale, the increase could result in a material number of legitimate streams being incorrectly quarantined, with corresponding delays in royalty payments to rights holders.
                The timing of this degradation is consistent with the recently reported label dispute involving quarantined streams from a viral campaign, though further analysis would be needed to confirm a direct connection.<br><br>
                <strong>Recommendation:</strong> Management should evaluate the need for expedited model retraining using post-acquisition data, ahead of the currently planned next-quarter timeline.
                We further recommend implementing automated distribution monitoring (e.g., PSI tracking) with defined alerting thresholds, and establishing a policy requiring model performance evaluation within a defined period following significant platform changes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
