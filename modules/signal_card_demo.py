"""Interactive Signal Card Demo — A working prototype of the proposed analyst workflow.

The Signal Card widget itself is exposed as `render_signal_card_widget(case, key_prefix, on_submit=None)`
so other pages (e.g., fraud_ops) can render the same interactive widget against their own case data.
"""

import streamlit as st
import pandas as pd
import random
from utils.style import (
    SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING, COLOR_INFO,
    SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG, SPOTIFY_GRAY,
)


def _generate_case():
    """Generate a realistic, ambiguous review-zone case with mixed signals."""
    rng = random.Random()

    archetype = rng.choice([
        "bot_farm",
        "new_catalog_artist",
        "compromised_account",
        "viral_campaign",
        "low_and_slow",
        "regional_artist",
    ])

    if archetype == "bot_farm":
        account_age = rng.randint(3, 18)
        devices = 1
        duration = rng.randint(30, 33)
        tracks_day = rng.randint(450, 650)
        skip_rate = rng.randint(0, 2)
        vpn = "Yes"
        locations = rng.randint(6, 11)
        same_ip = rng.randint(35, 90)
        ai_rec = "Quarantine"
        score = round(rng.uniform(0.88, 0.94), 2)
        fraud_signals = [True, True, True, True, True, True, True, True]

    elif archetype == "new_catalog_artist":
        account_age = rng.randint(8, 25)
        devices = rng.randint(1, 2)
        duration = rng.randint(180, 260)
        tracks_day = rng.randint(80, 180)
        skip_rate = rng.randint(8, 18)
        vpn = "No"
        locations = "2 (CO, EC)"
        same_ip = rng.randint(12, 30)
        ai_rec = "Quarantine"
        score = round(rng.uniform(0.76, 0.88), 2)
        fraud_signals = [True, True, False, True, False, False, True, True]

    elif archetype == "compromised_account":
        account_age = rng.randint(400, 1200)
        devices = rng.randint(3, 5)
        duration = rng.randint(30, 34)
        tracks_day = rng.randint(300, 500)
        skip_rate = rng.randint(1, 3)
        vpn = rng.choice(["Yes", "No"])
        locations = rng.randint(1, 3)
        same_ip = rng.randint(1, 8)
        ai_rec = "Monitor"
        score = round(rng.uniform(0.72, 0.84), 2)
        fraud_signals = [False, False, True, True, True, vpn == "Yes", False, False]

    elif archetype == "viral_campaign":
        account_age = rng.randint(60, 400)
        devices = rng.randint(2, 4)
        duration = rng.randint(140, 200)
        tracks_day = rng.randint(150, 350)
        skip_rate = rng.randint(20, 35)
        vpn = "No"
        locations = rng.randint(3, 8)
        same_ip = rng.randint(2, 10)
        ai_rec = "Monitor"
        score = round(rng.uniform(0.71, 0.82), 2)
        fraud_signals = [False, False, False, True, False, False, True, False]

    elif archetype == "low_and_slow":
        account_age = rng.randint(90, 300)
        devices = rng.randint(2, 3)
        duration = rng.randint(100, 180)
        tracks_day = rng.randint(40, 80)
        skip_rate = rng.randint(10, 22)
        vpn = "Yes"
        locations = rng.randint(1, 2)
        same_ip = rng.randint(15, 40)
        ai_rec = "Clear"
        score = round(rng.uniform(0.70, 0.78), 2)
        fraud_signals = [False, False, False, False, False, True, False, True]

    else:  # regional_artist
        account_age = rng.randint(15, 45)
        devices = rng.randint(1, 2)
        duration = rng.randint(200, 320)
        tracks_day = rng.randint(60, 120)
        skip_rate = rng.randint(5, 12)
        vpn = "No"
        locations = "1 (NG)"
        same_ip = rng.randint(20, 50)
        ai_rec = "Quarantine"
        score = round(rng.uniform(0.80, 0.92), 2)
        fraud_signals = [True, True, False, False, True, False, True, True]

    if isinstance(locations, int):
        locations = f"{locations} countries"

    signals = {
        "Account age": {"value": f"{account_age} days", "fraud_ground_truth": fraud_signals[0]},
        "Devices used": {"value": str(devices), "fraud_ground_truth": fraud_signals[1]},
        "Avg play duration": {"value": f"{duration} sec", "fraud_ground_truth": fraud_signals[2]},
        "Unique tracks/day": {"value": str(tracks_day), "fraud_ground_truth": fraud_signals[3]},
        "Skip rate": {"value": f"{skip_rate}%", "fraud_ground_truth": fraud_signals[4]},
        "VPN detected": {"value": vpn, "fraud_ground_truth": fraud_signals[5]},
        "Locations (24hr)": {"value": locations, "fraud_ground_truth": fraud_signals[6]},
        "Same-IP accounts": {"value": str(same_ip), "fraud_ground_truth": fraud_signals[7]},
    }

    case_id = f"CASE-{rng.randint(10000, 99999)}"
    return {
        "case_id": case_id,
        "fraud_score": score,
        "signals": signals,
        "ai_recommendation": ai_rec,
        "submitted": False,
        "analyst_signals": {},
        "analyst_decision": None,
    }


def render_signal_card_widget(case: dict, key_prefix: str, on_submit=None):
    """Render the interactive Signal Confirmation Card for a given case dict.

    `case` must have keys: case_id, fraud_score, signals (dict of name -> {value, fraud_ground_truth}),
        ai_recommendation, submitted, analyst_signals, analyst_decision.
    Mutates `case` in place when analyst submits. Calls `on_submit(case)` after submission.
    All st.* widget keys are namespaced with `key_prefix` to allow multiple cards on the same page.
    """
    # Case header
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <span style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700;">{case['case_id']}</span>
            <span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">Fraud Score: <strong style="color:{COLOR_WARNING};">{case['fraud_score']:.0%}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not case["submitted"]:
        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:12px;">Step 1: Assess Each Signal</div>',
            unsafe_allow_html=True,
        )

        signal_assessments = {}
        for i, (signal_name, signal_data) in enumerate(case["signals"].items()):
            col_name, col_value, col_assess = st.columns([3, 2, 2])
            with col_name:
                st.markdown(f"**{signal_name}**")
            with col_value:
                st.markdown(f"`{signal_data['value']}`")
            with col_assess:
                signal_assessments[signal_name] = st.radio(
                    f"Fraud? ({signal_name})",
                    options=["Yes", "No"],
                    index=1,
                    horizontal=True,
                    key=f"{key_prefix}_signal_{i}",
                    label_visibility="collapsed",
                )

        fraud_count = sum(1 for v in signal_assessments.values() if v == "Yes")

        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:12px 16px; border:1px solid rgba(83,83,83,0.2); margin:16px 0;">
                <span style="color:{SPOTIFY_LIGHT_GRAY};">Fraud signals flagged: </span>
                <strong style="color:{COLOR_DANGER if fraud_count >= 5 else COLOR_WARNING if fraud_count >= 3 else SPOTIFY_GREEN};">{fraud_count}/8</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:12px;">Step 2: Your Classification</div>',
            unsafe_allow_html=True,
        )

        decision = st.radio(
            "Your decision",
            options=["Quarantine", "Monitor", "Clear"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"{key_prefix}_decision",
        )

        # Step 3: Decision reasoning — captures WHY, not just WHAT
        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin:16px 0 8px;">Step 3: Reasoning</div>'
            f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:8px;">What was the primary basis for your decision? This becomes part of the structured audit trail, feeds into model retraining with quality labels, and serves as a training reference for new analysts.</div>',
            unsafe_allow_html=True,
        )

        REASON_OPTIONS = [
            "Select primary reason...",
            "VPN + suspicious geography pattern",
            "Account age too low for observed activity",
            "Play duration consistent with bot behavior (~31s)",
            "Skip rate inconsistent with human listening",
            "Multiple signals align with known fraud pattern",
            "Signals inconsistent — likely false positive / legitimate artist",
            "New catalog content — grace period applies",
            "Mixed signals — needs network-level investigation",
            "Matches known compromised account pattern",
        ]
        reason = st.selectbox(
            "Primary basis for decision",
            options=REASON_OPTIONS,
            key=f"{key_prefix}_reason",
            label_visibility="collapsed",
        )

        reason_valid = reason != REASON_OPTIONS[0]

        if st.button(
            "Submit Decision" if reason_valid else "Select a reason to submit",
            type="primary" if reason_valid else "secondary",
            use_container_width=True,
            key=f"{key_prefix}_submit",
            disabled=not reason_valid,
        ):
            case["analyst_signals"] = signal_assessments
            case["analyst_decision"] = decision
            case["analyst_reason"] = reason
            case["submitted"] = True
            case["fraud_count"] = fraud_count
            if on_submit is not None:
                on_submit(case)
            st.rerun()

        st.markdown(
            f'<div style="color:{SPOTIFY_GRAY}; font-size:12px; font-style:italic; margin-top:12px; text-align:center;">The LLM summary and recommendation will appear as a second opinion after you submit your initial assessment</div>',
            unsafe_allow_html=True,
        )

    else:
        agreed = case["analyst_decision"] == case["ai_recommendation"]

        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:16px;">Results</div>',
            unsafe_allow_html=True,
        )

        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); text-align:center;">
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Your Decision</div>
                    <div style="color:{SPOTIFY_WHITE}; font-size:24px; font-weight:700;">{case['analyst_decision']}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:12px; margin-top:4px;">{case.get('fraud_count', 0)}/8 signals flagged</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with res_col2:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); text-align:center;">
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">LLM Second Opinion</div>
                    <div style="color:{COLOR_INFO}; font-size:24px; font-weight:700;">{case['ai_recommendation']}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:12px; margin-top:4px;">Score: {case['fraud_score']:.0%}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with res_col3:
            match_color = SPOTIFY_GREEN if agreed else COLOR_WARNING
            match_text = "AGREED" if agreed else "OVERRIDDEN"
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); text-align:center;">
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Outcome</div>
                    <div style="color:{match_color}; font-size:24px; font-weight:700;">{match_text}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:12px; margin-top:4px;">Logged to audit trail</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin:20px 0 12px;">Structured Audit Trail</div>',
            unsafe_allow_html=True,
        )

        trail_data = []
        for signal_name, assessment in case["analyst_signals"].items():
            ground_truth = case["signals"][signal_name]["fraud_ground_truth"]
            trail_data.append({
                "Signal": signal_name,
                "Value": case["signals"][signal_name]["value"],
                "Analyst Assessment": assessment,
                "Consistent with Data": "Yes" if (assessment == "Yes") == ground_truth else "Review needed",
            })

        trail_df = pd.DataFrame(trail_data)
        st.dataframe(trail_df, use_container_width=True, hide_index=True)

        # Show reasoning
        analyst_reason = case.get("analyst_reason", "—")
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {COLOR_INFO}; margin-top:12px;">
                <div style="color:{COLOR_INFO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">Decision reasoning</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:600;">{analyst_reason}</div>
                <div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:6px;">Captured as part of structured audit trail. Used for: (1) model retraining with quality labels, (2) analyst training and knowledge management, (3) regulatory audit evidence.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(29,185,84,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:16px 20px; border-left:4px solid {SPOTIFY_GREEN}; margin-top:14px;">
                <div style="color:{SPOTIFY_GREEN}; font-weight:700; font-size:13px; margin-bottom:6px;">The Positive Feedback Loop — Human + AI Together</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                    <strong style="color:{SPOTIFY_WHITE};">For the model:</strong> Structured, independent assessments with stated reasoning become quality training labels. The analyst's view is captured first, then the LLM's — both feed into the next training cycle with clear provenance.<br><br>
                    <strong style="color:{SPOTIFY_WHITE};">For the LLM:</strong> The investigation assistant gets better over time because it trains on genuinely independent analyst decisions, not echoes of its own recommendations. The LLM remains a core part of the workflow — as a second opinion that the analyst can compare against their own assessment.<br><br>
                    <strong style="color:{SPOTIFY_WHITE};">For the team:</strong> The reasoning field builds institutional knowledge. New analysts can query: "How did experienced analysts handle VPN + new account + low skip rate?" The Signal Card becomes both an audit control and a training tool.<br><br>
                    <strong style="color:{SPOTIFY_WHITE};">For the auditor:</strong> Every decision is queryable, structured, and auditable at scale. The LLM summary is preserved alongside the analyst's independent assessment — two perspectives, one record.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render():
    """Standalone Signal Card Demo page (used by Review Integrity tab)."""
    st.markdown("## Interactive Signal Card Demo")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Experience the proposed analyst workflow. Evaluate each signal independently, "
        "make your classification decision, then see how the AI would have classified it. "
        "This resequences the workflow so analysts assess signals first, then receive the LLM summary as a second opinion."
        "</p>",
        unsafe_allow_html=True,
    )

    col_old, col_new = st.columns(2)
    with col_old:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {COLOR_DANGER};">
                <div style="color:{COLOR_DANGER}; font-size:13px; font-weight:700; margin-bottom:8px;">Current Workflow (Problem)</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                    1. LLM generates full analysis + recommendation<br>
                    2. Analyst reads the finished product<br>
                    3. Analyst clicks Approve/Reject<br>
                    4. LLM report becomes official documentation<br><br>
                    <span style="color:{COLOR_DANGER};">Result: 97% agreement in under 90 seconds</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_new:
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(83,83,83,0.2); border-top:3px solid {SPOTIFY_GREEN};">
                <div style="color:{SPOTIFY_GREEN}; font-size:13px; font-weight:700; margin-bottom:8px;">Proposed Workflow (Signal Card)</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                    1. Analyst sees raw signal values first<br>
                    2. Analyst assesses each signal: Y/N<br>
                    3. Analyst makes classification + states reasoning<br>
                    4. LLM summary appears as second opinion<br><br>
                    <span style="color:{SPOTIFY_GREEN};">Result: Human + AI, verifiable independence</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if st.button("Generate New Case", type="primary"):
        st.session_state["demo_case"] = _generate_case()

    if "demo_case" not in st.session_state:
        st.session_state["demo_case"] = _generate_case()

    case = st.session_state["demo_case"]
    render_signal_card_widget(case, key_prefix="signal_demo")

    if case.get("submitted"):
        if st.button("Review Next Case", type="primary", key="signal_demo_next"):
            st.session_state["demo_case"] = _generate_case()
            st.rerun()
