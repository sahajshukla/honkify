"""Module 1: Threshold Sensitivity Analyzer — Interactive what-if analysis."""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card,
)


def render(events_df: pd.DataFrame):
    st.markdown("## Threshold Sensitivity Analyzer")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Explore how adjusting StreamShield's classification thresholds impacts false positive rates, "
        "false negative rates, review volume, and estimated financial impact. The current thresholds "
        "(70% / 95%) were set by engineering without formal business stakeholder approval."
        "</p>",
        unsafe_allow_html=True,
    )

    # Threshold controls
    st.markdown(
        f'<div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px 24px; '
        f'border:1px solid {SPOTIFY_GRAY}33; margin-bottom:20px;">'
        f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:12px;">'
        "Adjust Classification Thresholds</div></div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        review_threshold = st.slider(
            "Review Zone Lower Bound",
            min_value=0.50, max_value=0.90, value=0.70, step=0.01,
            format="%.0f%%",
            help="Streams above this score enter the human review zone",
        )
    with col2:
        quarantine_threshold = st.slider(
            "Auto-Quarantine Threshold",
            min_value=0.80, max_value=0.99, value=0.95, step=0.01,
            format="%.0f%%",
            help="Streams above this score are automatically quarantined",
        )

    if quarantine_threshold <= review_threshold:
        st.error("Quarantine threshold must be higher than review threshold.")
        return

    # Classify at current thresholds
    scores = events_df["fraud_score"].values
    truth = events_df["is_actually_fraudulent"].values

    # Current (default) classification
    default_pred = np.where(scores > 0.95, 1, np.where(scores > 0.70, -1, 0))  # 1=quarantine, -1=review, 0=pass

    # User-adjusted classification
    adj_pred = np.where(scores > quarantine_threshold, 1, np.where(scores > review_threshold, -1, 0))

    # For binary metrics: quarantine + review = "flagged"
    default_flagged = (default_pred != 0).astype(int)
    adj_flagged = (adj_pred != 0).astype(int)

    # Metrics
    def calc_metrics(flagged, quarantined_mask, truth):
        tp = np.sum((flagged == 1) & (truth == True))
        fp = np.sum((flagged == 1) & (truth == False))
        fn = np.sum((flagged == 0) & (truth == True))
        tn = np.sum((flagged == 0) & (truth == False))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        n_quarantine = np.sum(quarantined_mask)
        n_review = np.sum(flagged) - n_quarantine
        n_pass = np.sum(flagged == 0)
        royalties_blocked_legit = fp * 0.004 * 150  # avg $0.004/stream * ~150 streams represented per record
        royalties_leaked_fraud = fn * 0.004 * 150
        return {
            "precision": precision, "recall": recall, "fpr": fpr,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "n_quarantine": int(n_quarantine), "n_review": int(n_review), "n_pass": int(n_pass),
            "royalties_blocked_legit": royalties_blocked_legit,
            "royalties_leaked_fraud": royalties_leaked_fraud,
        }

    default_metrics = calc_metrics(default_flagged, default_pred == 1, truth)
    adj_metrics = calc_metrics(adj_flagged, adj_pred == 1, truth)

    # Metrics comparison
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    cols = st.columns(4)
    labels_values = [
        ("False Positive Rate", f"{adj_metrics['fpr']:.2%}", round((adj_metrics['fpr'] - default_metrics['fpr']) * 100, 2), "bad" if adj_metrics['fpr'] > default_metrics['fpr'] else "good"),
        ("Fraud Caught (Recall)", f"{adj_metrics['recall']:.2%}", round((adj_metrics['recall'] - default_metrics['recall']) * 100, 2), "good" if adj_metrics['recall'] > default_metrics['recall'] else "bad"),
        ("Review Queue Volume", f"{adj_metrics['n_review']:,}", round((adj_metrics['n_review'] - default_metrics['n_review']) / max(default_metrics['n_review'], 1) * 100, 1), "normal"),
        ("Est. Legit Royalties Blocked", f"${adj_metrics['royalties_blocked_legit']:,.0f}", round((adj_metrics['royalties_blocked_legit'] - default_metrics['royalties_blocked_legit']) / max(default_metrics['royalties_blocked_legit'], 1) * 100, 1), "bad" if adj_metrics['royalties_blocked_legit'] > default_metrics['royalties_blocked_legit'] else "good"),
    ]

    for i, (label, val, delta, dc) in enumerate(labels_values):
        with cols[i]:
            st.markdown(metric_card(label, val, delta, dc), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Two charts side by side
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Stream classification breakdown
        fig_class = go.Figure()
        for label, data, colors in [
            ("Default (70/95)", default_metrics, [COLOR_DANGER, COLOR_WARNING, SPOTIFY_GREEN]),
            ("Adjusted", adj_metrics, ["rgba(232,17,91,0.6)", "rgba(245,155,35,0.6)", "rgba(29,185,84,0.6)"]),
        ]:
            fig_class.add_trace(go.Bar(
                x=["Quarantine", "Review", "Pass"],
                y=[data["n_quarantine"], data["n_review"], data["n_pass"]],
                name=label,
                marker_color=colors,
                text=[f"{data['n_quarantine']:,}", f"{data['n_review']:,}", f"{data['n_pass']:,}"],
                textposition="auto",
                textfont=dict(color=SPOTIFY_WHITE, size=12),
            ))
        apply_spotify_style(fig_class, height=400)
        fig_class.update_layout(
            title="Stream Classification Distribution",
            barmode="group",
            yaxis_title="Number of Streams",
        )
        st.plotly_chart(fig_class, use_container_width=True)

    with chart_col2:
        # Confusion matrix heatmap
        cm_labels = ["Legitimate", "Fraudulent"]
        cm = np.array([
            [adj_metrics["tn"], adj_metrics["fp"]],
            [adj_metrics["fn"], adj_metrics["tp"]],
        ])
        fig_cm = go.Figure(go.Heatmap(
            z=cm,
            x=["Predicted Legit", "Predicted Fraud"],
            y=["Actually Legit", "Actually Fraud"],
            text=[[f"{v:,}" for v in row] for row in cm],
            texttemplate="%{text}",
            textfont=dict(size=16, color=SPOTIFY_WHITE),
            colorscale=[[0, SPOTIFY_CARD_BG], [0.5, "rgba(29,185,84,0.4)"], [1, SPOTIFY_GREEN]],
            showscale=False,
        ))
        apply_spotify_style(fig_cm, height=400)
        fig_cm.update_layout(
            title="Confusion Matrix (Adjusted Thresholds)",
            xaxis=dict(side="bottom"),
        )
        st.plotly_chart(fig_cm, use_container_width=True)

    # ROC Curve
    st.markdown("### ROC Curve & Precision-Recall Trade-off")

    roc_col, pr_col = st.columns(2)

    with roc_col:
        fpr_curve, tpr_curve, _ = roc_curve(truth.astype(int), scores)
        roc_auc = auc(fpr_curve, tpr_curve)

        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(
            x=fpr_curve, y=tpr_curve,
            name=f"ROC (AUC = {roc_auc:.3f})",
            line=dict(color=SPOTIFY_GREEN, width=2),
            fill="tozeroy", fillcolor="rgba(29,185,84,0.08)",
        ))
        fig_roc.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1], name="Random",
            line=dict(color=SPOTIFY_GRAY, width=1, dash="dash"),
        ))

        # Mark current operating point
        current_fpr = adj_metrics["fpr"]
        current_tpr = adj_metrics["recall"]
        fig_roc.add_trace(go.Scatter(
            x=[current_fpr], y=[current_tpr],
            mode="markers", name="Current Operating Point",
            marker=dict(color=COLOR_DANGER, size=12, symbol="circle",
                        line=dict(color=SPOTIFY_WHITE, width=2)),
        ))

        apply_spotify_style(fig_roc, height=400)
        fig_roc.update_layout(
            title="ROC Curve",
            xaxis_title="False Positive Rate",
            yaxis_title="True Positive Rate",
        )
        st.plotly_chart(fig_roc, use_container_width=True)

    with pr_col:
        prec_curve, rec_curve, _ = precision_recall_curve(truth.astype(int), scores)

        fig_pr = go.Figure()
        fig_pr.add_trace(go.Scatter(
            x=rec_curve, y=prec_curve,
            name="Precision-Recall",
            line=dict(color=COLOR_INFO, width=2),
            fill="tozeroy", fillcolor="rgba(80,155,245,0.08)",
        ))

        # Mark current point
        fig_pr.add_trace(go.Scatter(
            x=[adj_metrics["recall"]], y=[adj_metrics["precision"]],
            mode="markers", name="Current Operating Point",
            marker=dict(color=COLOR_DANGER, size=12, symbol="circle",
                        line=dict(color=SPOTIFY_WHITE, width=2)),
        ))

        apply_spotify_style(fig_pr, height=400)
        fig_pr.update_layout(
            title="Precision-Recall Curve",
            xaxis_title="Recall (Fraud Caught)",
            yaxis_title="Precision",
        )
        st.plotly_chart(fig_pr, use_container_width=True)

    # Score distribution
    st.markdown("### Fraud Score Distribution")

    fig_dist = go.Figure()

    legit_scores = scores[~truth]
    fraud_scores_vals = scores[truth]

    fig_dist.add_trace(go.Histogram(
        x=legit_scores, nbinsx=80, name="Legitimate Streams",
        marker_color=SPOTIFY_GREEN, opacity=0.7,
    ))
    fig_dist.add_trace(go.Histogram(
        x=fraud_scores_vals, nbinsx=80, name="Fraudulent Streams",
        marker_color=COLOR_DANGER, opacity=0.7,
    ))

    # Threshold lines
    fig_dist.add_vline(x=review_threshold, line_dash="dash", line_color=COLOR_WARNING, line_width=2,
                       annotation_text=f"Review ({review_threshold:.0%})",
                       annotation_font_color=COLOR_WARNING)
    fig_dist.add_vline(x=quarantine_threshold, line_dash="dash", line_color=COLOR_DANGER, line_width=2,
                       annotation_text=f"Quarantine ({quarantine_threshold:.0%})",
                       annotation_font_color=COLOR_DANGER)

    apply_spotify_style(fig_dist, height=400)
    fig_dist.update_layout(
        barmode="overlay",
        xaxis_title="Fraud Score",
        yaxis_title="Count",
    )
    st.plotly_chart(fig_dist, use_container_width=True)

    # Governance finding
    st.markdown("---")
    is_different = (review_threshold != 0.70) or (quarantine_threshold != 0.95)
    comparison_text = ""
    if is_different:
        fp_delta = adj_metrics["fp"] - default_metrics["fp"]
        fn_delta = adj_metrics["fn"] - default_metrics["fn"]
        comparison_text = f"""<br><br>
        <strong>Illustrative Sensitivity Analysis:</strong> Adjusting thresholds from 70%/95% to {review_threshold:.0%}/{quarantine_threshold:.0%}
        results in a change of <strong>{abs(fp_delta):,}</strong> false positives ({"increase" if fp_delta > 0 else "decrease"}) and
        <strong>{abs(fn_delta):,}</strong> false negatives ({"increase" if fn_delta > 0 else "decrease"}) in our sample.
        This illustrates that threshold selection involves material tradeoffs that should be evaluated and approved by relevant business stakeholders."""

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(245,155,35,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:24px; border-left:4px solid {COLOR_WARNING};">
            <div style="color:{COLOR_WARNING}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">Observation: Classification Threshold Governance</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; line-height:1.6;">
                <strong>Condition:</strong> The classification thresholds (70% for review zone entry, 95% for auto-quarantine) were established by the engineering team during initial deployment based on their testing. These thresholds have not been formally reviewed or approved by business stakeholders (Finance, Legal, Content) since launch, and no documented rationale for the selected values was identified.<br><br>
                <strong>Criteria:</strong> Parameters governing automated controls with potential financial impact should be supported by documented design rationale, approved by appropriate business owners, and subject to periodic review. This is consistent with SOX internal control standards for application controls, as well as the NIST AI RMF Govern function, which emphasizes accountability and documented decision-making for AI system parameters.<br><br>
                <strong>Cause:</strong> A threshold governance framework was not established as part of the initial deployment process. No sensitivity analysis was conducted at the time of deployment or subsequently to quantify the impact of threshold selection on false positive and false negative rates.<br><br>
                <strong>Effect:</strong> These thresholds determine the classification of streams into quarantine, review, and pass categories, which in turn affects royalty calculations, chart positions, and recommendation algorithm inputs.
                In our sample of {len(events_df):,} streams, <strong>{default_metrics['fp']:,}</strong> legitimate streams were classified above the review threshold.
                Without a formal governance process, there is limited assurance that the current thresholds reflect an appropriate balance between fraud detection effectiveness and the risk of incorrectly impacting legitimate streams.
                {comparison_text}<br><br>
                <strong>Recommendation:</strong> Establish a formal threshold review and approval process involving relevant business stakeholders (Finance, Legal, Content & Rights). Conduct periodic sensitivity analysis to inform threshold decisions. Document the rationale for threshold selections and any subsequent changes through a change management process. Consider incorporating threshold review into the existing SOX control testing program.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
