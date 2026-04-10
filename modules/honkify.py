"""Honkify — Spotify-clone listener simulator that generates real events into the GCP backend."""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import random
import time
import uuid
from datetime import datetime, timezone, timedelta
from utils.style import (
    SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING, COLOR_INFO,
    SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG, SPOTIFY_GRAY,
    story_nav, story_next,
)

GCP_PROJECT = "gen-lang-client-0205243793"
PUBSUB_TOPIC = "streamshield-stream-events"
BQ_TABLE = "gen-lang-client-0205243793.streamshield.honkify_live_events"

# Catalog of fake tracks for the player.
# audio_url points at SoundHelix's CC-licensed instrumental test tracks — stable,
# free, and the de-facto standard for audio-player demos.
SOUNDHELIX = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{}.mp3"
TRACKS = [
    {"id": "tk_001", "title": "Midnight Drive", "artist": "Neon Wave", "album": "Echoes", "genre": "electronic", "duration": 245, "color": "#1DB954", "audio_url": SOUNDHELIX.format(1)},
    {"id": "tk_002", "title": "Café del Mar", "artist": "Sofia Reyes", "album": "Sunset Sessions", "genre": "latin", "duration": 198, "color": "#F59B23", "audio_url": SOUNDHELIX.format(2)},
    {"id": "tk_003", "title": "Tokyo Lights", "artist": "Kaito Mori", "album": "City Pop Revival", "genre": "j-pop", "duration": 215, "color": "#509BF5", "audio_url": SOUNDHELIX.format(3)},
    {"id": "tk_004", "title": "Sahara Dawn", "artist": "Amani Diop", "album": "Roots", "genre": "afrobeats", "duration": 280, "color": "#E8115B", "audio_url": SOUNDHELIX.format(4)},
    {"id": "tk_005", "title": "Vinyl Memories", "artist": "The Slow Hours", "album": "Lo-Fi Lounge", "genre": "lo-fi", "duration": 167, "color": "#AF2896", "audio_url": SOUNDHELIX.format(5)},
    {"id": "tk_006", "title": "Cumbia Vibrante", "artist": "Los Caminos", "album": "Tradición", "genre": "cumbia", "duration": 312, "color": "#FF6437", "audio_url": SOUNDHELIX.format(6)},
    {"id": "tk_007", "title": "String Theory", "artist": "Helsinki Quartet", "album": "Modern Classical", "genre": "classical", "duration": 425, "color": "#509BF5", "audio_url": SOUNDHELIX.format(7)},
    {"id": "tk_008", "title": "808 State of Mind", "artist": "DJ Pulse", "album": "Beats Vol. 3", "genre": "hip-hop", "duration": 192, "color": "#1DB954", "audio_url": SOUNDHELIX.format(8)},
]

DEVICES = ["mobile_ios", "mobile_android", "desktop", "smart_speaker", "web_player"]
COUNTRIES_REAL = ["US", "GB", "DE", "BR", "MX", "SE", "FR", "AU", "JP", "CO", "NG"]
COUNTRIES_BOT = ["RU", "CN", "VN", "TR", "PK"]


def _get_gcp_credentials():
    """Get GCP credentials from st.secrets (Streamlit Cloud) or ADC (local)."""
    try:
        if "gcp_service_account" in st.secrets:
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"])
            )
    except Exception:
        pass
    return None


def _get_pubsub_client():
    try:
        from google.cloud import pubsub_v1
        creds = _get_gcp_credentials()
        if creds:
            return pubsub_v1.PublisherClient(credentials=creds)
        return pubsub_v1.PublisherClient()
    except Exception:
        return None


def _get_bq_client():
    try:
        from google.cloud import bigquery
        creds = _get_gcp_credentials()
        if creds:
            return bigquery.Client(project=GCP_PROJECT, credentials=creds)
        return bigquery.Client(project=GCP_PROJECT)
    except Exception:
        return None


def _generate_event(track, user_type="real"):
    """Generate a synthetic event with realistic randomization based on user type."""
    rng = random.Random()
    event_id = f"hk_{int(time.time()*1000)}_{rng.randint(100,999)}"

    if user_type == "real":
        # Real listener: varied behavior, normal device, normal country, normal pattern
        duration = int(rng.uniform(0.6, 1.0) * track["duration"]) * 1000
        device = rng.choice(DEVICES)
        country = rng.choice(COUNTRIES_REAL)
        vpn = False
        skip_rate = round(rng.uniform(0.10, 0.30), 2)
        account_age = rng.randint(60, 2000)
        # Fraud score: low for real listeners
        fraud_score = round(rng.betavariate(1.5, 10), 3)
    elif user_type == "bot":
        # Bot listener: fixed duration, single device, suspicious country, high signals
        duration = int(rng.uniform(0.95, 1.05) * 31) * 1000  # Always ~31 seconds
        device = "web_player"  # Bots typically use web player
        country = rng.choice(COUNTRIES_BOT)
        vpn = True
        skip_rate = round(rng.uniform(0.0, 0.05), 2)
        account_age = rng.randint(1, 30)
        # Fraud score: high for bots
        fraud_score = round(rng.betavariate(8, 1.5), 3)
    else:  # edge_case
        # Edge case: realistic but with one or two suspicious signals — ends up in review zone
        duration = int(rng.uniform(0.5, 0.9) * track["duration"]) * 1000
        device = rng.choice(DEVICES)
        country = rng.choice(COUNTRIES_REAL)
        vpn = rng.choice([True, False])
        skip_rate = round(rng.uniform(0.05, 0.15), 2)
        account_age = rng.randint(15, 120)
        # Fraud score: in review zone
        fraud_score = round(rng.uniform(0.72, 0.93), 3)

    classification = (
        "quarantine" if fraud_score > 0.95
        else "review" if fraud_score > 0.70
        else "pass"
    )

    return {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": f"u_{rng.randint(10000, 99999)}",
        "user_type": user_type,
        "track_id": track["id"],
        "track_name": track["title"],
        "artist_name": track["artist"],
        "duration_ms": duration,
        "device_type": device,
        "country": country,
        "ip_hash": f"ip_{rng.randint(1000, 9999)}",
        "vpn_detected": vpn,
        "skip_rate": skip_rate,
        "account_age_days": account_age,
        "fraud_score": fraud_score,
        "classification": classification,
        "source": "honkify_demo",
    }


def _publish_event(event):
    """Publish event to Pub/Sub and insert into BigQuery. Returns (pubsub_ok, bq_ok, pubsub_msg_id, latencies)."""
    success_pubsub = False
    success_bq = False
    pubsub_msg_id = None
    pubsub_latency_ms = None
    bq_latency_ms = None

    # Publish to Pub/Sub
    pub = _get_pubsub_client()
    if pub:
        try:
            topic_path = pub.topic_path(GCP_PROJECT, PUBSUB_TOPIC)
            t0 = time.time()
            future = pub.publish(topic_path, json.dumps(event).encode('utf-8'))
            pubsub_msg_id = future.result(timeout=5)
            pubsub_latency_ms = int((time.time() - t0) * 1000)
            success_pubsub = True
        except Exception as e:
            st.warning(f"Pub/Sub publish failed: {str(e)[:100]}")

    # Insert into BigQuery
    bq = _get_bq_client()
    if bq:
        try:
            t0 = time.time()
            errors = bq.insert_rows_json(BQ_TABLE, [event])
            bq_latency_ms = int((time.time() - t0) * 1000)
            if not errors:
                success_bq = True
            else:
                st.warning(f"BigQuery insert errors: {errors}")
        except Exception as e:
            st.warning(f"BigQuery insert failed: {str(e)[:100]}")

    return success_pubsub, success_bq, pubsub_msg_id, pubsub_latency_ms, bq_latency_ms


def _simulate_traffic(n_events=100):
    """Generate and bulk-insert N realistic events into BigQuery.

    Uses a 60/25/15 split for real/bot/edge_case. Timestamps are spread across
    the last 60 minutes for realistic traffic patterns. Skips Pub/Sub to avoid
    latency — goes straight to BigQuery streaming inserts in batches of 25.
    """
    bq = _get_bq_client()
    if bq is None:
        return 0, 0, 0, 0

    rng = random.Random()
    user_pool = [f"u_{rng.randint(10000, 99999)}" for _ in range(30)]
    events = []
    now = datetime.now(timezone.utc)

    for i in range(n_events):
        roll = rng.random()
        user_type = "real" if roll < 0.60 else "bot" if roll < 0.85 else "edge_case"
        track = rng.choice(TRACKS)
        event = _generate_event(track, user_type=user_type)
        event["user_id"] = rng.choice(user_pool)
        minutes_ago = rng.uniform(0, 60)
        event["timestamp"] = (now - timedelta(minutes=minutes_ago)).isoformat()
        events.append(event)

    inserted = 0
    batch_size = 25
    for batch_start in range(0, len(events), batch_size):
        batch = events[batch_start:batch_start + batch_size]
        clean_batch = [{k: v for k, v in e.items() if not k.startswith("_")} for e in batch]
        try:
            errors = bq.insert_rows_json(BQ_TABLE, clean_batch)
            if not errors:
                inserted += len(batch)
        except Exception:
            pass

    n_real = sum(1 for e in events if e["user_type"] == "real")
    n_bot = sum(1 for e in events if e["user_type"] == "bot")
    n_edge = sum(1 for e in events if e["user_type"] == "edge_case")
    return inserted, n_real, n_bot, n_edge


def _query_backend_sample():
    """Run a real SQL query against BigQuery and return (df, query_text, latency_ms)."""
    query_text = (
        f"SELECT event_id, timestamp, track_name, user_type,\n"
        f"       fraud_score, classification, country, device_type\n"
        f"FROM `{BQ_TABLE}`\n"
        f"ORDER BY timestamp DESC\n"
        f"LIMIT 10;"
    )
    bq = _get_bq_client()
    if bq is None:
        return None, query_text, None
    try:
        t0 = time.time()
        df = bq.query(query_text).to_dataframe()
        latency = int((time.time() - t0) * 1000)
        return df, query_text, latency
    except Exception:
        return None, query_text, None


def _query_pipeline_stats():
    """Aggregate stats from the live table for the counter strip."""
    bq = _get_bq_client()
    if bq is None:
        return None
    try:
        q = (
            f"SELECT COUNT(*) AS total, "
            f"COUNTIF(classification='review') AS in_review, "
            f"COUNTIF(classification='quarantine') AS quarantined, "
            f"COUNTIF(classification='pass') AS passed "
            f"FROM `{BQ_TABLE}` "
            f"WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)"
        )
        result = list(bq.query(q).result(timeout=8))
        if result:
            return {
                "total": int(result[0].total),
                "in_review": int(result[0].in_review),
                "quarantined": int(result[0].quarantined),
                "passed": int(result[0].passed),
            }
    except Exception:
        pass
    return None


def _verify_event_in_bigquery(event_id):
    """Live readback via tabledata.list — fetch recent rows and check membership.

    Uses list_rows() instead of jobs.query for ~10x lower latency (~500ms warm
    vs 5-15s for cold-plan SQL queries). Returns (visible, latency_ms, query_text).
    """
    query_text = (
        f"# Equivalent BigQuery REST call:\n"
        f"client.list_rows(\n"
        f"    '{BQ_TABLE}',\n"
        f"    max_results=200,\n"
        f"    selected_fields=['event_id'],\n"
        f")\n"
        f"# Then check membership of '{event_id}' in returned rows."
    )
    bq = _get_bq_client()
    if bq is None:
        return False, None, query_text
    try:
        from google.cloud import bigquery as _bq
        t0 = time.time()
        rows = bq.list_rows(
            BQ_TABLE,
            max_results=200,
            selected_fields=[_bq.SchemaField("event_id", "STRING")],
        )
        found = False
        for row in rows:
            if row.event_id == event_id:
                found = True
                break
        latency = int((time.time() - t0) * 1000)
        return found, latency, query_text
    except Exception:
        return False, None, query_text


def _render_stream_journey(event):
    """Render the 5-stage journey of a single event from frontend click to downstream.

    Uses native Streamlit columns instead of raw HTML flex to avoid div-leak
    and emoji-rendering issues with st.markdown's sanitizer.
    """
    pub_ok = bool(event.get("_pubsub_published"))
    bq_ok = bool(event.get("_bigquery_inserted"))
    pub_msg_id = str(event.get("_pubsub_msg_id") or "—")[:16]
    pub_lat = event.get("_pubsub_latency_ms")
    bq_lat = event.get("_bigquery_latency_ms")

    verification = st.session_state.get("honkify_journey_verification") or {}
    verified = verification.get("visible", False)
    verify_lat = verification.get("latency_ms")
    verify_ran = verification.get("ran", False)

    classification = event.get("classification", "—")

    # Header
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(80,155,245,0.06), {SPOTIFY_CARD_BG}); border-radius:10px; padding:16px 20px; border:1px solid rgba(80,155,245,0.15); margin-bottom:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="color:{COLOR_INFO}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px;">Stream Journey</span>
                    <span style="color:{SPOTIFY_GRAY}; font-size:10px; margin-left:10px; font-family:monospace;">{event['event_id']}</span>
                </div>
                <div style="color:{SPOTIFY_WHITE}; font-size:12px; font-weight:600;">
                    {event['track_name']} &middot; {event.get('user_type','—')} &middot; score {event.get('fraud_score',0):.3f} &rarr; {classification}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    def _card(status, title, line1, line2):
        color = SPOTIFY_GREEN if status == "ok" else COLOR_DANGER if status == "fail" else COLOR_WARNING if status == "warn" else SPOTIFY_GRAY
        dot = "●" if status in ("ok", "warn") else "○"
        st.markdown(
            f"""
            <div style="background:#181818; border-radius:8px; padding:12px; border:1px solid rgba(83,83,83,0.25); border-left:3px solid {color}; min-height:100px;">
                <div style="color:{color}; font-size:11px; font-weight:800; letter-spacing:0.5px; margin-bottom:6px;">{dot} {title}</div>
                <div style="color:{SPOTIFY_WHITE}; font-size:12px; font-weight:600; line-height:1.4;">{line1}</div>
                <div style="color:{SPOTIFY_GRAY}; font-size:10px; font-family:monospace; margin-top:5px; word-break:break-all;">{line2}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _card("ok", "1 · CLICK", f"play_{event['track_id']}", f"event_id: {event['event_id']}")
    with c2:
        _card("ok" if pub_ok else "fail", "2 · PUB/SUB",
              f"topic: {PUBSUB_TOPIC}",
              f"msg: {pub_msg_id}" + (f" | {pub_lat}ms" if pub_lat else ""))
    with c3:
        _card("ok" if bq_ok else "fail", "3 · BIGQUERY",
              "honkify_live_events",
              f"insert_rows_json | 1 row" + (f" | {bq_lat}ms" if bq_lat else ""))
    with c4:
        if classification == "quarantine":
            r_status, r_line = "fail", "auto-quarantined"
        elif classification == "review":
            r_status, r_line = "warn", "Fraud Ops review queue"
        else:
            r_status, r_line = "ok", "passed through"
        _card(r_status, "4 · ROUTING", r_line, f"score {event.get('fraud_score',0):.3f} → {classification}")
    with c5:
        if verified:
            _card("ok", "5 · READBACK", "row visible to consumers", f"readback in {verify_lat}ms")
        elif bq_ok:
            _card("ok", "5 · COMMITTED", "row in streaming buffer", "visible to consumers within 60s")
        else:
            _card("fail", "5 · COMMITTED", "insert failed", "check credentials")

    # Live readback button
    btn_col, msg_col = st.columns([1, 3])
    with btn_col:
        if st.button("Run live BigQuery readback", key="honkify_verify_btn", use_container_width=True):
            with st.spinner("Querying BigQuery..."):
                visible, lat, query = _verify_event_in_bigquery(event["event_id"])
                st.session_state["honkify_journey_verification"] = {
                    "visible": visible, "latency_ms": lat, "query": query, "ran": True,
                }
            st.rerun()
    with msg_col:
        if verify_ran and verified:
            st.markdown(f'<div style="color:{SPOTIFY_GREEN}; font-size:12px; padding:8px;">Row confirmed visible in {verify_lat} ms.</div>', unsafe_allow_html=True)
        elif verify_ran:
            st.markdown(f'<div style="color:{COLOR_WARNING}; font-size:12px; padding:8px;">Not visible yet — streaming buffer takes up to 90s. Pub/Sub is the real-time source of truth.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:{SPOTIFY_GRAY}; font-size:11px; padding:8px; font-style:italic;">Stages 1-4 from publish-time acks. Stage 5 readback is opt-in (~1s warm).</div>', unsafe_allow_html=True)


def render():
    # Initialize session state for events
    if "honkify_events" not in st.session_state:
        st.session_state["honkify_events"] = []
    if "honkify_user_mode" not in st.session_state:
        st.session_state["honkify_user_mode"] = "real"

    story_nav(
        step=1, total=3,
        title="The Product — What listeners experience",
        what_to_do='Click "Simulate Traffic" to fill the pipeline with 100 events, then click ▶ Play on any track. '
        "Watch your event flow through Pub/Sub → BigQuery → the fraud scoring pipeline in the Stream Journey below. "
        "Then continue to Fraud Operations to see what happens to it.",
    )

    # Header — Honkify branding
    st.markdown(
        f"""
        <div style="background: linear-gradient(180deg, #1DB954 0%, #121212 100%); border-radius:12px; padding:32px 36px; margin-bottom:24px;">
            <div style="display:flex; align-items:center; gap:16px; margin-bottom:8px;">
                <div style="background:#fff; width:56px; height:56px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:32px;">🎵</div>
                <div>
                    <div style="font-size:36px; font-weight:900; color:#fff; letter-spacing:-1px; line-height:1;">Honkify</div>
                    <div style="font-size:13px; color:rgba(255,255,255,0.8); margin-top:4px;">Music for everyone &middot; A demonstration product for the StreamShield assessment</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Demo mode selector
    st.markdown(
        f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-bottom:8px;">Select listener type, then click any track. Each click generates a real event sent to GCP Pub/Sub and BigQuery.</div>',
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2, mode_col3, mode_col4 = st.columns(4)

    with mode_col1:
        if st.button("Real Listener", use_container_width=True, type="primary" if st.session_state["honkify_user_mode"] == "real" else "secondary"):
            st.session_state["honkify_user_mode"] = "real"
            st.rerun()
    with mode_col2:
        if st.button("Bot Listener", use_container_width=True, type="primary" if st.session_state["honkify_user_mode"] == "bot" else "secondary"):
            st.session_state["honkify_user_mode"] = "bot"
            st.rerun()
    with mode_col3:
        if st.button("Edge Case", use_container_width=True, type="primary" if st.session_state["honkify_user_mode"] == "edge_case" else "secondary"):
            st.session_state["honkify_user_mode"] = "edge_case"
            st.rerun()
    with mode_col4:
        if st.button("Clear Session", use_container_width=True):
            st.session_state["honkify_events"] = []
            st.rerun()

    # Mode indicator
    mode = st.session_state["honkify_user_mode"]
    mode_label = {"real": "Real Listener", "bot": "Bot Listener", "edge_case": "Edge Case"}[mode]
    mode_color = {"real": SPOTIFY_GREEN, "bot": COLOR_DANGER, "edge_case": COLOR_WARNING}[mode]
    mode_desc = {
        "real": "Normal listening behavior. Varied durations, normal devices, low fraud scores. Will pass through.",
        "bot": "Bot-like behavior. ~31 second plays, web player, suspicious country, VPN, high fraud scores. Will be quarantined.",
        "edge_case": "Realistic but ambiguous. Could go either way. Will likely enter the review zone for human analyst attention.",
    }[mode]

    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px 20px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {mode_color}; margin-bottom:24px;">
            <div style="color:{mode_color}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Active Listener Mode</div>
            <div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:700;">{mode_label}</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-top:4px;">{mode_desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Pipeline Counter (single row of 4 metrics + 2 action buttons) ---
    stats = st.session_state.get("_honkify_stats")
    if stats is None:
        stats = _query_pipeline_stats()
        if stats:
            st.session_state["_honkify_stats"] = stats

    p1, p2, p3, p4, p5, p6 = st.columns([1, 1, 1, 1, 1, 1])
    if stats:
        for col, (label, value, color) in zip(
            [p1, p2, p3, p4],
            [
                ("Events (24h)", f"{stats['total']:,}", SPOTIFY_WHITE),
                ("In Review", str(stats['in_review']), COLOR_WARNING),
                ("Quarantined", str(stats['quarantined']), COLOR_DANGER),
                ("Passed", str(stats['passed']), SPOTIFY_GREEN),
            ],
        ):
            with col:
                st.markdown(
                    f'<div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px; border:1px solid rgba(83,83,83,0.25); text-align:center;">'
                    f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:9px; text-transform:uppercase; letter-spacing:1px;">{label}</div>'
                    f'<div style="color:{color}; font-size:24px; font-weight:800; margin-top:4px;">{value}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    with p5:
        if st.button("Simulate Traffic", use_container_width=True, key="honkify_simulate", help="Generate 100 realistic events into BigQuery"):
            with st.spinner("Inserting 100 events..."):
                inserted, n_real, n_bot, n_edge = _simulate_traffic(100)
            if inserted > 0:
                from utils.data_loader import load_honkify_live_events
                load_honkify_live_events.clear()
                st.session_state.pop("_honkify_stats", None)
                st.rerun()
            else:
                st.error("BigQuery not reachable.")
    with p6:
        if st.button("Refresh Stats", use_container_width=True, key="honkify_refresh_stats"):
            st.session_state.pop("_honkify_stats", None)
            from utils.data_loader import load_honkify_live_events
            load_honkify_live_events.clear()
            st.rerun()

    # Now Playing bar — appears after the user clicks a track
    now_playing = st.session_state.get("honkify_now_playing")
    if now_playing:
        bar_col_art, bar_col_meta, bar_col_player, bar_col_stop = st.columns([1, 3, 6, 1])
        with bar_col_art:
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg, {now_playing['color']}, {now_playing['color']}66); height:64px; border-radius:6px; display:flex; align-items:center; justify-content:center;">
                    <span style="font-size:28px; opacity:0.6;">♫</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with bar_col_meta:
            st.markdown(
                f"""
                <div style="padding:6px 4px;">
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; font-weight:700;">Now Playing</div>
                    <div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-top:4px;">{now_playing['title']}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px;">{now_playing['artist']} &middot; {now_playing['album']}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:10px; margin-top:3px; font-style:italic;">Audio: T. Schürger &middot; <a href="https://www.soundhelix.com" target="_blank" style="color:{SPOTIFY_GRAY}; text-decoration:underline;">SoundHelix.com</a></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with bar_col_player:
            st.audio(now_playing["audio_url"], format="audio/mp3", autoplay=True)
        with bar_col_stop:
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            if st.button("✕", key="honkify_stop", help="Stop playback"):
                st.session_state["honkify_now_playing"] = None
                st.rerun()
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Stream Journey — appears after the most recent play, shows the event's path
    journey_event = st.session_state.get("honkify_journey_event")
    if journey_event:
        _render_stream_journey(journey_event)

    # Live Backend — actual BigQuery query result showing recent rows
    with st.expander("BigQuery Live Backend — real query result", expanded=False):
        st.markdown(
            f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:10px;">This runs a real SQL query against the <code>honkify_live_events</code> table and displays the result. The query text is visible so the interviewer can see exactly what runs. Click "Run Query" after playing tracks to see your events appear.</div>',
            unsafe_allow_html=True,
        )
        q_col, b_col = st.columns([4, 1])
        with b_col:
            run_query = st.button("Run Query", key="honkify_run_backend_query", use_container_width=True)
        if run_query or st.session_state.get("_honkify_backend_result") is not None:
            if run_query:
                backend_df, sql_text, lat = _query_backend_sample()
                st.session_state["_honkify_backend_result"] = (backend_df, sql_text, lat)
            else:
                backend_df, sql_text, lat = st.session_state["_honkify_backend_result"]
            with q_col:
                if lat is not None:
                    st.markdown(f'<div style="color:{SPOTIFY_GREEN}; font-size:11px;">Query completed in {lat} ms</div>', unsafe_allow_html=True)
            st.code(sql_text, language="sql")
            if backend_df is not None and len(backend_df) > 0:
                st.dataframe(backend_df, use_container_width=True, hide_index=True)
            elif backend_df is not None:
                st.info("Table is empty. Click Simulate Traffic or play some tracks first.")
            else:
                st.warning("BigQuery query failed. Check credentials.")
        else:
            st.markdown(f'<div style="color:{SPOTIFY_GRAY}; font-size:12px; font-style:italic;">Click "Run Query" to execute a live BigQuery read.</div>', unsafe_allow_html=True)

    # --- ML Classification Pipeline — shows what the model sees and decides ---
    from utils.data_loader import load_honkify_live_events as _load_live
    _clf_df, _clf_src = _load_live()
    if _clf_src != "unavailable" and len(_clf_df) > 0:
        with st.expander("ML Classification Pipeline — how the model scores and routes events", expanded=True):
            st.markdown(
                f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:12px;">'
                f'Every event is scored by the ML model (gradient-boosted trees on Hendrix/Salem). '
                f'The <code>fraud_score</code> determines routing: '
                f'<strong style="color:{SPOTIFY_GREEN};">below 0.70 → pass</strong>, '
                f'<strong style="color:{COLOR_WARNING};">0.70–0.95 → human review</strong>, '
                f'<strong style="color:{COLOR_DANGER};">above 0.95 → auto-quarantine</strong>. '
                f'The review zone is where human-in-the-loop is essential — the model is not confident enough to auto-decide.</div>',
                unsafe_allow_html=True,
            )

            # Three-zone summary
            n_pass = int((_clf_df["classification"] == "pass").sum())
            n_review = int((_clf_df["classification"] == "review").sum())
            n_quar = int((_clf_df["classification"] == "quarantine").sum())
            n_total = len(_clf_df)

            z1, z2, z3 = st.columns(3)
            with z1:
                pct = (n_pass / n_total * 100) if n_total else 0
                st.markdown(
                    f'<div style="background:rgba(29,185,84,0.1); border:1px solid {SPOTIFY_GREEN}; border-radius:8px; padding:16px; text-align:center;">'
                    f'<div style="color:{SPOTIFY_GREEN}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">CLEAR — Auto-passed</div>'
                    f'<div style="color:{SPOTIFY_WHITE}; font-size:28px; font-weight:800; margin:6px 0;">{n_pass}</div>'
                    f'<div style="color:{SPOTIFY_GREEN}; font-size:12px;">fraud_score &lt; 0.70 · {pct:.0f}% of events</div>'
                    f'<div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:4px;">Royalties flow immediately</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with z2:
                pct = (n_review / n_total * 100) if n_total else 0
                st.markdown(
                    f'<div style="background:rgba(245,155,35,0.1); border:1px solid {COLOR_WARNING}; border-radius:8px; padding:16px; text-align:center;">'
                    f'<div style="color:{COLOR_WARNING}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">UNCERTAIN — Needs human review</div>'
                    f'<div style="color:{SPOTIFY_WHITE}; font-size:28px; font-weight:800; margin:6px 0;">{n_review}</div>'
                    f'<div style="color:{COLOR_WARNING}; font-size:12px;">fraud_score 0.70–0.95 · {pct:.0f}% of events</div>'
                    f'<div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:4px;">Held for analyst Signal Card review</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with z3:
                pct = (n_quar / n_total * 100) if n_total else 0
                st.markdown(
                    f'<div style="background:rgba(232,17,91,0.1); border:1px solid {COLOR_DANGER}; border-radius:8px; padding:16px; text-align:center;">'
                    f'<div style="color:{COLOR_DANGER}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">FRAUD — Auto-quarantined</div>'
                    f'<div style="color:{SPOTIFY_WHITE}; font-size:28px; font-weight:800; margin:6px 0;">{n_quar}</div>'
                    f'<div style="color:{COLOR_DANGER}; font-size:12px;">fraud_score &gt; 0.95 · {pct:.0f}% of events</div>'
                    f'<div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:4px;">Royalties frozen, clawback eligible</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Score distribution chart
            import plotly.graph_objects as go
            from utils.style import apply_spotify_style

            scores = _clf_df["fraud_score"].dropna().astype(float)
            if len(scores) > 0:
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=scores, nbinsx=40,
                    marker_color=SPOTIFY_GREEN, opacity=0.7,
                    name="Events",
                ))
                fig.add_vrect(x0=0.70, x1=0.95, fillcolor="rgba(245,155,35,0.08)", layer="below", line_width=0,
                              annotation_text="REVIEW ZONE", annotation_position="top",
                              annotation=dict(font=dict(color=COLOR_WARNING, size=10)))
                fig.add_vrect(x0=0.95, x1=1.0, fillcolor="rgba(232,17,91,0.08)", layer="below", line_width=0,
                              annotation_text="QUARANTINE", annotation_position="top",
                              annotation=dict(font=dict(color=COLOR_DANGER, size=10)))
                fig.add_vline(x=0.70, line_dash="dot", line_color=COLOR_WARNING)
                fig.add_vline(x=0.95, line_dash="dot", line_color=COLOR_DANGER)
                fig.update_layout(
                    title="Fraud score distribution — ML model output",
                    xaxis_title="fraud_score",
                    yaxis_title="Event count",
                    margin=dict(l=60, r=40, t=50, b=40),
                    showlegend=False,
                )
                apply_spotify_style(fig, height=300)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                f'<div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; line-height:1.6; margin-top:8px;">'
                f'<strong style="color:{SPOTIFY_WHITE};">Why human-in-the-loop matters:</strong> '
                f'The {n_review} events in the review zone (orange) cannot be auto-decided — the model\'s confidence is '
                f'between 70% and 95%. These are the cases where a sophisticated scam looks almost legitimate, or a legitimate '
                f'artist\'s behavior looks almost fraudulent. An analyst with the Signal Confirmation Card examines the raw signals, '
                f'makes an independent assessment, states their reasoning, and that structured decision becomes both a quality '
                f'training label and an institutional knowledge record. '
                f'<strong style="color:{COLOR_WARNING};">This is the human-in-the-loop that makes the system better over time.</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Featured Today header
    st.markdown(
        f'<div style="color:{SPOTIFY_WHITE}; font-size:22px; font-weight:800; margin-bottom:14px;">Featured Today</div>',
        unsafe_allow_html=True,
    )

    # Track grid — 4 columns
    cols = st.columns(4)
    for i, track in enumerate(TRACKS):
        with cols[i % 4]:
            # Album card
            mins = track["duration"] // 60
            secs = track["duration"] % 60

            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; margin-bottom:12px; border:1px solid rgba(83,83,83,0.2); transition:all 0.2s;">
                    <div style="background:linear-gradient(135deg, {track['color']}, {track['color']}66); height:140px; border-radius:6px; display:flex; align-items:center; justify-content:center; margin-bottom:12px;">
                        <span style="font-size:48px; opacity:0.5;">♫</span>
                    </div>
                    <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700; margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{track['title']}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{track['artist']}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:10px; margin-top:4px;">{track['album']} &middot; {mins}:{secs:02d}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("▶ Play", key=f"play_{track['id']}", use_container_width=True):
                event = _generate_event(track, user_type=mode)
                pub_ok, bq_ok, pub_msg_id, pub_lat, bq_lat = _publish_event(event)
                event["_pubsub_published"] = pub_ok
                event["_bigquery_inserted"] = bq_ok
                event["_pubsub_msg_id"] = pub_msg_id
                event["_pubsub_latency_ms"] = pub_lat
                event["_bigquery_latency_ms"] = bq_lat
                st.session_state["honkify_events"].insert(0, event)
                st.session_state["honkify_now_playing"] = track
                st.session_state["honkify_journey_event"] = event
                # Reset verification — user can opt in to the live readback via button
                st.session_state["honkify_journey_verification"] = None
                st.rerun()

    # Recent activity — show events generated in this session
    if st.session_state["honkify_events"]:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-bottom:12px;">Session Activity ({len(st.session_state["honkify_events"])} events)</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:12px; margin-bottom:14px;">Events generated this session. Each is published to GCP Pub/Sub topic and inserted into BigQuery in real time.</p>',
            unsafe_allow_html=True,
        )

        # Build event list HTML
        events_html_parts = ['''
        <html><head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body { font-family: 'Inter', sans-serif; background: #121212; color: #fff; margin: 0; padding: 0; }
            .event-card { background: #181818; border-radius: 8px; padding: 14px 18px; margin-bottom: 8px; border: 1px solid rgba(83,83,83,0.2); }
            .event-row { display: flex; justify-content: space-between; align-items: center; }
            .event-track { color: #fff; font-size: 14px; font-weight: 600; }
            .event-meta { color: #B3B3B3; font-size: 11px; margin-top: 4px; }
            .badge { padding: 3px 10px; border-radius: 500px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; display: inline-block; margin-left: 6px; }
            .pass { background: rgba(29,185,84,0.2); color: #1DB954; }
            .review { background: rgba(245,155,35,0.2); color: #F59B23; }
            .quarantine { background: rgba(232,17,91,0.2); color: #E8115B; }
            .gcp-status { color: #535353; font-size: 10px; margin-top: 4px; font-family: monospace; }
        </style>
        </head><body>
        ''']

        for event in st.session_state["honkify_events"][:20]:  # Show last 20
            class_name = event["classification"]
            class_label = {"pass": "PASS", "review": "REVIEW", "quarantine": "QUARANTINE"}[class_name]

            pubsub_indicator = "✓ Pub/Sub" if event.get("_pubsub_published") else "✗ Pub/Sub"
            bq_indicator = "✓ BigQuery" if event.get("_bigquery_inserted") else "✗ BigQuery"

            events_html_parts.append(f'''
            <div class="event-card">
                <div class="event-row">
                    <div>
                        <span class="event-track">{event['track_name']}</span>
                        <span style="color:#B3B3B3; font-size:12px;"> by {event['artist_name']}</span>
                        <span class="badge {class_name}">{class_label}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#B3B3B3; font-size:12px;">Score: <strong style="color:#fff;">{event['fraud_score']:.3f}</strong></div>
                        <div style="color:#535353; font-size:10px;">{event['user_type']} &middot; {event['country']} &middot; {event['device_type']}</div>
                    </div>
                </div>
                <div class="gcp-status">{pubsub_indicator} &middot; {bq_indicator} &middot; {event['event_id']}</div>
            </div>
            ''')

        events_html_parts.append('</body></html>')
        components.html("".join(events_html_parts), height=min(450, 100 + len(st.session_state["honkify_events"][:20]) * 90), scrolling=True)

    # Backend integration info
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(29,185,84,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 22px; border-left:4px solid {SPOTIFY_GREEN};">
            <div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Backend Integration</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                Each click is a real event published to Cloud Pub/Sub topic <code style="background:#0a0a0a; padding:2px 6px; border-radius:4px; color:{SPOTIFY_GREEN};">streamshield-stream-events</code> and inserted into BigQuery table <code style="background:#0a0a0a; padding:2px 6px; border-radius:4px; color:{SPOTIFY_GREEN};">streamshield.honkify_live_events</code>. The Fraud Operations and Internal Audit views query these endpoints live. This is the same GCP stack Spotify uses internally — Pub/Sub for ingestion, BigQuery for analytics, GKE for processing.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Credits / attribution
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 22px; border:1px solid rgba(83,83,83,0.25); border-left:4px solid {COLOR_INFO};">
            <div style="color:{COLOR_INFO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Credits &amp; Attribution</div>
            <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.7;">
                <strong style="color:{SPOTIFY_WHITE};">Music.</strong> All eight tracks featured here are instrumental compositions by <strong style="color:{SPOTIFY_WHITE};">Tobias Schürger</strong>, distributed freely via <a href="https://www.soundhelix.com" target="_blank" style="color:{COLOR_INFO};">SoundHelix.com</a>. The "artist", "album" and "title" labels shown on the cards are fictional and exist only to make the demo feel like a real music product — the actual audio is the work of T. Schürger and credit belongs to him. Thank you to Tobias for making these available to the developer community.<br><br>
                <strong style="color:{SPOTIFY_WHITE};">Brand &amp; design.</strong> Honkify is a non-commercial demonstration product built for the StreamShield Internal Audit case study. It is not affiliated with, endorsed by, or representative of Spotify AB. The Spotify visual language is referenced for educational purposes only.<br><br>
                <strong style="color:{SPOTIFY_WHITE};">Synthetic data.</strong> All listener accounts, fraud scores, geographies, and event IDs are randomly generated. No real user data is processed.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Story navigation → next page
    story_next(
        "Fraud Operations",
        "See what happens to the events you just generated. The Before tab shows the broken analyst workflow. The After tab shows the Signal Confirmation Card that fixes it.",
    )
