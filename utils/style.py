"""Spotify-themed styling constants and helpers for the StreamShield Audit Assistant."""

# Spotify Brand Colors
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_LIGHT = "#1ED760"
SPOTIFY_GREEN_DARK = "#17A34A"
SPOTIFY_BLACK = "#191414"
SPOTIFY_DARK_BG = "#121212"
SPOTIFY_CARD_BG = "#181818"
SPOTIFY_CARD_HOVER = "#282828"
SPOTIFY_GRAY = "#535353"
SPOTIFY_LIGHT_GRAY = "#B3B3B3"
SPOTIFY_WHITE = "#FFFFFF"

# Extended palette for charts
CHART_COLORS = [
    "#1DB954",  # green
    "#E8115B",  # red/pink (error/danger)
    "#509BF5",  # blue
    "#F59B23",  # orange/amber
    "#AF2896",  # purple
    "#1E90FF",  # dodger blue
    "#E91429",  # deep red
    "#148A08",  # dark green
    "#FF6437",  # coral
    "#FFC864",  # gold
]

# Semantic colors
COLOR_SUCCESS = SPOTIFY_GREEN
COLOR_DANGER = "#E8115B"
COLOR_WARNING = "#F59B23"
COLOR_INFO = "#509BF5"
COLOR_NEUTRAL = SPOTIFY_LIGHT_GRAY

# Risk level colors
RISK_CRITICAL = "#E8115B"
RISK_HIGH = "#FF6437"
RISK_MEDIUM = "#F59B23"
RISK_LOW = "#509BF5"

# Plotly layout template
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Circular, Helvetica Neue, Helvetica, Arial, sans-serif", color=SPOTIFY_WHITE, size=13),
    title_font=dict(size=18, color=SPOTIFY_WHITE),
    xaxis=dict(
        gridcolor="rgba(83,83,83,0.3)",
        zerolinecolor="rgba(83,83,83,0.3)",
        tickfont=dict(color=SPOTIFY_LIGHT_GRAY),
        title_font=dict(color=SPOTIFY_LIGHT_GRAY),
    ),
    yaxis=dict(
        gridcolor="rgba(83,83,83,0.3)",
        zerolinecolor="rgba(83,83,83,0.3)",
        tickfont=dict(color=SPOTIFY_LIGHT_GRAY),
        title_font=dict(color=SPOTIFY_LIGHT_GRAY),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=SPOTIFY_LIGHT_GRAY),
    ),
    margin=dict(l=50, r=30, t=50, b=50),
    hoverlabel=dict(
        bgcolor=SPOTIFY_CARD_HOVER,
        font_size=13,
        font_family="Circular, Helvetica Neue, Helvetica, Arial, sans-serif",
        font_color=SPOTIFY_WHITE,
    ),
)


def apply_spotify_style(fig, height=450):
    """Apply Spotify dark theme to a Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig


def metric_card(label, value, delta=None, delta_color="normal"):
    """Generate HTML for a Spotify-styled metric card."""
    delta_html = ""
    if delta is not None:
        color = COLOR_SUCCESS if delta_color == "good" else COLOR_DANGER if delta_color == "bad" else SPOTIFY_LIGHT_GRAY
        arrow = "&#9650;" if delta > 0 else "&#9660;" if delta < 0 else "&#8212;"
        delta_html = f'<div style="color:{color}; font-size:14px; margin-top:4px;">{arrow} {abs(delta):.1f}%</div>'

    return f"""
    <div style="
        background: {SPOTIFY_CARD_BG};
        border-radius: 8px;
        padding: 20px 24px;
        border: 1px solid {SPOTIFY_GRAY}33;
    ">
        <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:8px;">{label}</div>
        <div style="color:{SPOTIFY_WHITE}; font-size:32px; font-weight:700; line-height:1.1;">{value}</div>
        {delta_html}
    </div>
    """


def story_nav(step, total, title, what_to_do, next_page=None, next_hint=None):
    """Render a story navigator bar at the top of a demo page.

    Returns (bar_html, should_navigate). Call at the top of render().
    The caller must handle navigation if should_navigate is True.
    """
    import streamlit as _st

    dots = ""
    for i in range(1, total + 1):
        if i == step:
            dots += f'<span style="color:{SPOTIFY_GREEN}; font-weight:800;">●</span> '
        elif i < step:
            dots += f'<span style="color:{SPOTIFY_GREEN}40;">●</span> '
        else:
            dots += f'<span style="color:{SPOTIFY_GRAY};">○</span> '

    _st.markdown(
        f"""
        <div style="background:linear-gradient(90deg, rgba(29,185,84,0.08), rgba(29,185,84,0.02)); border:1px solid rgba(29,185,84,0.15); border-left:4px solid {SPOTIFY_GREEN}; border-radius:8px; padding:14px 20px; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:{SPOTIFY_GREEN}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px;">Step {step} of {total} {dots}</div>
                    <div style="color:{SPOTIFY_WHITE}; font-size:17px; font-weight:800; margin-top:4px;">{title}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-top:4px; line-height:1.5;">{what_to_do}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def story_next(next_page, next_hint):
    """Render a 'Next →' button at the bottom of a demo page. Returns True if clicked."""
    import streamlit as _st

    _st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    _st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(29,185,84,0.2); border-left:4px solid {SPOTIFY_GREEN};">
            <div style="color:{SPOTIFY_GREEN}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px;">Next step</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:700; margin-top:4px;">{next_page}</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-top:3px;">{next_hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if _st.button(f"→ Continue to {next_page}", use_container_width=True, key=f"story_next_{next_page}"):
        _st.session_state["nav_page"] = next_page
        _st.rerun()


GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global overrides */
    .stApp {
        font-family: 'Inter', 'Circular', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #28282833;
    }
    section[data-testid="stSidebar"] .stRadio > label {
        color: #B3B3B3 !important;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
        padding: 8px 12px !important;
        border-radius: 6px;
        transition: all 0.2s ease;
        margin-bottom: 2px;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
        background-color: #282828;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #282828;
    }

    /* Headers */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    h1 {
        font-size: 2rem !important;
    }

    /* Metric containers */
    [data-testid="stMetric"] {
        background-color: #181818;
        border: 1px solid #28282866;
        border-radius: 8px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] {
        color: #B3B3B3 !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: transparent;
        border-bottom: 1px solid #282828;
    }
    .stTabs [data-baseweb="tab"] {
        color: #B3B3B3;
        font-weight: 600;
        padding: 12px 20px;
        border-radius: 0;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 2px solid #1DB954 !important;
        background-color: transparent !important;
    }

    /* Selectbox and slider */
    .stSelectbox > div > div {
        background-color: #282828;
        border-color: #535353;
        color: #FFFFFF;
    }
    .stSlider > div > div > div {
        color: #1DB954;
    }

    /* Dividers */
    hr {
        border-color: #282828 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #181818 !important;
        border-radius: 8px;
        color: #FFFFFF !important;
        font-weight: 600;
    }

    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Buttons */
    .stButton > button {
        background-color: #1DB954;
        color: #000000;
        border: none;
        border-radius: 500px;
        font-weight: 700;
        padding: 8px 32px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1ED760;
        transform: scale(1.04);
    }

    /* Info/warning boxes */
    .stAlert {
        background-color: #181818;
        border-radius: 8px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #121212;
    }
    ::-webkit-scrollbar-thumb {
        background: #535353;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #B3B3B3;
    }

    /* Custom card class */
    .spotify-card {
        background: #181818;
        border-radius: 8px;
        padding: 24px;
        border: 1px solid #28282866;
        margin-bottom: 16px;
    }
    .spotify-card:hover {
        background: #282828;
        transition: background 0.3s ease;
    }

    /* Status badges */
    .badge-critical {
        background: #E8115B22;
        color: #E8115B;
        padding: 4px 12px;
        border-radius: 500px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-high {
        background: #FF643722;
        color: #FF6437;
        padding: 4px 12px;
        border-radius: 500px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-medium {
        background: #F59B2322;
        color: #F59B23;
        padding: 4px 12px;
        border-radius: 500px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-low {
        background: #509BF522;
        color: #509BF5;
        padding: 4px 12px;
        border-radius: 500px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
"""
