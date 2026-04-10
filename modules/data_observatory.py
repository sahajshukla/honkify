"""Data Observatory — Production vs Ground Truth pipelines, live GCP connections, data lineage."""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import json
import time
from pathlib import Path
from utils.style import (
    apply_spotify_style, SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING,
    COLOR_INFO, SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG,
    SPOTIFY_GRAY, metric_card,
)
from utils.data_loader import GCP_PROJECT, load_pipeline_data

PUBSUB_TOPIC = "streamshield-stream-events"
PUBSUB_SUB = "streamshield-stream-sub"
GCS_BUCKET = "streamshield-audit-data-lake"
BQ_DATASET = "streamshield"


def render(events_df, reviews_df, appeals_df):
    st.markdown("## Data Observatory")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Live connections to GCP backends, dual pipeline comparison, and ground truth lineage. "
        "The production system sees 11 fields. The audit system assembles 30+ fields from 6 sources. 86% of streams are never validated."
        "</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Live GCP Connections", "Pipeline Comparison", "Ground Truth Sources", "Pub/Sub Stream"])

    # ============================================
    # TAB 1: Live GCP Connections
    # ============================================
    with tab1:
        st.markdown("### GCP Backend Status")

        # Check connections
        services = []

        try:
            from google.cloud import bigquery
            bq = bigquery.Client(project=GCP_PROJECT)
            tables = list(bq.list_tables(f"{GCP_PROJECT}.{BQ_DATASET}"))
            services.append(("BigQuery", f"{len(tables)} tables in {BQ_DATASET}", True, "Data warehouse — ground truth, ML scores, analyst reviews"))
        except Exception:
            services.append(("BigQuery", "Not connected", False, "Data warehouse"))

        try:
            from google.cloud import pubsub_v1
            pub = pubsub_v1.PublisherClient()
            topic_path = pub.topic_path(GCP_PROJECT, PUBSUB_TOPIC)
            pub.get_topic(request={"topic": topic_path})
            services.append(("Cloud Pub/Sub", f"Topic: {PUBSUB_TOPIC}", True, "Streaming — real-time event ingestion"))
        except Exception:
            services.append(("Cloud Pub/Sub", "Not connected", False, "Streaming events"))

        try:
            from google.cloud import storage
            gcs = storage.Client(project=GCP_PROJECT)
            bucket = gcs.bucket(GCS_BUCKET)
            blobs = list(bucket.list_blobs(max_results=5))
            all_blobs = list(bucket.list_blobs())
            services.append(("Cloud Storage", f"{len(all_blobs)} objects in gs://{GCS_BUCKET}", True, "Data lake — raw CSVs, pipeline outputs"))
        except Exception:
            services.append(("Cloud Storage", "Not connected", False, "Data lake"))

        for name, detail, connected, desc in services:
            color = SPOTIFY_GREEN if connected else COLOR_DANGER
            status = "CONNECTED" if connected else "UNAVAILABLE"
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {color}; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color:{SPOTIFY_WHITE}; font-size:16px; font-weight:700;">{name}</span>
                            <span style="color:{SPOTIFY_GRAY}; font-size:12px; margin-left:12px;">{detail}</span>
                        </div>
                        <span style="background:rgba(255,255,255,0.06); color:{color}; padding:3px 12px; border-radius:500px; font-size:11px; font-weight:700;">{status}</span>
                    </div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; margin-top:6px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Live BigQuery query
        st.markdown("### Live BigQuery Query")
        preset = st.selectbox("Select query", [
            "Stream classification breakdown",
            "False positive rate by genre (post-acquisition)",
            "Analyst agreement rates",
            "Table sizes",
            "Custom SQL",
        ])

        preset_sql = {
            "Stream classification breakdown": f"SELECT classification, COUNT(*) as count, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events` GROUP BY classification ORDER BY count DESC",
            "False positive rate by genre (post-acquisition)": f"SELECT genre, COUNT(*) as total, SUM(CASE WHEN classification IN ('quarantine', 'review') THEN 1 ELSE 0 END) as flagged, ROUND(SUM(CASE WHEN classification IN ('quarantine', 'review') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as fp_pct FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events` WHERE NOT is_actually_fraudulent AND timestamp >= '2026-01-29' GROUP BY genre HAVING COUNT(*) > 50 ORDER BY fp_pct DESC",
            "Analyst agreement rates": f"SELECT analyst_name, COUNT(*) as reviews, ROUND(AVG(CASE WHEN agreed_with_llm THEN 1 ELSE 0 END) * 100, 1) as agree_pct, ROUND(AVG(time_to_decision_sec), 0) as avg_sec FROM `{GCP_PROJECT}.{BQ_DATASET}.analyst_reviews` GROUP BY analyst_name ORDER BY agree_pct DESC",
            "Table sizes": f"SELECT table_id, row_count, ROUND(size_bytes / 1024, 1) as size_kb FROM `{GCP_PROJECT}.{BQ_DATASET}.__TABLES__` ORDER BY row_count DESC",
        }

        if preset == "Custom SQL":
            sql = st.text_area("SQL", f"SELECT * FROM `{GCP_PROJECT}.{BQ_DATASET}.streaming_events` LIMIT 10", height=100)
        else:
            sql = preset_sql[preset]
            st.code(sql, language="sql")

        if st.button("Run Query", type="primary"):
            try:
                from google.cloud import bigquery
                bq = bigquery.Client(project=GCP_PROJECT)
                start = time.time()
                result = bq.query(sql).to_dataframe()
                elapsed = time.time() - start
                st.markdown(f'<span style="color:{SPOTIFY_GREEN}; font-size:12px;">Completed in {elapsed:.2f}s — {len(result)} rows</span>', unsafe_allow_html=True)
                st.dataframe(result, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Query failed: {e}")

    # ============================================
    # TAB 2: Pipeline Comparison
    # ============================================
    with tab2:
        st.markdown("### Real-Time Pipeline vs. Ground Truth Pipeline")

        pipeline_data = load_pipeline_data()

        comparison_html = """
        <html><head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body { font-family: 'Inter', sans-serif; background: #121212; color: #fff; margin: 0; padding: 16px; }
            table { width: 100%; border-collapse: collapse; font-size: 13px; }
            td { padding: 10px 12px; border-bottom: 1px solid rgba(83,83,83,0.2); }
            .header td { color: #B3B3B3; font-weight: 600; border-bottom: 2px solid #535353; }
            .rt { color: #F59B23; }
            .gt { color: #1DB954; }
        </style>
        </head><body>
        <table>
            <tr class="header"><td></td><td class="rt">Real-Time Pipeline</td><td class="gt">Ground Truth Pipeline</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Purpose</td><td>Classify streams as they happen</td><td>Evaluate if classifications were correct</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Timing</td><td>Under 200ms</td><td>Hours to months (retrospective)</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Fields Available</td><td>~47 fields from 5 enrichment sources</td><td>30+ fields from 6 ground truth sources</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Ground Truth</td><td style="color:#E8115B;font-weight:600;">NOT AVAILABLE</td><td style="color:#1DB954;">Assembled from multiple sources</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Metrics Possible</td><td>Quarantine rate, score distribution, PSI</td><td>Precision, recall, F1, ROC curves</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Self-Evaluation</td><td style="color:#E8115B;">Cannot know if decisions are correct</td><td>Can compare decisions against labels</td></tr>
            <tr><td style="color:#fff;font-weight:600;">Coverage</td><td>100% of streams scored</td><td style="color:#E8115B;font-weight:600;">~14% receive labels. 86% never validated.</td></tr>
            <tr><td style="color:#fff;font-weight:600;">GCP Services</td><td>Pub/Sub, Dataflow, GKE, Feature Store</td><td>BigQuery, Cloud SQL, Kubeflow</td></tr>
        </table>
        </body></html>
        """
        components.html(comparison_html, height=380, scrolling=False)

        # Pipeline stage data previews
        if pipeline_data:
            st.markdown("### Real-Time Pipeline Stages")
            rt_stages = [
                ("p1_raw_stream_events", "Raw Stream Events", "Cloud Pub/Sub", "0ms", COLOR_INFO),
                ("p1_account_features", "Account Features", "BigQuery Feature Store", "~50ms", COLOR_WARNING),
                ("p1_track_features", "Track Metadata", "Content Catalog", "~30ms", SPOTIFY_GREEN),
                ("p1_network_signals", "Network Signals", "Dataflow", "~5s", "#AF2896"),
                ("p1_ml_scores", "ML Classification", "StreamShield GKE", "~15ms", COLOR_DANGER),
            ]
            for key, name, source, latency, color in rt_stages:
                if key in pipeline_data:
                    df = pipeline_data[key]
                    with st.expander(f"{name} — {len(df):,} rows, {len(df.columns)} columns ({source}, {latency})"):
                        st.dataframe(df.head(5), use_container_width=True, hide_index=True)

            st.markdown("### Ground Truth Sources")
            gt_stages = [
                ("p2_gt_heuristic_flags", "Heuristic Rules", "Real-time", "90-95%"),
                ("p2_gt_analyst_decisions", "Analyst Decisions", "Hours", "70-92%"),
                ("p2_gt_appeal_outcomes", "Appeal Outcomes", "Weeks", "75-95%"),
                ("p2_gt_behavioral_decay", "Behavioral Decay", "30-90 days", "55-85%"),
                ("p2_gt_confirmed_takedowns", "Confirmed Takedowns", "Months", "99%"),
                ("p2_gt_distributor_flags", "Distributor Flags", "Months", "75-90%"),
            ]
            for key, name, latency, confidence in gt_stages:
                if key in pipeline_data:
                    df = pipeline_data[key]
                    with st.expander(f"{name} — {len(df):,} rows (Latency: {latency}, Confidence: {confidence})"):
                        st.dataframe(df.head(5), use_container_width=True, hide_index=True)

    # ============================================
    # TAB 3: Ground Truth Sources
    # ============================================
    with tab3:
        st.markdown("### Ground Truth Label Sources")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Ground truth is assembled from 6 independent sources at different latencies and confidence levels."
            "</p>",
            unsafe_allow_html=True,
        )

        sources_html = """
        <html><head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body { font-family: 'Inter', sans-serif; background: #121212; color: #fff; margin: 0; padding: 16px; }
            .source { background: #181818; border-radius: 8px; padding: 16px; margin-bottom: 10px; display: grid; grid-template-columns: auto 1fr auto; gap: 16px; align-items: center; }
            .num { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
            .title { font-weight: 700; font-size: 14px; }
            .desc { color: #B3B3B3; font-size: 12px; margin-top: 4px; }
            .meta { text-align: right; font-size: 11px; color: #B3B3B3; }
            .conf { font-weight: 600; }
        </style>
        </head><body>
        <div class="source" style="border-left: 3px solid #1DB954;">
            <div class="num" style="background: rgba(29,185,84,0.2); color: #1DB954;">1</div>
            <div><div class="title">Confirmed Takedowns</div><div class="desc">Fraud operations confirmed by Trust & Safety investigation or law enforcement. Highest confidence.</div></div>
            <div class="meta"><span class="conf" style="color:#1DB954;">99%</span><br>Months latency</div>
        </div>
        <div class="source" style="border-left: 3px solid #1DB954;">
            <div class="num" style="background: rgba(29,185,84,0.2); color: #1DB954;">2</div>
            <div><div class="title">Heuristic Rules</div><div class="desc">Self-evident fraud: 500 accounts same IP streaming same tracks 24/7. Rule-based, near-certain.</div></div>
            <div class="meta"><span class="conf" style="color:#1DB954;">95%</span><br>Real-time</div>
        </div>
        <div class="source" style="border-left: 3px solid #509BF5;">
            <div class="num" style="background: rgba(80,155,245,0.2); color: #509BF5;">3</div>
            <div><div class="title">Appeal Outcomes</div><div class="desc">Overturned = strong legitimate signal. Upheld = confirmed fraud. High confidence for resolved cases.</div></div>
            <div class="meta"><span class="conf" style="color:#509BF5;">95%</span><br>Weeks latency</div>
        </div>
        <div class="source" style="border-left: 3px solid #509BF5;">
            <div class="num" style="background: rgba(80,155,245,0.2); color: #509BF5;">4</div>
            <div><div class="title">Distributor Flags</div><div class="desc">Distributors with repeated violations. All content from flagged distributors gets risk-elevated.</div></div>
            <div class="meta"><span class="conf" style="color:#509BF5;">85%</span><br>Months latency</div>
        </div>
        <div class="source" style="border-left: 3px solid #F59B23;">
            <div class="num" style="background: rgba(245,155,35,0.2); color: #F59B23;">5</div>
            <div><div class="title">Analyst Decisions</div><div class="desc">Human classifications for review-zone cases. Subject to automation bias — quality depends on review thoroughness.</div></div>
            <div class="meta"><span class="conf" style="color:#F59B23;">80%</span><br>Hours latency</div>
        </div>
        <div class="source" style="border-left: 3px solid #F59B23;">
            <div class="num" style="background: rgba(245,155,35,0.2); color: #F59B23;">6</div>
            <div><div class="title">Behavioral Decay</div><div class="desc">Accounts that stream intensely then go permanently silent. Retrospective bot detection.</div></div>
            <div class="meta"><span class="conf" style="color:#F59B23;">70%</span><br>30-90 days</div>
        </div>
        <div style="background: rgba(232,17,91,0.08); border: 1px solid #E8115B; border-radius: 8px; padding: 16px; margin-top: 16px; text-align: center;">
            <div style="color: #E8115B; font-weight: 700; font-size: 14px;">86% of streams are NEVER validated</div>
            <div style="color: #B3B3B3; font-size: 12px; margin-top: 6px;">No source systematically evaluates the 92% of streams that pass through as legitimate.</div>
        </div>
        </body></html>
        """
        components.html(sources_html, height=560, scrolling=False)

    # ============================================
    # TAB 4: Pub/Sub Stream
    # ============================================
    with tab4:
        st.markdown("### Pub/Sub — Real-Time Event Stream")

        col1, col2 = st.columns(2)
        with col1:
            n_events = st.slider("Events to publish", 1, 20, 5)
            if st.button("Publish Events", type="primary"):
                try:
                    from google.cloud import pubsub_v1
                    import random
                    pub = pubsub_v1.PublisherClient()
                    topic_path = pub.topic_path(GCP_PROJECT, PUBSUB_TOPIC)
                    devices = ['mobile_ios', 'mobile_android', 'desktop', 'smart_speaker']
                    countries = ['US', 'GB', 'DE', 'BR', 'IN', 'CO', 'NG']

                    for i in range(n_events):
                        event = {
                            'event_id': f'live_{int(time.time())}_{i}',
                            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'user_id': f'u_{random.randint(10000, 99999)}',
                            'track_id': f't_{random.randint(10000, 99999)}',
                            'duration_ms': random.randint(5000, 300000),
                            'device_type': random.choice(devices),
                            'country': random.choice(countries),
                        }
                        pub.publish(topic_path, json.dumps(event).encode('utf-8')).result()

                    st.success(f"Published {n_events} events to Pub/Sub")
                except Exception as e:
                    st.warning(f"Pub/Sub not available: {str(e)[:100]}")

        with col2:
            if st.button("Pull Events from Subscription"):
                try:
                    from google.cloud import pubsub_v1
                    sub = pubsub_v1.SubscriberClient()
                    sub_path = sub.subscription_path(GCP_PROJECT, PUBSUB_SUB)
                    response = sub.pull(request={"subscription": sub_path, "max_messages": 10}, timeout=5)
                    if response.received_messages:
                        events = []
                        ack_ids = []
                        for msg in response.received_messages:
                            events.append(json.loads(msg.message.data.decode('utf-8')))
                            ack_ids.append(msg.ack_id)
                        sub.acknowledge(request={"subscription": sub_path, "ack_ids": ack_ids})
                        st.success(f"Consumed {len(events)} events")
                        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
                    else:
                        st.info("No messages in queue")
                except Exception as e:
                    st.info(f"No messages or timeout: {str(e)[:100]}")
