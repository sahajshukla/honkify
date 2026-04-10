"""Module: System Architecture — Deployment topology and production vision."""

import streamlit as st
import streamlit.components.v1 as components
from utils.style import (
    SPOTIFY_GREEN, COLOR_DANGER, COLOR_WARNING, COLOR_INFO,
    SPOTIFY_LIGHT_GRAY, SPOTIFY_WHITE, SPOTIFY_CARD_BG, SPOTIFY_GRAY,
)


def _box(title, subtitle, detail, color, icon=""):
    """Generate a styled architecture component box."""
    return f"""
    <div style="background:rgba({_hex_to_rgb(color)},0.12); border:1px solid {color}; border-radius:8px; padding:14px; text-align:center; min-height:90px; display:flex; flex-direction:column; justify-content:center;">
        <div style="color:{color}; font-weight:700; font-size:13px; letter-spacing:0.3px;">{icon} {title}</div>
        <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; margin-top:4px;">{subtitle}</div>
        <div style="color:{SPOTIFY_GRAY}; font-size:10px; margin-top:2px;">{detail}</div>
    </div>
    """


def _hex_to_rgb(hex_color):
    """Convert hex color to RGB string for rgba()."""
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def _arrow_down():
    return f'<div style="text-align:center; color:{SPOTIFY_GRAY}; font-size:20px; margin:6px 0;">&#8595;</div>'


def _arrow_right():
    return f'<span style="color:{SPOTIFY_GRAY}; font-size:20px; margin:0 4px;">&#8594;</span>'


def _build_full_html_page(parts):
    """Wrap HTML parts in a full page with dark background and font."""
    body = "".join(parts)
    return f"""
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        body {{
            font-family: 'Inter', sans-serif;
            background: #121212;
            color: #FFFFFF;
            margin: 0;
            padding: 24px;
        }}
    </style>
    </head>
    <body>
    {body}
    </body>
    </html>
    """


def render():
    st.markdown("## System Architecture")
    st.markdown(
        f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:15px; margin-top:-8px;">'
        "Current deployment topology and production-scale architecture vision, "
        "aligned with Spotify's GCP-native infrastructure."
        "</p>",
        unsafe_allow_html=True,
    )

    # Tab selection
    tab0, tab1, tab2, tab3 = st.tabs([
        "Spotify Stack (Inferred)",
        "Current Deployment",
        "Production Architecture",
        "Kubernetes Manifest",
    ])

    # ==========================================
    # TAB 0: Spotify Stack — Inferred from public information
    # ==========================================
    with tab0:
        st.markdown("### StreamShield's likely architecture inside Spotify")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "An approximate reconstruction of how a fraud-detection pipeline like StreamShield is likely built inside Spotify, "
            "synthesized from public engineering blog posts, talks, the Spotify R&amp;D site, the Backstage open-source project, "
            "and the Apache Beam / Scio history. Every component below is either documented publicly by Spotify or is the "
            "industry-standard GCP service for the role. <strong>This is what enabled the prototype on the right — we built "
            "against the same primitives.</strong>"
            "</p>",
            unsafe_allow_html=True,
        )

        spotify_html = _build_full_html_page([
            # Ingestion
            f'<div style="color:#fff; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px;">1 · Stream Ingestion</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">',
            _box("Mobile / Web / Desktop", "Spotify clients", "play, pause, skip events", COLOR_INFO),
            _box("Cloud Pub/Sub", "Event bus", "100k+ events/sec sustained", SPOTIFY_GREEN),
            _box("Edge Lambda Filters", "Fastly / GCP edge", "geo, abuse pre-filtering", SPOTIFY_GRAY),
            '</div>',
            _arrow_down(),
            # Stream processing
            f'<div style="color:#fff; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px; margin-top:8px;">2 · Stream Processing</div>',
            f'<div style="border:2px dashed {COLOR_INFO}; border-radius:12px; padding:14px;">',
            f'<div style="color:{COLOR_INFO}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; text-align:center;">Apache Beam · Scio (Spotify\'s Scala API) · Cloud Dataflow</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">',
            _box("Sessionization", "Beam stateful DoFn", "groups events into sessions", COLOR_INFO),
            _box("Feature enrichment", "Beam + Bigtable", "account, geo, device joins", COLOR_INFO),
            _box("Fraud scoring call", "Beam → Salem", "RPC into model server", "#AF2896"),
            '</div></div>',
            _arrow_down(),
            # ML platform
            f'<div style="color:#fff; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px; margin-top:8px;">3 · ML Platform — Hendrix</div>',
            f'<div style="border:2px dashed {SPOTIFY_GREEN}; border-radius:12px; padding:14px;">',
            f'<div style="color:{SPOTIFY_GREEN}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; text-align:center;">Hendrix (Spotify ML platform) · Salem (model serving) · Jukebox (feature store) · Kubeflow on GKE</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Salem", "Model serving", "low-latency RPC", SPOTIFY_GREEN),
            _box("Jukebox", "Feature store", "online + offline parity", SPOTIFY_GREEN),
            _box("Kubeflow Pipelines", "Training DAGs", "TFX components", SPOTIFY_GREEN),
            _box("Vertex AI", "Experimentation", "AutoML, custom training", SPOTIFY_GREEN),
            '</div></div>',
            _arrow_down(),
            # Storage
            f'<div style="color:#fff; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px; margin-top:8px;">4 · Storage Layer</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Cloud Bigtable", "Hot serving", "recent events, last 30d", COLOR_WARNING),
            _box("BigQuery", "Analytics warehouse", "petabyte-scale, columnar", SPOTIFY_GREEN),
            _box("Cloud Storage", "Data lake", "Parquet / Avro events archive", COLOR_INFO),
            _box("Cloud SQL", "Operational state", "appeals, dispositions, config", "#AF2896"),
            '</div>',
            _arrow_down(),
            # Consumers
            f'<div style="color:#fff; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px; margin-top:8px;">5 · Consumers</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Fraud Operations", "1st line — analysts", "review queue UI", COLOR_DANGER),
            _box("Internal Audit", "3rd line — IAR", "this dashboard", COLOR_INFO),
            _box("Royalty engine", "Finance", "stream-count reconciliation", COLOR_WARNING),
            _box("Recommendations", "Discovery", "exclude quarantined", "#AF2896"),
            '</div>',
            _arrow_down(),
            # Cross-cutting
            f'<div style="color:#fff; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px; margin-top:8px;">Cross-cutting infrastructure</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Backstage", "Service catalog", "open-sourced by Spotify", SPOTIFY_GRAY),
            _box("GKE Autopilot", "Workload host", "all stateless services", SPOTIFY_GRAY),
            _box("Cloud IAM + IAP", "Identity & access", "least-privilege service accounts", SPOTIFY_GRAY),
            _box("Looker / Mode", "BI surfaces", "executive dashboards", SPOTIFY_GRAY),
            '</div>',
        ])
        components.html(spotify_html, height=1080, scrolling=True)

        # What the prototype actually touches
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown("### What this prototype actually touched on GCP")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "These are the GCP services we provisioned, configured, and exercised end-to-end while building the demo. "
            "Each row maps a real component in this app to the corresponding piece of Spotify\'s likely stack above, so the "
            "claim \"we built against the same primitives\" can be made concretely rather than rhetorically."
            "</p>",
            unsafe_allow_html=True,
        )

        touched = [
            ("Cloud Pub/Sub",
             "USED",
             "topic streamshield-stream-events",
             "Honkify publishes a real JSON-encoded event on every Play click. Maps directly to Spotify\'s ingestion bus.",
             SPOTIFY_GREEN),
            ("BigQuery",
             "USED",
             "dataset streamshield · 5 tables (streaming_events, analyst_reviews, model_performance, appeal_cases, honkify_live_events)",
             "Inserts via streaming insert API (insert_rows_json), reads via tabledata.list (~500ms warm). Maps to Spotify\'s analytics warehouse.",
             SPOTIFY_GREEN),
            ("Cloud IAM · Service Accounts",
             "USED",
             "streamshield-sa@gen-lang-client-... · roles/bigquery.dataEditor + roles/pubsub.publisher",
             "Single least-privilege service account with explicit role bindings. Same pattern Spotify uses for service-to-service auth.",
             SPOTIFY_GREEN),
            ("BigQuery DataFrames API",
             "USED",
             "google-cloud-bigquery + db-dtypes + pandas",
             "Live tabledata.list reads with pandas conversion. Powers the live event ribbon on every demo page.",
             SPOTIFY_GREEN),
            ("Cloud Run",
             "PLANNED",
             "us-central1 · Python 3.12 + Streamlit container",
             "Dockerfile and deploy command ready. Same Knative-on-GKE platform that hosts many internal Spotify tools.",
             COLOR_WARNING),
            ("Cloud Storage",
             "PLANNED",
             "bucket streamshield-audit-data-lake (provisioned)",
             "Bucket created for the workpaper artifact uploads. Not yet wired to the workpaper generator output.",
             COLOR_WARNING),
            ("Cloud Bigtable",
             "NOT TOUCHED",
             "would back the hot serving layer",
             "Out of scope for the audit prototype. Spotify\'s actual StreamShield uses Bigtable for sub-100ms feature lookups.",
             SPOTIFY_GRAY),
            ("Vertex AI / Hendrix",
             "NOT TOUCHED",
             "would back the model training and serving",
             "Out of scope. Salem-equivalent model serving is Spotify-internal; we mock the scoring distribution instead.",
             SPOTIFY_GRAY),
            ("GKE / Kubeflow / Backstage",
             "NOT TOUCHED",
             "Spotify-specific platform layer",
             "Architectural references only — our scale doesn\'t justify GKE. The Production Architecture tab shows where these would fit.",
             SPOTIFY_GRAY),
        ]
        for name, status, detail, note, color in touched:
            badge_color = SPOTIFY_GREEN if status == "USED" else COLOR_WARNING if status == "PLANNED" else SPOTIFY_GRAY
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px 18px; border:1px solid rgba(83,83,83,0.25); border-left:3px solid {color}; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <div style="color:{SPOTIFY_WHITE}; font-size:14px; font-weight:700;">{name}</div>
                        <div style="background:rgba({_hex_to_rgb(badge_color)},0.2); color:{badge_color}; padding:2px 10px; border-radius:500px; font-size:10px; font-weight:800; letter-spacing:0.5px;">{status}</div>
                    </div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; font-family:monospace; margin-top:5px;">{detail}</div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5; margin-top:6px;">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, rgba(80,155,245,0.08), {SPOTIFY_CARD_BG}); border-radius:8px; padding:18px 22px; border-left:4px solid {COLOR_INFO}; margin-top:14px;">
                <div style="color:{COLOR_INFO}; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px;">Disclaimer</div>
                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.6;">
                    This is an outsider\'s reconstruction based on public talks, blog posts (Spotify Engineering, scio.io, backstage.io), and the GCP service catalog.
                    No proprietary Spotify diagrams or internal documents were used. The actual StreamShield system may differ in topology, naming, and component choice. The intent is to show that we understand the problem domain and the platform, not to claim insider knowledge.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================
    # TAB 1: Current Deployment
    # ==========================================
    with tab1:
        st.markdown("### Current Deployment — GCP Cloud Run")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "The prototype is deployed as a containerized Streamlit application on Google Cloud Run — "
            "a serverless platform built on Knative/GKE. This provides auto-scaling, HTTPS, and zero infrastructure management."
            "</p>",
            unsafe_allow_html=True,
        )

        # Use components.html for full HTML rendering (bypasses Streamlit sanitization)
        curr_html = _build_full_html_page([
            f'<div style="text-align:center; margin-bottom:8px;"><span style="color:#fff; font-size:11px; text-transform:uppercase; letter-spacing:2px; background:rgba(83,83,83,0.3); padding:4px 16px; border-radius:4px;">User / Interviewer</span></div>',
            _arrow_down(),
            '<div style="display:grid; grid-template-columns:1fr; gap:12px; max-width:500px; margin:0 auto;">',
            _box("HTTPS Load Balancer", "Google Frontend", "TLS termination, global anycast", COLOR_INFO),
            '</div>',
            _arrow_down(),
            f'<div style="border:2px dashed {SPOTIFY_GREEN}; border-radius:12px; padding:20px; margin:8px 0;">',
            f'<div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px; text-align:center;">Google Cloud Run (Knative on GKE)</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">',
            _box("Docker Container", "Python 3.12 + Streamlit", "Port 8080", SPOTIFY_GREEN),
            _box("Auto-scaling", "0 to N instances", "Scale to zero when idle", SPOTIFY_GREEN),
            '</div>',
            _arrow_down(),
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:4px;">',
            _box("Streamlit App", "app.py", "UI framework", COLOR_INFO),
            _box("9 Audit Modules", "Python + Plotly", "Analysis engine", COLOR_WARNING),
            _box("Synthetic Data", "CSV in container", "50K events", "#AF2896"),
            '</div></div>',
            '<div style="margin-top:16px; display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">',
            _box("Cloud Build", "Dockerfile to Image", "Automated build", SPOTIFY_GRAY),
            _box("Artifact Registry", "Container storage", "us-central1", SPOTIFY_GRAY),
            _box("IAM", "Public access", "allow-unauthenticated", SPOTIFY_GRAY),
            '</div>',
        ])
        components.html(curr_html, height=600, scrolling=True)

        # Deployment specs
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("### Deployment Specifications")

        spec_cols = st.columns(4)
        specs = [
            ("Platform", "GCP Cloud Run", "Serverless containers"),
            ("Region", "us-central1", "Iowa, USA"),
            ("Resources", "1 vCPU / 1 GB RAM", "Auto-scales 0→N"),
            ("Cost", "~$0.00/month", "Pay-per-request, free tier"),
        ]
        for i, (label, value, detail) in enumerate(specs):
            with spec_cols[i]:
                st.markdown(
                    f"""
                    <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px; border:1px solid rgba(83,83,83,0.2);">
                        <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1px;">{label}</div>
                        <div style="color:{SPOTIFY_WHITE}; font-size:18px; font-weight:700; margin-top:4px;">{value}</div>
                        <div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:2px;">{detail}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Tech stack
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("### Technology Stack")

        stack = [
            ("Runtime", "Python 3.12", "Same as Spotify's primary ML language"),
            ("UI Framework", "Streamlit 1.56", "Rapid prototyping, interactive dashboards"),
            ("Visualization", "Plotly 6.x", "Interactive charts, Spotify dark theme"),
            ("Data Processing", "Pandas + NumPy", "Tabular analysis, synthetic data generation"),
            ("ML Metrics", "Scikit-learn + SciPy", "ROC curves, statistical tests, PSI calculation"),
            ("AI Agent", "LLM API", "Audit finding generation (Module 4)"),
            ("Containerization", "Docker", "Reproducible builds, Cloud Run deployment"),
            ("Cloud Platform", "Google Cloud Platform", "Cloud Run + Cloud Build + Artifact Registry"),
            ("CI/CD", "gcloud CLI", "Single-command source-to-deployment"),
        ]

        for i in range(0, len(stack), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(stack):
                    layer, tech, note = stack[i + j]
                    with col:
                        st.markdown(
                            f"""
                            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:14px; border:1px solid rgba(83,83,83,0.2); margin-bottom:8px;">
                                <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:11px; text-transform:uppercase; letter-spacing:1px;">{layer}</div>
                                <div style="color:{SPOTIFY_WHITE}; font-size:15px; font-weight:600; margin-top:4px;">{tech}</div>
                                <div style="color:{SPOTIFY_GRAY}; font-size:11px; margin-top:2px;">{note}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    # ==========================================
    # TAB 2: Production Architecture
    # ==========================================
    with tab2:
        st.markdown("### Production Architecture — Spotify GKE Scale")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "How this tool would be architected at production scale, aligned with Spotify's "
            "GCP-native infrastructure: GKE for orchestration, BigQuery for data, Pub/Sub for events, "
            "and Kubeflow for ML pipeline integration."
            "</p>",
            unsafe_allow_html=True,
        )

        # Use components.html for full rendering
        prod_html = _build_full_html_page([
            # Data Sources
            f'<div style="color:#fff; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px;">Data Sources</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Streaming Events", "Cloud Pub/Sub", "~8M events/sec", COLOR_INFO),
            _box("StreamShield Output", "BigQuery", "Classifications + scores", SPOTIFY_GREEN),
            _box("Analyst Reviews", "Cloud SQL", "Signal card data", COLOR_WARNING),
            _box("Appeal Outcomes", "Cloud SQL", "Content & Rights", "#AF2896"),
            '</div>',
            _arrow_down(),
            # Processing Layer
            f'<div style="color:#fff; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px; margin-top:8px;">Processing Layer</div>',
            f'<div style="border:2px dashed {COLOR_INFO}; border-radius:12px; padding:16px; margin-bottom:12px;">',
            f'<div style="color:{COLOR_INFO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; text-align:center;">Google Kubernetes Engine (GKE Autopilot)</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">',
            _box("Audit Data Pipeline", "Cloud Dataflow (Scio)", "ETL from BigQuery + Pub/Sub", COLOR_INFO),
            _box("Drift Detection Service", "Python microservice", "PSI monitoring, auto-alerts", COLOR_DANGER),
            _box("Bias Analysis Service", "Python microservice", "Per-analyst metrics, challenge cases", COLOR_WARNING),
            '</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:10px;">',
            _box("Threshold Simulator", "Python + Scikit-learn", "What-if analysis engine", SPOTIFY_GREEN),
            _box("AI Audit Agent", "LLM API + LangChain", "Finding generation", "#AF2896"),
            _box("Report Generator", "Python + Jinja2", "Automated audit reports", SPOTIFY_GRAY),
            '</div></div>',
            # Kubernetes Infrastructure
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px; margin-bottom:12px;">',
            _box("Horizontal Pod Autoscaler", "K8s HPA", "CPU/memory-based scaling", SPOTIFY_GRAY),
            _box("Config Maps + Secrets", "K8s native", "Thresholds, API keys", SPOTIFY_GRAY),
            _box("CronJobs", "K8s CronJob", "Scheduled drift checks", SPOTIFY_GRAY),
            _box("Ingress Controller", "GKE Ingress", "HTTPS + IAP auth", SPOTIFY_GRAY),
            '</div>',
            _arrow_down(),
            # Presentation Layer
            f'<div style="color:#fff; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px; margin-top:8px;">Presentation & Integration Layer</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Streamlit Dashboard", "GKE Pod", "IAR analyst interface", SPOTIFY_GREEN),
            _box("Slack / PagerDuty", "Webhook integration", "Drift & bias alerts", COLOR_DANGER),
            _box("GRC Platform", "API integration", "Finding sync, remediation tracking", COLOR_INFO),
            _box("BigQuery Exports", "Scheduled queries", "Downstream analytics", COLOR_WARNING),
            '</div>',
            _arrow_down(),
            # ML Pipeline
            f'<div style="color:#fff; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px; margin-top:8px;">ML Lifecycle Integration</div>',
            f'<div style="border:2px dashed {SPOTIFY_GREEN}; border-radius:12px; padding:16px;">',
            f'<div style="color:{SPOTIFY_GREEN}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; text-align:center;">Kubeflow Pipelines on GKE</div>',
            '<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">',
            _box("Model Registry", "MLflow / Kubeflow", "Version control, lineage", SPOTIFY_GREEN),
            _box("Retraining Pipeline", "TFX + Dataflow", "Triggered by drift alerts", SPOTIFY_GREEN),
            _box("Model Validation", "TFX Evaluator", "Pre-deploy accuracy gates", SPOTIFY_GREEN),
            _box("A/B Testing", "Salem (Spotify)", "Canary deployments", SPOTIFY_GREEN),
            '</div></div>',
        ])
        components.html(prod_html, height=950, scrolling=True)

        # Evolution roadmap
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("### Evolution Roadmap")

        phases = [
            ("Q1: Deploy & Connect", "Current prototype → Cloud Run. Connect to real BigQuery tables via read-only service account. Replace synthetic data with live StreamShield output.", SPOTIFY_GREEN, "NOW"),
            ("Q2: Continuous Monitoring", "Migrate to GKE. Add Kubernetes CronJobs for scheduled drift checks (hourly PSI, daily model metrics). Integrate Slack/PagerDuty alerts. Deploy bias detection as a persistent microservice.", COLOR_INFO, "NEXT"),
            ("Q3: GRC Integration", "API integration with IAR's GRC platform for automated finding creation and remediation tracking. Add SOX control testing automation. Connect to Kubeflow for model lifecycle visibility.", COLOR_WARNING, "PLANNED"),
            ("Q4: Platform Expansion", "Extend to audit other Spotify AI systems (recommendation engine, content moderation, ad targeting). Build reusable audit module framework. Multi-tenant support for different IAR teams.", "#AF2896", "VISION"),
        ]

        for title, desc, color, badge in phases:
            st.markdown(
                f"""
                <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:18px 20px; border:1px solid rgba(83,83,83,0.2); border-left:4px solid {color}; margin-bottom:10px;">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                        <span style="background:rgba({_hex_to_rgb(color)},0.2); color:{color}; padding:2px 10px; border-radius:500px; font-size:10px; font-weight:700; letter-spacing:0.5px;">{badge}</span>
                        <span style="color:{SPOTIFY_WHITE}; font-weight:700; font-size:15px;">{title}</span>
                    </div>
                    <div style="color:{SPOTIFY_LIGHT_GRAY}; font-size:13px; line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ==========================================
    # TAB 3: Kubernetes Manifest
    # ==========================================
    with tab3:
        st.markdown("### Kubernetes Deployment Manifest")
        st.markdown(
            f'<p style="color:{SPOTIFY_LIGHT_GRAY}; font-size:14px;">'
            "Production-ready Kubernetes manifests for deploying the StreamShield Audit Assistant "
            "on GKE, with health checks, autoscaling, resource limits, and scheduled drift monitoring."
            "</p>",
            unsafe_allow_html=True,
        )

        st.code("""# streamshield-audit-deployment.yaml
# Production deployment on GKE (Spotify's container orchestration platform)

apiVersion: apps/v1
kind: Deployment
metadata:
  name: streamshield-audit
  namespace: iar-tools
  labels:
    app: streamshield-audit
    team: internal-audit-risk
    component: audit-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: streamshield-audit
  template:
    metadata:
      labels:
        app: streamshield-audit
        team: internal-audit-risk
    spec:
      containers:
      - name: streamshield-audit
        image: us-central1-docker.pkg.dev/spotify-iar/audit-tools/streamshield-audit:latest
        ports:
        - containerPort: 8080
          protocol: TCP
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        env:
        - name: STREAMLIT_SERVER_PORT
          value: "8080"
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
        - name: STREAMLIT_SERVER_HEADLESS
          value: "true"
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: streamshield-secrets
              key: llm-api-key
        - name: BIGQUERY_PROJECT
          value: "spotify-iar"
        - name: BIGQUERY_DATASET
          value: "streamshield_audit"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 10
          timeoutSeconds: 5
        startupProbe:
          httpGet:
            path: /_stcore/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 30

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: streamshield-audit
  namespace: iar-tools
spec:
  selector:
    app: streamshield-audit
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  type: ClusterIP

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: streamshield-audit-hpa
  namespace: iar-tools
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: streamshield-audit
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

---
# Ingress with Identity-Aware Proxy (IAP) — Spotify internal access only
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: streamshield-audit-ingress
  namespace: iar-tools
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "streamshield-audit-ip"
    networking.gke.io/managed-certificates: "streamshield-audit-cert"
    kubernetes.io/ingress.allow-http: "false"
spec:
  rules:
  - host: streamshield-audit.internal.spotify.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: streamshield-audit
            port:
              number: 80

---
# CronJob: Scheduled Drift Monitoring (runs every 6 hours)
apiVersion: batch/v1
kind: CronJob
metadata:
  name: streamshield-drift-check
  namespace: iar-tools
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: drift-monitor
            image: us-central1-docker.pkg.dev/spotify-iar/audit-tools/streamshield-audit:latest
            command: ["python", "-m", "modules.drift_check_scheduled"]
            env:
            - name: BIGQUERY_PROJECT
              value: "spotify-iar"
            - name: SLACK_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: streamshield-secrets
                  key: slack-webhook-url
            - name: PSI_WARNING_THRESHOLD
              value: "0.10"
            - name: PSI_CRITICAL_THRESHOLD
              value: "0.20"
            resources:
              requests:
                cpu: "250m"
                memory: "256Mi"
              limits:
                cpu: "500m"
                memory: "512Mi"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 5
  failedJobsHistoryLimit: 3

---
# CronJob: Weekly Bias Analysis Report
apiVersion: batch/v1
kind: CronJob
metadata:
  name: streamshield-bias-report
  namespace: iar-tools
spec:
  schedule: "0 8 * * 1"  # Every Monday at 8am
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: bias-reporter
            image: us-central1-docker.pkg.dev/spotify-iar/audit-tools/streamshield-audit:latest
            command: ["python", "-m", "modules.bias_report_scheduled"]
            env:
            - name: BIGQUERY_PROJECT
              value: "spotify-iar"
            - name: SLACK_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: streamshield-secrets
                  key: slack-webhook-url
            resources:
              requests:
                cpu: "250m"
                memory: "256Mi"
          restartPolicy: OnFailure

---
# Secrets (managed via Google Secret Manager)
apiVersion: v1
kind: Secret
metadata:
  name: streamshield-secrets
  namespace: iar-tools
type: Opaque
# Values populated from Google Secret Manager via External Secrets Operator
# - llm-api-key: LLM API key for AI Audit Agent
# - slack-webhook-url: Slack channel for drift/bias alerts

---
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: iar-tools
  labels:
    team: internal-audit-risk
    purpose: audit-tooling
""", language="yaml")

        st.markdown(
            f"""
            <div style="background:{SPOTIFY_CARD_BG}; border-radius:8px; padding:16px 20px; border:1px solid rgba(83,83,83,0.2); margin-top:16px;">
                <div style="color:{SPOTIFY_WHITE}; font-size:14px; line-height:1.6;">
                    <strong style="color:{SPOTIFY_GREEN};">Key Kubernetes features used:</strong><br>
                    <span style="color:{SPOTIFY_LIGHT_GRAY};">
                    <strong>Deployment</strong> with 2 replicas for high availability<br>
                    <strong>HPA</strong> (Horizontal Pod Autoscaler) — scales 1→5 pods based on CPU utilization<br>
                    <strong>Health probes</strong> — liveness, readiness, and startup probes using Streamlit's health endpoint<br>
                    <strong>Ingress + IAP</strong> — Identity-Aware Proxy restricts access to Spotify internal users<br>
                    <strong>CronJobs</strong> — automated drift monitoring every 6 hours, weekly bias reports<br>
                    <strong>Secrets</strong> — API keys managed via Google Secret Manager + External Secrets Operator<br>
                    <strong>Resource limits</strong> — CPU and memory bounds prevent noisy-neighbor issues<br>
                    <strong>Namespace isolation</strong> — <code>iar-tools</code> namespace separates IAR tooling from other workloads
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
