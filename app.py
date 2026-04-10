"""StreamShield Audit Assistant — Spotify IAR Team"""

import streamlit as st

st.set_page_config(
    page_title="StreamShield Audit Assistant",
    page_icon="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.style import GLOBAL_CSS, SPOTIFY_GREEN, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG, SPOTIFY_GRAY, COLOR_DANGER, COLOR_WARNING, COLOR_INFO, metric_card
from utils.data_loader import (
    load_streaming_events, load_analyst_reviews, load_model_performance,
    load_appeal_cases, get_data_source_badge, warmup_honkify_table,
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Lazy data loading — only load what the current page needs, cache in
# session_state so subsequent reruns (button clicks, tab switches) are instant
# instead of deserializing pickled DataFrames from st.cache_data every time.
# --------------------------------------------------------------------------

def _lazy(name, loader_fn):
    """Load a dataset once per session. Returns (df, source)."""
    dk, sk = f"_d_{name}", f"_s_{name}"
    if dk not in st.session_state:
        df, src = loader_fn()
        st.session_state[dk] = df
        st.session_state[sk] = src
    return st.session_state[dk], st.session_state[sk]


def _events():    return _lazy("events",  load_streaming_events)
def _reviews():   return _lazy("reviews", load_analyst_reviews)
def _perf():      return _lazy("perf",    load_model_performance)
def _appeals():   return _lazy("appeals", load_appeal_cases)


# One-time BigQuery warmup (fires list_rows once to pre-warm auth + connection).
if "_bq_warm" not in st.session_state:
    warmup_honkify_table()
    st.session_state["_bq_warm"] = True


# --- Sidebar ---
st.sidebar.markdown(
    f"""
    <div style="text-align:center; padding:24px 0 28px 0;">
        <div style="margin-bottom:12px;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="{SPOTIFY_GREEN}">
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
            </svg>
        </div>
        <div style="font-size:24px; font-weight:800; color:{SPOTIFY_WHITE}; letter-spacing:-0.5px;">StreamShield</div>
        <div style="font-size:11px; color:{SPOTIFY_GREEN}; margin-top:4px; letter-spacing:2px; text-transform:uppercase; font-weight:600;">Audit Assistant</div>
        <div style="margin-top:12px; padding-top:12px; border-top:1px solid rgba(83,83,83,0.2);">
            <div style="font-size:10px; color:{SPOTIFY_GRAY}; letter-spacing:1.5px; text-transform:uppercase;">Internal Audit & Risk</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")

# Section headers + selectbox navigation (single widget, no state conflicts)
# Clean sidebar: THE STORY is the primary flow, REFERENCE is supplementary.
# All analysis is baked into the Before/After tabs of the story pages.
_STORY_PAGES = ["Honkify", "Fraud Operations", "Internal Audit"]
_REFERENCE_PAGES = ["Dashboard", "Audit Agent", "Audit Journey", "Architecture"]

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Honkify"

st.sidebar.markdown(
    f'<div style="color:{SPOTIFY_GRAY}; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin:8px 4px 6px 4px; font-weight:700;">THE STORY</div>',
    unsafe_allow_html=True,
)
for sp in _STORY_PAGES:
    idx = _STORY_PAGES.index(sp) + 1
    is_active = st.session_state.get("nav_page") == sp
    if st.sidebar.button(
        f"{'●' if is_active else '○'} Step {idx} · {sp}",
        key=f"nav_{sp}",
        use_container_width=True,
    ):
        st.session_state["nav_page"] = sp
        st.rerun()

st.sidebar.markdown(
    f'<div style="color:{SPOTIFY_GRAY}; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin:14px 4px 6px 4px; font-weight:700;">REFERENCE</div>',
    unsafe_allow_html=True,
)
for sp in _REFERENCE_PAGES:
    is_active = st.session_state.get("nav_page") == sp
    if st.sidebar.button(
        f"{'●' if is_active else '○'} {sp}",
        key=f"nav_{sp}",
        use_container_width=True,
    ):
        st.session_state["nav_page"] = sp
        st.rerun()

page = st.session_state["nav_page"]

st.sidebar.markdown("---")

# Data source badges — show cached sources if available, otherwise a neutral indicator
_badge_keys = {"Events": "_s_events", "Reviews": "_s_reviews", "Performance": "_s_perf", "Appeals": "_s_appeals"}
src_html = "".join([
    f'<div style="margin-bottom:4px;">{get_data_source_badge(st.session_state.get(sk, "csv"))} '
    f'<span style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; margin-left:4px;">{k}</span></div>'
    for k, sk in _badge_keys.items()
])
st.sidebar.markdown(
    f'<div style="padding:0 4px;"><div style="color:{SPOTIFY_GRAY}; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;">Data Sources</div>{src_html}</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div style="color:{SPOTIFY_GRAY}; font-size:10px; padding:0 4px; text-align:center;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="{SPOTIFY_GRAY}">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
        </svg>
        <br>Spotify IAR &middot; 2026
    </div>
    """,
    unsafe_allow_html=True,
)


# --- Page Routing (lazy data loading per page) ---
if page == "Honkify":
    from modules.honkify import render
    render()

elif page == "Fraud Operations":
    reviews_df, _ = _reviews()
    perf_df, _ = _perf()
    appeals_df, _ = _appeals()
    from modules.fraud_ops import render
    render(reviews_df, perf_df, appeals_df)

elif page == "Internal Audit":
    reviews_df, _ = _reviews()
    perf_df, _ = _perf()
    appeals_df, _ = _appeals()
    from modules.internal_audit import render
    render(reviews_df, perf_df, appeals_df)

elif page == "Dashboard":
    events_df, events_src = _events()
    reviews_df, _ = _reviews()
    perf_df, _ = _perf()
    appeals_df, _ = _appeals()
    from modules.dashboard import render
    render(events_df, reviews_df, perf_df, appeals_df, events_src)

elif page == "Audit Journey":
    from modules.audit_journey import render
    render()

elif page == "Architecture":
    from modules.architecture import render
    render()

elif page == "Drift Monitor":
    perf_df, _ = _perf()
    events_df, _ = _events()
    from modules.drift_monitor import render
    render(perf_df, events_df)

elif page == "Threshold Lab":
    events_df, _ = _events()
    from modules.threshold_analyzer import render
    render(events_df)

elif page == "Review Integrity":
    reviews_df, _ = _reviews()
    tab_analysis, tab_demo = st.tabs(["Bias Analysis", "Interactive Signal Card"])
    with tab_analysis:
        from modules.bias_detector import render as render_bias
        render_bias(reviews_df)
    with tab_demo:
        from modules.signal_card_demo import render as render_card
        render_card()

elif page == "Data Observatory":
    events_df, _ = _events()
    reviews_df, _ = _reviews()
    appeals_df, _ = _appeals()
    from modules.data_observatory import render
    render(events_df, reviews_df, appeals_df)

elif page == "Audit Agent":
    events_df, _ = _events()
    reviews_df, _ = _reviews()
    perf_df, _ = _perf()
    appeals_df, _ = _appeals()
    from modules.ai_audit_agent import render
    render(events_df, reviews_df, perf_df, appeals_df)

elif page == "Presentation":
    from modules.presentation import render
    render()
