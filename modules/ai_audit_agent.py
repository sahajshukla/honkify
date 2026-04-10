"""Module 4: AI Audit Agent — AI-powered finding generation."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_LOW,
    metric_card,
)


def _get_data_summary(events_df, reviews_df, perf_df, appeals_df):
    """Create a structured data summary for the AI agent."""
    # Model drift stats
    pre_acq = perf_df.iloc[:120]
    post_acq = perf_df.iloc[120:]

    # Analyst bias stats
    analyst_stats = reviews_df.groupby("analyst_name").agg(
        agreement_rate=("agreed_with_llm", "mean"),
        avg_time=("time_to_decision_sec", "mean"),
        count=("case_id", "count"),
    ).reset_index()

    # Appeal stats
    appeal_by_type = appeals_df.groupby("artist_type").agg(
        avg_days=("days_to_resolve", "mean"),
        overturn_rate=("outcome", lambda x: (x == "overturned").mean()),
        count=("appeal_id", "count"),
    ).reset_index()

    # FP analysis
    quarantined = events_df[events_df["classification"] == "quarantine"]
    fp_rate = (~quarantined["is_actually_fraudulent"]).mean() if len(quarantined) > 0 else 0

    summary = {
        "model_performance": {
            "pre_acquisition_precision": round(pre_acq["precision"].mean(), 4),
            "post_acquisition_precision": round(post_acq["precision"].mean(), 4),
            "precision_drop_pct": round((pre_acq["precision"].mean() - post_acq["precision"].mean()) * 100, 2),
            "current_fpr": round(post_acq["false_positive_rate"].iloc[-7:].mean(), 4),
            "pre_fpr": round(pre_acq["false_positive_rate"].mean(), 4),
            "current_psi": round(post_acq["psi_score"].iloc[-7:].mean(), 4),
            "days_since_retrain": 120 + len(post_acq),
        },
        "analyst_behavior": {
            "overall_agreement_rate": round(reviews_df["agreed_with_llm"].mean(), 4),
            "analysts_above_96pct": int((analyst_stats["agreement_rate"] > 0.96).sum()),
            "total_analysts": len(analyst_stats),
            "high_bias_avg_time_sec": round(analyst_stats[analyst_stats["agreement_rate"] > 0.96]["avg_time"].mean(), 1),
            "independent_avg_time_sec": round(analyst_stats[analyst_stats["agreement_rate"] <= 0.96]["avg_time"].mean(), 1),
            "per_analyst": analyst_stats.to_dict("records"),
        },
        "appeals": {
            "total_appeals": len(appeals_df),
            "overall_overturn_rate": round((appeals_df["outcome"] == "overturned").mean(), 4),
            "avg_resolution_days": round(appeals_df["days_to_resolve"].mean(), 1),
            "by_artist_type": appeal_by_type.to_dict("records"),
        },
        "classification": {
            "total_streams": len(events_df),
            "quarantine_rate": round((events_df["classification"] == "quarantine").mean(), 4),
            "review_rate": round((events_df["classification"] == "review").mean(), 4),
            "pass_rate": round((events_df["classification"] == "pass").mean(), 4),
            "actual_fraud_rate": round(events_df["is_actually_fraudulent"].mean(), 4),
            "quarantine_false_positive_rate": round(fp_rate, 4),
        },
    }
    return summary


RISK_MATRIX = {
    "Model Drift": {"likelihood": 5, "impact": 5, "category": "Technology"},
    "False Positives": {"likelihood": 4, "impact": 5, "category": "Financial"},
    "Threshold Governance": {"likelihood": 5, "impact": 4, "category": "Operational"},
    "Automation Bias": {"likelihood": 4, "impact": 4, "category": "Operational"},
    "LLM Documentation": {"likelihood": 3, "impact": 4, "category": "Compliance"},
    "Model Opacity": {"likelihood": 4, "impact": 3, "category": "Legal"},
    "Downstream Data": {"likelihood": 3, "impact": 5, "category": "Strategic"},
    "Adversarial Evolution": {"likelihood": 4, "impact": 3, "category": "Technology"},
    "Appeal Process": {"likelihood": 3, "impact": 3, "category": "Reputational"},
}


def _render_risk_heatmap():
    """Render the risk likelihood x impact heatmap."""
    fig = go.Figure()

    category_colors = {
        "Technology": SPOTIFY_GREEN,
        "Financial": COLOR_DANGER,
        "Operational": COLOR_WARNING,
        "Compliance": COLOR_INFO,
        "Legal": "#AF2896",
        "Strategic": "#FF6437",
        "Reputational": "#FFC864",
    }

    for risk_name, risk_data in RISK_MATRIX.items():
        color = category_colors.get(risk_data["category"], SPOTIFY_LIGHT_GRAY)
        score = risk_data["likelihood"] * risk_data["impact"]
        size = max(25, score * 3)

        fig.add_trace(go.Scatter(
            x=[risk_data["likelihood"]],
            y=[risk_data["impact"]],
            mode="markers+text",
            marker=dict(size=size, color=color, opacity=0.85,
                        line=dict(color=SPOTIFY_WHITE, width=1.5)),
            text=[risk_name],
            textposition="top center",
            textfont=dict(size=11, color=SPOTIFY_WHITE),
            name=f"{risk_name} ({risk_data['category']})",
            hovertemplate=f"<b>{risk_name}</b><br>Category: {risk_data['category']}<br>Likelihood: {risk_data['likelihood']}/5<br>Impact: {risk_data['impact']}/5<br>Score: {score}/25<extra></extra>",
        ))

    # Background zones
    fig.add_shape(type="rect", x0=0.5, y0=3.5, x1=5.5, y1=5.5,
                  fillcolor="rgba(232,17,91,0.07)", line_width=0)
    fig.add_shape(type="rect", x0=3.5, y0=0.5, x1=5.5, y1=3.5,
                  fillcolor="rgba(232,17,91,0.07)", line_width=0)
    fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=3.5, y1=3.5,
                  fillcolor="rgba(29,185,84,0.05)", line_width=0)

    apply_spotify_style(fig, height=500)
    fig.update_layout(
        xaxis=dict(title="Likelihood", range=[0.5, 5.5], dtick=1, tickvals=[1, 2, 3, 4, 5],
                    ticktext=["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]),
        yaxis=dict(title="Impact", range=[0.5, 5.5], dtick=1, tickvals=[1, 2, 3, 4, 5],
                    ticktext=["Minimal", "Minor", "Moderate", "Major", "Severe"]),
        showlegend=False,
    )
    return fig


PREGENERATED_FINDINGS = {
    "Model Drift": """## Observation: ML Model Performance Degradation

**Risk Rating:** High

**Condition:**
Based on our scenario modeling of StreamShield's performance data, we observed a pattern consistent with model precision declining post-catalog-acquisition. The false positive rate appears elevated, and the Population Stability Index (PSI) reached **{psi}**, exceeding the commonly accepted threshold of 0.20 that indicates significant distribution shift. *(Precision figures based on illustrative scenario data — actual values would require access to production metrics.)*

**Criteria:**
The NIST AI Risk Management Framework (Measure function) calls for continuous monitoring of AI system performance, with re-evaluation triggered when material changes occur in the operating environment. ISACA guidance on AI model lifecycle governance emphasizes the need for documented retraining protocols when underlying data distributions shift. Leading practices in model risk management (e.g., OCC SR 11-7 principles, adapted) call for ongoing validation commensurate with the materiality of model outputs.

**Cause:**
The ML model has not been retrained since its last update approximately four months ago. The subsequent catalog acquisition introduced a material change to the distribution of content on the platform, yet no model performance evaluation or retraining was initiated. Management has indicated that retraining is planned for next quarter.

**Effect:**
The observed increase in the false positive rate suggests that a greater number of legitimate streams may be incorrectly classified. Based on our sample analysis, this could result in an estimated **{additional_fp:,}** additional legitimate streams being incorrectly flagged at production scale, with corresponding delays in royalty payments to rights holders (estimated at approximately **${daily_royalty_impact:,.0f}** per day, subject to validation with production data). The timing of this degradation is consistent with the recently reported label dispute, though a direct causal link would require further investigation.

**Recommendation:**
1. Management should evaluate the need for expedited model retraining using post-acquisition data, ahead of the currently planned next-quarter timeline
2. Implement automated distribution monitoring (e.g., PSI tracking) with defined alerting thresholds at warning (>0.10) and critical (>0.20) levels
3. Establish a policy requiring model performance evaluation within a defined period following significant platform changes (catalog acquisitions, market expansions, new content formats)
4. Consider establishing a cross-functional Model Risk Committee (Engineering, Finance, Legal, Content) with a regular review cadence
5. **Establish a formal catalog onboarding protocol:** When new catalog content is acquired, tag the content, apply adjusted classification thresholds during a defined grace period (e.g., raising the auto-quarantine threshold to 98% for new catalog content for 90 days), and default to "monitor with provisional royalty payment" rather than "quarantine" for review-zone cases involving new catalog content. This reflects the asymmetry in error costs — a false positive directly harms a legitimate artist, while a false negative results in a small, recoverable royalty leakage that can be addressed through retroactive clawback. This protocol should include velocity monitoring and entity-level fraud intelligence to catch repeat offenders who attempt to exploit the grace period""",

    "Automation Bias": """## Observation: Potential Automation Bias in Human Review Process

**Risk Rating:** High

**Condition:**
Our analysis of analyst review data ({total_reviews:,} cases reviewed) identified patterns consistent with potential automation bias:
- **{high_bias_count}** of **{total_analysts}** analysts agree with LLM recommendations more than **96%** of the time
- These high-agreement analysts exhibit an average review duration of **{high_bias_time:.0f} seconds** per case, compared to **{independent_time:.0f} seconds** for analysts with lower agreement rates
- This **{time_ratio:.1f}x** differential in review duration, combined with the elevated agreement rate, warrants further investigation into whether independent judgment is being consistently applied
- The overall **{agreement_rate}** agreement rate, which management has cited as evidence of model calibration, may also be consistent with over-reliance on automated recommendations

**Criteria:**
The design intent of the human review zone (scores between 70-95%) is to provide independent human judgment for cases where the ML model has insufficient confidence. Emerging regulatory frameworks, including the EU AI Act (Article 14), emphasize the importance of effective human oversight for AI systems involved in consequential decision-making. Academic research on automation bias (Springer Nature, 2025) identifies high agreement rates combined with short review durations as indicators that merit investigation.

**Cause:**
Based on our review, no formal automation bias monitoring program is in place. Challenge cases with known outcomes are not seeded into the review queue to objectively assess analyst independence. The review workflow and user interface design have not been evaluated for potential anchoring effects. Management currently interprets the high agreement rate as a positive indicator of model calibration rather than investigating it as a potential risk signal.

**Effect:**
If the observed patterns reflect automation bias rather than genuine agreement, the human review control may not be operating as designed for a portion of review-zone cases. This could diminish the overall effectiveness of the review process and limit the organization's ability to demonstrate meaningful human oversight for consequential classification decisions. The financial and reputational implications would depend on the extent to which biased reviews result in incorrect classifications.

**Recommendation:**
1. **Replace narrative-based review with a structured signal confirmation card.** Instead of presenting a completed LLM summary and recommendation, present the raw signal values (account age, device diversity, VPN status, play duration, skip rate, geographic concentration, IP clustering) as a lightweight card with binary fraud-indicator assessments per signal. The analyst evaluates each signal, records their classification, and only then sees the AI recommendation. This takes approximately 60-90 seconds per case — comparable to reading an LLM summary — but eliminates anchoring bias and produces structured, auditable data with zero free-text writing burden.
2. **Implement a challenge case program:** periodically seed the review queue (e.g., 5% of cases) with pre-labeled cases of known outcomes to objectively measure whether analysts can detect when the AI recommendation is incorrect.
3. **Establish per-analyst performance monitoring** as a standard management practice, tracking agreement rates, review duration, signal-level assessment patterns, and override rates. The signal confirmation card naturally produces this data without additional reporting burden.
4. **Conduct periodic quality reviews** on a random sample of completed signal cards to verify that analyst assessments are consistent with the displayed signal values""",

    "Executive Summary": """## StreamShield — IAR Preliminary Assessment

**Prepared for:** Head of Fraud Department | Leadership Review
**Prepared by:** Internal Audit & Risk

---

### Overview
StreamShield has demonstrated meaningful impact since deployment, reducing estimated fraudulent royalty payouts by approximately 40% and automatically handling 95% of all streams. Our preliminary analysis has identified **{n_critical + n_high} high-priority** areas where the control environment can be strengthened.

### Key Observations

**1. Model Performance — Drift Monitoring (High)**
Scenario modeling indicates precision may be declining following the catalog acquisition, consistent with the 4-month gap since last retraining. An automated PSI monitoring system with alerting thresholds would detect drift in hours rather than months. *(Precision figures are illustrative — actual values require production metrics.)*

**2. Threshold Governance (High)**
The classification thresholds (70%/95%) were established by the engineering team during initial deployment and have not been formally reviewed or approved by business stakeholders. Given that these thresholds directly influence royalty calculations and chart positions, they should be considered for inclusion in the company's internal control framework.

**3. Human Review Process Effectiveness (High)**
{high_bias_count} of {total_analysts} analysts exhibit agreement rates above 96% with AI recommendations, with average review durations under {high_bias_time:.0f} seconds. These patterns warrant further investigation to determine whether the human review control is operating as designed.

**4. LLM Output Governance (High)**
Investigation reports generated by the LLM assistant serve as official case documentation. Our review did not identify quality assurance procedures, hallucination detection controls, or formal human attestation requirements for these records.

### Areas for Further Analysis
- Estimated daily royalty impact from excess false positives: approximately **${daily_royalty_impact:,.0f}** (subject to validation with production data)
- Appeal resolution timelines vary by artist type: indie artists average **{indie_days:.0f} days** compared to **{major_days:.0f} days** for major labels
- Overall appeal overturn rate of **{overturn_rate:.0%}** warrants analysis of root causes for reversed decisions

### Recommended Next Steps
1. Evaluate the need for expedited model retraining using post-acquisition data
2. Establish a formal catalog onboarding protocol — adjusted thresholds, grace periods, and provisional royalty payments for newly acquired content, with retroactive clawback capability and entity-level fraud monitoring as compensating controls
3. Establish a formal threshold governance framework with cross-functional stakeholder input
4. Replace narrative-based analyst review with a structured signal confirmation card to address automation bias while maintaining review throughput at 200 cases/day
5. Implement a challenge case program to objectively test analyst independence
6. Develop LLM output governance controls (attestation, spot-check validation)
7. Review appeal process timelines and consider SLA establishment
8. Assess downstream data consumption and consider formalizing data contracts with Finance, Ads, and Creator Analytics

### Proposed IAR Engagement
We recommend a combined advisory and assurance engagement (approximately 8 weeks) to formally evaluate StreamShield controls, with immediate advisory support available ahead of the leadership review. A detailed scope and approach will be provided upon engagement approval.""",
}


def _format_finding(template_key, data_summary):
    """Fill in a pre-generated finding with actual data values."""
    s = data_summary
    post_precision = f"{s['model_performance']['post_acquisition_precision']:.1%}"
    precision_drop = f"{s['model_performance']['precision_drop_pct']:.1f}"
    pre_fpr = f"{s['model_performance']['pre_fpr']:.2%}"
    current_fpr = f"{s['model_performance']['current_fpr']:.2%}"
    psi = f"{s['model_performance']['current_psi']:.3f}"
    daily_streams = 18_000_000
    additional_fp = int(daily_streams * (s["model_performance"]["current_fpr"] - s["model_performance"]["pre_fpr"]))
    daily_royalty_impact = additional_fp * 0.004

    template = PREGENERATED_FINDINGS[template_key]
    return template.format(
        post_precision=post_precision,
        precision_drop=precision_drop,
        pre_fpr=pre_fpr,
        current_fpr=current_fpr,
        psi=psi,
        additional_fp=additional_fp,
        daily_royalty_impact=daily_royalty_impact,
        total_reviews=s["analyst_behavior"].get("overall_agreement_rate", 0),
        high_bias_count=s["analyst_behavior"]["analysts_above_96pct"],
        total_analysts=s["analyst_behavior"]["total_analysts"],
        high_bias_time=s["analyst_behavior"]["high_bias_avg_time_sec"],
        independent_time=s["analyst_behavior"]["independent_avg_time_sec"],
        time_ratio=s["analyst_behavior"]["independent_avg_time_sec"] / max(s["analyst_behavior"]["high_bias_avg_time_sec"], 1),
        agreement_rate=f"{s['analyst_behavior']['overall_agreement_rate']:.1%}",
        rubber_stamp_pct=s["analyst_behavior"]["analysts_above_96pct"] / max(s["analyst_behavior"]["total_analysts"], 1) * 100,
        n_critical=2,
        n_high=2,
        indie_days=next((x["avg_days"] for x in s["appeals"]["by_artist_type"] if x["artist_type"] == "indie"), 38),
        major_days=next((x["avg_days"] for x in s["appeals"]["by_artist_type"] if x["artist_type"] == "major"), 12),
        overturn_rate=s["appeals"]["overall_overturn_rate"],
    )


def render(events_df, reviews_df, perf_df, appeals_df):
    st.markdown("## AI Audit Agent")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "AI-powered audit finding generation. Select a risk area to analyze, and the agent produces "
        "a structured finding with data-backed evidence. Every claim is traceable to the underlying data."
        "</p>",
        unsafe_allow_html=True,
    )

    # Risk heatmap
    st.markdown("### Risk Landscape — Likelihood x Impact Matrix")
    fig_risk = _render_risk_heatmap()
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("---")

    # Finding generation
    st.markdown("### Generate Audit Finding")

    data_summary = _get_data_summary(events_df, reviews_df, perf_df, appeals_df)

    finding_type = st.selectbox(
        "Select audit area to analyze",
        options=["Model Drift", "Automation Bias", "Executive Summary"],
        index=0,
        help="The AI agent will analyze the data for the selected area and generate a structured audit finding.",
    )

    col_btn, col_mode = st.columns([1, 2])

    with col_mode:
        use_ai = st.toggle(
            "Use LLM API (live generation)",
            value=False,
            help="When enabled, calls the LLM API for live analysis. When disabled, uses pre-generated findings populated with real data values.",
        )

    with col_btn:
        generate = st.button("Generate Finding", type="primary", use_container_width=True)

    if generate:
        if use_ai:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                st.warning("Set the `LLM_API_KEY` environment variable to use live AI generation. Falling back to pre-generated findings.")
                use_ai = False

        if use_ai:
            try:
                import anthropic
                client = anthropic.Anthropic()

                system_prompt = """You are an Internal Audit & Risk analyst at Spotify preparing observations for a preliminary assessment of StreamShield, an AI-powered fraud detection system.

Your observations must follow the IIA's standard finding structure:
- **Risk Rating:** (Critical / High / Medium / Low)
- **Condition:** What was observed, stated objectively with specific data points from the summary provided. Use precise, measured language. Do not overstate or editorialize.
- **Criteria:** The applicable standard, framework, or leading practice that establishes what should be in place. Reference specific frameworks (NIST AI RMF, EU AI Act, ISACA AI Governance, SOX ITGC) where applicable. Do not cite policies that do not exist as criteria.
- **Cause:** The root cause of the gap, stated factually. Use language like "based on our review" or "no evidence was identified of" rather than definitive assertions.
- **Effect:** The potential business impact. Where quantifying, clearly note whether figures are based on sample analysis or production data. Use "may result in" or "could lead to" rather than definitive statements unless directly evidenced.
- **Recommendation:** Specific, actionable steps framed as suggestions to management (e.g., "Management should consider..." or "We recommend..."). Avoid prescribing implementation details beyond what is necessary.

Tone guidelines:
- Objective, measured, professional. An auditor observes and recommends — they do not declare emergencies or make editorial judgments.
- Distinguish between what was observed (facts) and what may be inferred (analysis requiring validation).
- Avoid informal language (e.g., "rubber-stamping", "ticking time bomb").
- Ground every quantitative claim in the data summary provided. Never fabricate numbers."""

                user_prompt = f"""Analyze the following StreamShield audit data and generate a detailed audit finding for: **{finding_type}**

Data Summary:
{json.dumps(data_summary, indent=2, default=str)}

Generate a comprehensive, professional audit finding with specific data references."""

                with st.spinner("AI Agent analyzing data..."):
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                    )
                    finding_text = message.content[0].text

                st.markdown(
                    f"""
                    <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:4px 12px; margin-bottom:16px; display:inline-block;">
                        <span style="color:{SPOTIFY_GREEN}; font-size:12px; font-weight:700;">GENERATED LIVE VIA LLM API</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(finding_text)

            except Exception as e:
                st.error(f"API call failed: {e}. Falling back to pre-generated finding.")
                use_ai = False

        if not use_ai:
            finding_text = _format_finding(finding_type, data_summary)
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:4px 12px; margin-bottom:16px; display:inline-block;">
                    <span style="color:{COLOR_INFO}; font-size:12px; font-weight:700;">PRE-GENERATED FINDING (POPULATED WITH REAL DATA)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""<div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:24px; border:1px solid {SPOTIFY_GRAY}33; line-height:1.7;">
                {finding_text}
                </div>""",
                unsafe_allow_html=True,
            )

    # Data transparency section
    st.markdown("---")
    st.markdown("### Data Transparency")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
        "Every finding is grounded in the data below. This ensures traceability and auditability of the AI agent's outputs."
        "</p>",
        unsafe_allow_html=True,
    )

    with st.expander("View Raw Data Summary", expanded=False):
        st.json(data_summary)

    with st.expander("View Risk Register", expanded=False):
        risk_data = []
        for name, data in RISK_MATRIX.items():
            score = data["likelihood"] * data["impact"]
            rating = "High" if score >= 15 else "Medium" if score >= 9 else "Low"
            risk_data.append({
                "Risk": name,
                "Category": data["category"],
                "Likelihood": data["likelihood"],
                "Impact": data["impact"],
                "Score": score,
                "Rating": rating,
            })
        risk_df = pd.DataFrame(risk_data).sort_values("Score", ascending=False)
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
