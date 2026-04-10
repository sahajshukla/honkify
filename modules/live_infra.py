"""Module: Live Infrastructure — Real-time connections to GCP backends."""

import streamlit as st
import pandas as pd
import json
import time
import os
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card,
)

GCP_PROJECT = "gen-lang-client-0205243793"
BQ_DATASET = "streamshield"
GCS_BUCKET = "streamshield-audit-data-lake"
PUBSUB_TOPIC = "streamshield-stream-events"
PUBSUB_SUB = "streamshield-stream-sub"


def _get_bq_client():
    try:
        from google.cloud import bigquery
        return bigquery.Client(project=GCP_PROJECT)
    except Exception:
        return None


def _get_pubsub_publisher():
    try:
        from google.cloud import pubsub_v1
        return pubsub_v1.PublisherClient()
    except Exception:
        return None


def _get_pubsub_subscriber():
    try:
        from google.cloud import pubsub_v1
        return pubsub_v1.SubscriberClient()
    except Exception:
        return None


def _get_gcs_client():
    try:
        from google.cloud import storage
        return storage.Client(project=GCP_PROJECT)
    except Exception:
        return None


def render():
    st.markdown("## Live Infrastructure")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Real-time connections to GCP backends. The dashboard reads from BigQuery (data warehouse), "
        "Cloud Storage (data lake), and Pub/Sub (streaming events) — the same services Spotify uses in production."
        "</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Connection Status", "BigQuery Live Queries", "Pub/Sub Stream", "Cloud Storage"])

    # ============================================
    # TAB 1: Connection Status
    # ============================================
    with tab1:
        st.markdown("### GCP Backend Connections")

        services = []

        # BigQuery check
        bq = _get_bq_client()
        bq_status = False
        bq_detail = ""
        if bq:
            try:
                tables = list(bq.list_tables(f"{GCP_PROJECT}.{BQ_DATASET}"))
                bq_status = True
                bq_detail = f"{len(tables)} tables"
            except Exception as e:
                bq_detail = str(e)[:80]
        services.append(("BigQuery", BQ_DATASET, bq_status, bq_detail, "Data Warehouse — Ground truth, ML scores, analyst reviews, model performance"))

        # Pub/Sub check
        pub = _get_pubsub_publisher()
        pubsub_status = False
        pubsub_detail = ""
        if pub:
            try:
                topic_path = pub.topic_path(GCP_PROJECT, PUBSUB_TOPIC)
                pub.get_topic(request={"topic": topic_path})
                pubsub_status = True
                pubsub_detail = f"Topic: {PUBSUB_TOPIC}"
            except Exception as e:
                pubsub_detail = str(e)[:80]
        services.append(("Cloud Pub/Sub", PUBSUB_TOPIC, pubsub_status, pubsub_detail, "Streaming — Real-time stream events ingestion"))

        # GCS check
        gcs = _get_gcs_client()
        gcs_status = False
        gcs_detail = ""
        if gcs:
            try:
                bucket = gcs.bucket(GCS_BUCKET)
                blobs = list(bucket.list_blobs(max_results=1))
                gcs_status = True
                all_blobs = list(bucket.list_blobs())
                gcs_detail = f"{len(all_blobs)} objects"
            except Exception as e:
                gcs_detail = str(e)[:80]
        services.append(("Cloud Storage", GCS_BUCKET, gcs_status, gcs_detail, "Data Lake — Raw CSVs, pipeline stage outputs"))

        for name, resource, status, detail, desc in services:
            status_color = SPOTIFY_GREEN if status else COLOR_DANGER
            status_text = "CONNECTED" if status else "UNAVAILABLE"
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {status_color}; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color:{SPOTIFY_WHITE}; font-size:17px; font-weight:700;">{name}</span>
                            <span style="color:{SPOTIFY_GRAY}; font-size:13px; margin-left:12px;">{resource}</span>
                        </div>
                        <span style="background:rgba({_hex_rgb(status_color)},0.2); color:{status_color}; padding:4px 14px; border-radius:500px; font-size:11px; font-weight:700; letter-spacing:0.5px;">{status_text}</span>
                    </div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-top:8px;">{desc}</div>
                    <div style="color:{SPOTIFY_GRAY}; font-size:12px; margin-top:4px;">{detail}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Architecture summary
        connected = sum(1 for _, _, s, _, _ in services if s)
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(29,185,84,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2); margin-top:16px;">
                <div style="color:{SPOTIFY_GREEN}; font-weight:700; font-size:14px; margin-bottom:8px;">{connected}/3 Backends Connected</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                    All data sources are live GCP services — not local files.
                    BigQuery serves as the analytical warehouse (equivalent to Spotify's data platform).
                    Cloud Pub/Sub provides the real-time event stream (equivalent to Spotify's event delivery infrastructure).
                    Cloud Storage acts as the raw data lake layer.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================
    # TAB 2: BigQuery Live Queries
    # ============================================
    with tab2:
        st.markdown("### BigQuery — Live Queries")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Run live SQL queries against the StreamShield dataset in BigQuery. "
            "This demonstrates real-time analytical capability — the same way Spotify's data teams query production data."
            "</p>",
            unsafe_allow_html=True,
        )

        bq = _get_bq_client()
        if not bq:
            st.warning("BigQuery client not available. Ensure GCP credentials are configured.")
            return

        # Preset queries
        preset = st.selectbox("Select a query", [
            "Custom SQL",
            "Stream classification breakdown",
            "Model performance trend (last 30 days)",
            "Analyst agreement rates",
            "False positive rate by genre (post-acquisition)",
            "Appeal outcomes by artist type",
            "Ground truth coverage",
            "Table sizes",
        ])

        preset_sql = {
            "Stream classification breakdown": f"""
SELECT classification, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events`
GROUP BY classification ORDER BY count DESC""",

            "Model performance trend (last 30 days)": f"""
SELECT date, precision, recall, f1_score, false_positive_rate, psi_score
FROM `{GCP_PROJECT}.{BQ_DATASET}.model_performance`
ORDER BY date DESC LIMIT 30""",

            "Analyst agreement rates": f"""
SELECT analyst_name,
       COUNT(*) as total_reviews,
       ROUND(AVG(CASE WHEN agreed_with_llm THEN 1 ELSE 0 END) * 100, 1) as agreement_pct,
       ROUND(AVG(time_to_decision_sec), 0) as avg_time_sec
FROM `{GCP_PROJECT}.{BQ_DATASET}.analyst_reviews`
GROUP BY analyst_name ORDER BY agreement_pct DESC""",

            "False positive rate by genre (post-acquisition)": f"""
SELECT genre,
       COUNT(*) as total_legitimate,
       SUM(CASE WHEN classification IN ('quarantine', 'review') THEN 1 ELSE 0 END) as false_flags,
       ROUND(SUM(CASE WHEN classification IN ('quarantine', 'review') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as fp_rate_pct
FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events`
WHERE NOT is_actually_fraudulent AND timestamp >= '2026-01-29'
GROUP BY genre HAVING COUNT(*) > 50
ORDER BY fp_rate_pct DESC""",

            "Appeal outcomes by artist type": f"""
SELECT artist_type,
       COUNT(*) as total_appeals,
       ROUND(AVG(days_to_resolve), 0) as avg_days,
       ROUND(SUM(CASE WHEN outcome = 'overturned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 0) as overturn_pct
FROM `{GCP_PROJECT}.{BQ_DATASET}.appeal_cases`
GROUP BY artist_type ORDER BY avg_days""",

            "Ground truth coverage": f"""
SELECT
  COUNT(*) as total_events,
  SUM(CASE WHEN has_ground_truth THEN 1 ELSE 0 END) as with_labels,
  ROUND(SUM(CASE WHEN has_ground_truth THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as coverage_pct
FROM `{GCP_PROJECT}.{BQ_DATASET}.p2_collated_ground_truth`""",

            "Table sizes": f"""
SELECT table_id, row_count, ROUND(size_bytes / 1024, 1) as size_kb
FROM `{GCP_PROJECT}.{BQ_DATASET}.__TABLES__`
ORDER BY row_count DESC""",
        }

        if preset == "Custom SQL":
            sql = st.text_area(
                "SQL Query",
                value=f"SELECT * FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events` LIMIT 10",
                height=120,
            )
        else:
            sql = preset_sql[preset]
            st.code(sql, language="sql")

        if st.button("Run Query", type="primary"):
            try:
                start = time.time()
                result_df = bq.query(sql).to_dataframe()
                elapsed = time.time() - start

                col1, col2 = st.columns([3, 1])
                with col2:
                    st.markdown(
                        f"""
                        <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:12px; border:1px solid rgba(83,83,83,0.2); text-align:center;">
                            <div style="color:{SPOTIFY_GRAY}; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Query Time</div>
                            <div style="color:{SPOTIFY_GREEN}; font-size:20px; font-weight:700;">{elapsed:.2f}s</div>
                            <div style="color:{SPOTIFY_GRAY}; font-size:10px;">{len(result_df)} rows</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col1:
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Query failed: {e}")

    # ============================================
    # TAB 3: Pub/Sub Stream
    # ============================================
    with tab3:
        st.markdown("### Pub/Sub — Real-Time Stream Events")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Publish and consume simulated streaming events via Cloud Pub/Sub — "
            "the same messaging service Spotify uses to process ~8 million events per second."
            "</p>",
            unsafe_allow_html=True,
        )

        col_pub, col_sub = st.columns(2)

        with col_pub:
            st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:12px;">Publish Events</div>', unsafe_allow_html=True)
            n_events = st.slider("Number of events to publish", 1, 50, 5)

            if st.button("Publish to Pub/Sub", type="primary"):
                pub = _get_pubsub_publisher()
                if pub:
                    import random
                    topic_path = pub.topic_path(GCP_PROJECT, PUBSUB_TOPIC)
                    devices = ['mobile_ios', 'mobile_android', 'desktop', 'smart_speaker']
                    countries = ['US', 'GB', 'DE', 'BR', 'IN', 'CO', 'NG']

                    published = []
                    for i in range(n_events):
                        event = {
                            'event_id': f'live_{int(time.time())}_{i}',
                            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'user_id': f'u_{random.randint(10000, 99999)}',
                            'track_id': f't_{random.randint(10000, 99999)}',
                            'duration_ms': random.randint(5000, 300000),
                            'device_type': random.choice(devices),
                            'country': random.choice(countries),
                            'is_premium': random.choice([True, False]),
                        }
                        future = pub.publish(topic_path, json.dumps(event).encode('utf-8'))
                        future.result()
                        published.append(event)

                    st.success(f"Published {n_events} events!")
                    st.json(published[-1])  # Show last event
                else:
                    st.warning("Pub/Sub client not available.")

        with col_sub:
            st.markdown(f'<div style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700; margin-bottom:12px;">Consume Events</div>', unsafe_allow_html=True)

            if st.button("Pull from Subscription"):
                sub = _get_pubsub_subscriber()
                if sub:
                    sub_path = sub.subscription_path(GCP_PROJECT, PUBSUB_SUB)
                    try:
                        response = sub.pull(
                            request={"subscription": sub_path, "max_messages": 10},
                            timeout=5,
                        )
                        if response.received_messages:
                            ack_ids = []
                            events = []
                            for msg in response.received_messages:
                                events.append(json.loads(msg.message.data.decode('utf-8')))
                                ack_ids.append(msg.ack_id)

                            sub.acknowledge(request={"subscription": sub_path, "ack_ids": ack_ids})
                            st.success(f"Consumed {len(events)} events!")
                            st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
                        else:
                            st.info("No messages in queue.")
                    except Exception as e:
                        st.info(f"No messages available or timeout: {str(e)[:100]}")
                else:
                    st.warning("Pub/Sub client not available.")

        # Pipeline flow diagram
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:20px; border:1px solid rgba(83,83,83,0.2);">
                <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700; margin-bottom:12px;">Event Flow</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; font-family:monospace; line-height:2.0; text-align:center;">
                    <span style="color:{COLOR_INFO};">Streaming Client</span>
                    &nbsp;&#8594;&nbsp;
                    <span style="background:rgba(80,155,245,0.15); padding:4px 10px; border-radius:4px; color:{COLOR_INFO};">Pub/Sub Topic</span>
                    &nbsp;&#8594;&nbsp;
                    <span style="background:rgba(29,185,84,0.15); padding:4px 10px; border-radius:4px; color:{SPOTIFY_GREEN};">Dataflow (Enrich)</span>
                    &nbsp;&#8594;&nbsp;
                    <span style="background:rgba(245,155,35,0.15); padding:4px 10px; border-radius:4px; color:{COLOR_WARNING};">ML Model (Score)</span>
                    &nbsp;&#8594;&nbsp;
                    <span style="background:rgba(232,17,91,0.15); padding:4px 10px; border-radius:4px; color:{COLOR_DANGER};">Classify &amp; Route</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================
    # TAB 4: Cloud Storage
    # ============================================
    with tab4:
        st.markdown("### Cloud Storage — Data Lake")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Raw pipeline data stored in Cloud Storage. This is the data lake layer — "
            "raw files that feed into BigQuery for analytical processing."
            "</p>",
            unsafe_allow_html=True,
        )

        gcs = _get_gcs_client()
        if gcs:
            try:
                bucket = gcs.bucket(GCS_BUCKET)
                blobs = list(bucket.list_blobs())

                # Group by prefix
                raw_files = [b for b in blobs if b.name.startswith("raw/")]
                processed_files = [b for b in blobs if b.name.startswith("processed/")]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f'<div style="color:{COLOR_INFO}; font-size:15px; font-weight:700; margin-bottom:10px;">Raw Pipeline Data ({len(raw_files)} files)</div>', unsafe_allow_html=True)
                    for blob in raw_files:
                        name = blob.name.split("/")[-1]
                        size_kb = blob.size / 1024 if blob.size else 0
                        st.markdown(
                            f"""
                            <div style="background:{SPOTIFY_CARD_BG}; border-radius:6px; padding:10px 14px; margin-bottom:6px; border:1px solid rgba(83,83,83,0.15); display:flex; justify-content:space-between; align-items:center;">
                                <span style="color:{SPOTIFY_WHITE}; font-size:13px; font-family:monospace;">{name}</span>
                                <span style="color:{SPOTIFY_GRAY}; font-size:11px;">{size_kb:.1f} KB</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                with col2:
                    st.markdown(f'<div style="color:{SPOTIFY_GREEN}; font-size:15px; font-weight:700; margin-bottom:10px;">Processed Data ({len(processed_files)} files)</div>', unsafe_allow_html=True)
                    for blob in processed_files:
                        name = blob.name.split("/")[-1]
                        size_kb = blob.size / 1024 if blob.size else 0
                        st.markdown(
                            f"""
                            <div style="background:{SPOTIFY_CARD_BG}; border-radius:6px; padding:10px 14px; margin-bottom:6px; border:1px solid rgba(83,83,83,0.15); display:flex; justify-content:space-between; align-items:center;">
                                <span style="color:{SPOTIFY_WHITE}; font-size:13px; font-family:monospace;">{name}</span>
                                <span style="color:{SPOTIFY_GRAY}; font-size:11px;">{size_kb:.1f} KB</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                total_size = sum(b.size for b in blobs if b.size) / (1024 * 1024)
                st.markdown(
                    f"""
                    <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px 20px; border:1px solid rgba(83,83,83,0.2); margin-top:12px;">
                        <span style="color:{SPOTIFY_GRAY}; font-size:12px;">Bucket: </span>
                        <span style="color:{SPOTIFY_WHITE}; font-size:13px; font-family:monospace;">gs://{GCS_BUCKET}</span>
                        <span style="color:{SPOTIFY_GRAY}; font-size:12px; margin-left:16px;">Total: </span>
                        <span style="color:{SPOTIFY_WHITE}; font-size:13px;">{total_size:.1f} MB across {len(blobs)} objects</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.warning(f"Could not list bucket: {e}")
        else:
            st.warning("Cloud Storage client not available.")


def _hex_rgb(hex_color):
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
