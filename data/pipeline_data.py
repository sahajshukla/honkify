"""
Data Pipeline Generator — Two distinct pipelines with different data granularity.

Pipeline 1: REAL-TIME STREAM EVENTS (what StreamShield sees at classification time)
  - Bare metadata only: user, track, timestamp, device, duration, country
  - No history, no context, no labels
  - Decision must be made with just these signals

Pipeline 2: GROUND TRUTH ASSEMBLY (what IAR uses to evaluate the model)
  - Enriched over time from 6 independent sources
  - Each source contributes different fields at different latencies
  - Final collated dataset has 30+ fields with confidence-weighted labels
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
OUTPUT_DIR = Path(__file__).parent / "cached"


def generate_realtime_events(n=5000, seed=SEED):
    """
    Pipeline 1: Real-time stream events.
    This is ALL that StreamShield has when it must classify a stream.
    Bare metadata — no enrichment, no history, no labels.
    """
    rng = np.random.default_rng(seed + 10)

    dates = pd.date_range("2026-03-25", periods=3, freq="D")
    timestamps = []
    for _ in range(n):
        day = rng.choice(dates)
        hour = rng.integers(0, 24)
        minute = rng.integers(0, 60)
        second = rng.integers(0, 60)
        timestamps.append(day + pd.Timedelta(hours=int(hour), minutes=int(minute), seconds=int(second)))

    devices = ["mobile_ios", "mobile_android", "desktop", "smart_speaker", "web_player"]
    countries = ["US", "GB", "DE", "BR", "MX", "SE", "IN", "JP", "FR", "CO", "NG", "KR"]

    df = pd.DataFrame({
        "event_id": [f"evt_{i:07d}" for i in range(n)],
        "timestamp": sorted(timestamps),
        "user_id": [f"u_{rng.integers(10000, 99999)}" for _ in range(n)],
        "track_id": [f"t_{rng.integers(10000, 99999)}" for _ in range(n)],
        "session_id": [f"s_{rng.integers(100000, 999999)}" for _ in range(n)],
        "duration_ms": rng.integers(5000, 360000, size=n),
        "device_type": rng.choice(devices, size=n),
        "country": rng.choice(countries, size=n),
        "ip_hash": [f"ip_{rng.integers(1000, 9999)}" for _ in range(n)],
        "is_shuffle": rng.choice([True, False], size=n, p=[0.35, 0.65]),
        "is_premium": rng.choice([True, False], size=n, p=[0.55, 0.45]),
    })

    return df


def generate_enrichment_account_features(realtime_df, seed=SEED):
    """
    Enrichment source 1: Account feature store (BigQuery lookup).
    Available at classification time via feature store, but NOT part of the raw event.
    Latency: ~50ms lookup.
    """
    rng = np.random.default_rng(seed + 11)
    unique_users = realtime_df["user_id"].unique()

    records = []
    for uid in unique_users:
        records.append({
            "user_id": uid,
            "account_age_days": int(rng.lognormal(5, 1.5)),
            "profile_completeness_pct": round(rng.beta(3, 1.5) * 100, 1),
            "device_count_lifetime": int(rng.poisson(2.5) + 1),
            "country_count_lifetime": int(rng.poisson(1.2) + 1),
            "total_streams_lifetime": int(rng.lognormal(7, 2)),
            "followers_count": int(rng.lognormal(3, 2.5)),
            "playlists_created": int(rng.poisson(3)),
            "is_family_plan": bool(rng.choice([True, False], p=[0.15, 0.85])),
            "signup_source": rng.choice(["organic", "referral", "campaign", "unknown"], p=[0.5, 0.2, 0.2, 0.1]),
        })

    return pd.DataFrame(records)


def generate_enrichment_track_features(realtime_df, seed=SEED):
    """
    Enrichment source 2: Track/content metadata (BigQuery lookup).
    Available at classification time via content catalog.
    """
    rng = np.random.default_rng(seed + 12)
    unique_tracks = realtime_df["track_id"].unique()

    genres = ["pop", "hip-hop", "rock", "electronic", "ambient", "lo-fi",
              "latin", "classical", "r&b", "country", "regional-folk", "cumbia"]

    records = []
    for tid in unique_tracks:
        is_new = bool(rng.random() < 0.25)
        records.append({
            "track_id": tid,
            "genre": rng.choice(genres),
            "track_duration_ms": int(rng.normal(210000, 60000)),
            "release_date": str(pd.Timestamp("2020-01-01") + pd.Timedelta(days=int(rng.integers(0, 2200)))),
            "artist_id": f"a_{rng.integers(1000, 9999)}",
            "artist_verified": bool(rng.choice([True, False], p=[0.3, 0.7])),
            "artist_monthly_listeners": int(rng.lognormal(8, 3)),
            "distributor_id": f"dist_{rng.integers(100, 999)}",
            "is_new_catalog": is_new,
            "catalog_acquisition_date": "2026-01-29" if is_new else None,
        })

    return pd.DataFrame(records)


def generate_enrichment_network_signals(realtime_df, seed=SEED):
    """
    Enrichment source 3: Network-level signals (Dataflow computation).
    Computed in near-real-time from the event stream.
    Latency: ~5 seconds (streaming aggregation).
    """
    rng = np.random.default_rng(seed + 13)
    unique_ips = realtime_df["ip_hash"].unique()

    records = []
    for ip in unique_ips:
        records.append({
            "ip_hash": ip,
            "accounts_on_ip_24hr": int(rng.lognormal(1.5, 1.5)),
            "streams_from_ip_24hr": int(rng.lognormal(4, 2)),
            "unique_tracks_from_ip_24hr": int(rng.lognormal(3, 1.5)),
            "is_datacenter_ip": bool(rng.choice([True, False], p=[0.08, 0.92])),
            "is_vpn_detected": bool(rng.choice([True, False], p=[0.12, 0.88])),
            "is_proxy_detected": bool(rng.choice([True, False], p=[0.05, 0.95])),
            "geo_country_from_ip": rng.choice(["US", "GB", "DE", "BR", "IN", "NG", "CO", "RU", "CN"]),
            "geo_mismatch": bool(rng.choice([True, False], p=[0.1, 0.9])),
        })

    return pd.DataFrame(records)


def generate_ml_scores(realtime_df, seed=SEED):
    """
    ML Model Output: Fraud probability scores.
    Generated by the StreamShield ML model at classification time.
    This is the ONLY output the production system adds to the raw event.
    """
    rng = np.random.default_rng(seed + 14)
    n = len(realtime_df)

    fraud_scores = rng.beta(1.8, 8, size=n)  # mostly low scores (legitimate)
    # Inject some high scores
    n_suspicious = int(n * 0.08)
    suspicious_idx = rng.choice(n, n_suspicious, replace=False)
    fraud_scores[suspicious_idx] = rng.beta(6, 2, size=n_suspicious)

    classification = np.where(
        fraud_scores > 0.95, "quarantine",
        np.where(fraud_scores > 0.70, "review", "pass")
    )

    return pd.DataFrame({
        "event_id": realtime_df["event_id"],
        "fraud_score": np.round(fraud_scores, 6),
        "classification": classification,
        "model_version": "streamshield-v2.3.1",
        "scoring_latency_ms": rng.integers(5, 45, size=n),
        "top_signal_1": rng.choice(["listening_pattern", "account_age", "geo_anomaly", "network_cluster", "device_fingerprint"], size=n),
        "top_signal_2": rng.choice(["skip_rate", "session_length", "vpn_usage", "ip_cluster", "track_diversity"], size=n),
    })


# ===== GROUND TRUTH SOURCES (assembled AFTER classification) =====

def generate_gt_analyst_decisions(ml_scores_df, seed=SEED):
    """
    Ground truth source 1: Analyst decisions on review-zone cases.
    Latency: hours to 1 day after classification.
    Only exists for review-zone cases (70-95% score).
    """
    rng = np.random.default_rng(seed + 20)
    review_cases = ml_scores_df[ml_scores_df["classification"] == "review"].copy()

    analysts = ["A. Chen", "B. Okafor", "C. Petrov", "D. Johansson",
                "E. Gutierrez", "F. Kim", "G. Sharma", "H. Mueller"]

    records = []
    for _, row in review_cases.iterrows():
        analyst = rng.choice(analysts)
        decision = rng.choice(["quarantine", "monitor", "clear"], p=[0.25, 0.35, 0.40])
        records.append({
            "event_id": row["event_id"],
            "analyst_name": analyst,
            "analyst_decision": decision,
            "review_timestamp": str(pd.Timestamp("2026-03-26") + pd.Timedelta(hours=int(rng.integers(2, 48)))),
            "time_to_decision_sec": int(rng.normal(150, 80)),
            "signals_flagged": int(rng.integers(1, 9)),
            "confidence_level": rng.choice(["high", "medium", "low"], p=[0.4, 0.45, 0.15]),
            "is_fraud_label": decision == "quarantine",
            "label_source": "analyst_decision",
            "label_confidence": round(rng.uniform(0.70, 0.92), 3),
        })

    return pd.DataFrame(records)


def generate_gt_heuristic_flags(realtime_df, seed=SEED):
    """
    Ground truth source 2: Heuristic rule-based flags.
    Latency: real-time (computed alongside ML scoring).
    High confidence for clear-cut cases.
    """
    rng = np.random.default_rng(seed + 21)
    n = len(realtime_df)

    # ~2% of events get heuristic flags
    flagged_idx = rng.choice(n, int(n * 0.02), replace=False)

    records = []
    rules = [
        ("same_ip_burst", "50+ accounts from same IP in 1 hour", 0.95),
        ("duration_anomaly", "All streams exactly 31 seconds", 0.90),
        ("sequential_tracks", "Tracks played in alphabetical order", 0.88),
        ("24hr_nonstop", "Continuous streaming 24+ hours no pause", 0.93),
        ("new_account_burst", "Account created < 1hr ago, 100+ streams", 0.92),
    ]

    for idx in flagged_idx:
        rule = rules[rng.integers(0, len(rules))]
        records.append({
            "event_id": realtime_df.iloc[idx]["event_id"],
            "rule_name": rule[0],
            "rule_description": rule[1],
            "rule_confidence": rule[2],
            "triggered_at": str(realtime_df.iloc[idx]["timestamp"]),
            "is_fraud_label": True,
            "label_source": "heuristic_rule",
            "label_confidence": round(rule[2] + rng.uniform(-0.03, 0.03), 3),
        })

    return pd.DataFrame(records)


def generate_gt_behavioral_decay(realtime_df, seed=SEED):
    """
    Ground truth source 3: Behavioral decay analysis.
    Latency: 30-90 days retrospective.
    Accounts that go silent after intense streaming = probable bots.
    """
    rng = np.random.default_rng(seed + 22)
    unique_users = realtime_df["user_id"].unique()

    # ~5% of accounts show decay pattern
    n_decay = int(len(unique_users) * 0.05)
    decay_users = rng.choice(unique_users, n_decay, replace=False)

    records = []
    for uid in decay_users:
        active_days = int(rng.integers(3, 21))
        silent_days = int(rng.integers(30, 90))
        records.append({
            "user_id": uid,
            "active_period_days": active_days,
            "silent_period_days": silent_days,
            "streams_during_active": int(rng.lognormal(7, 1.5)),
            "streams_during_silent": 0,
            "analysis_date": str(pd.Timestamp("2026-03-28") + pd.Timedelta(days=int(rng.integers(30, 90)))),
            "decay_classification": "probable_bot" if silent_days > 45 else "uncertain",
            "is_fraud_label": silent_days > 45,
            "label_source": "behavioral_decay",
            "label_confidence": round(min(0.55 + (silent_days / 200), 0.85), 3),
        })

    return pd.DataFrame(records)


def generate_gt_appeal_outcomes(ml_scores_df, seed=SEED):
    """
    Ground truth source 4: Appeal outcomes.
    Latency: weeks (avg 29 days).
    Overturned appeals = strong legitimate signal. Upheld = confirmed fraud.
    """
    rng = np.random.default_rng(seed + 23)
    quarantined = ml_scores_df[ml_scores_df["classification"] == "quarantine"]

    # ~15% of quarantined streams get appealed
    n_appeals = int(len(quarantined) * 0.15)
    appealed = quarantined.sample(n=min(n_appeals, len(quarantined)), random_state=seed)

    records = []
    for _, row in appealed.iterrows():
        outcome = rng.choice(["overturned", "upheld", "partial"], p=[0.40, 0.40, 0.20])
        days = int(rng.normal(29, 12))
        records.append({
            "event_id": row["event_id"],
            "appeal_filed_date": str(pd.Timestamp("2026-03-27") + pd.Timedelta(days=int(rng.integers(1, 14)))),
            "appeal_resolved_date": str(pd.Timestamp("2026-03-27") + pd.Timedelta(days=max(7, days))),
            "appeal_outcome": outcome,
            "reviewed_by": rng.choice(["Content & Rights Team", "Senior Fraud Analyst", "Legal Review"]),
            "is_fraud_label": outcome == "upheld",
            "label_source": "appeal_outcome",
            "label_confidence": 0.95 if outcome in ("overturned", "upheld") else 0.75,
        })

    return pd.DataFrame(records)


def generate_gt_confirmed_takedowns(realtime_df, seed=SEED):
    """
    Ground truth source 5: Confirmed fraud takedowns.
    Latency: months (investigations take time).
    Highest confidence labels — confirmed by investigation or law enforcement.
    """
    rng = np.random.default_rng(seed + 24)

    # Simulate 3 confirmed fraud operations affecting a small subset of events
    operations = [
        {"name": "Operation BotSwarm", "n_accounts": 12, "n_events": 45, "method": "Bot farm with residential proxies"},
        {"name": "Operation GhostStream", "n_accounts": 8, "n_events": 30, "method": "Compromised accounts streaming AI-generated ambient"},
        {"name": "Operation LoopHole", "n_accounts": 5, "n_events": 20, "method": "Low-and-slow streaming via cloud VMs"},
    ]

    records = []
    used_events = set()
    for op in operations:
        available = [i for i in range(len(realtime_df)) if i not in used_events]
        selected = rng.choice(available, min(op["n_events"], len(available)), replace=False)
        used_events.update(selected)

        for idx in selected:
            records.append({
                "event_id": realtime_df.iloc[idx]["event_id"],
                "operation_name": op["name"],
                "investigation_method": op["method"],
                "accounts_involved": op["n_accounts"],
                "confirmed_date": str(pd.Timestamp("2026-04-01") + pd.Timedelta(days=int(rng.integers(1, 60)))),
                "confirmed_by": rng.choice(["Trust & Safety", "Law Enforcement Referral", "Fraud Investigation Unit"]),
                "is_fraud_label": True,
                "label_source": "confirmed_takedown",
                "label_confidence": 0.99,
            })

    return pd.DataFrame(records)


def generate_gt_distributor_flags(realtime_df, seed=SEED):
    """
    Ground truth source 6: Distributor-level flags.
    Latency: months (pattern emerges over time).
    Distributors with repeated violations get flagged; all their content gets risk-elevated.
    """
    rng = np.random.default_rng(seed + 25)

    # 3 flagged distributors
    flagged_dists = ["dist_117", "dist_342", "dist_891"]

    records = []
    for dist_id in flagged_dists:
        records.append({
            "distributor_id": dist_id,
            "flag_reason": rng.choice(["Repeated artificial streaming", "Multiple takedowns", "Penalty threshold exceeded"]),
            "prior_violations": int(rng.integers(3, 12)),
            "total_penalty_eur": round(rng.uniform(500, 5000), 2),
            "flag_date": str(pd.Timestamp("2026-02-15") + pd.Timedelta(days=int(rng.integers(0, 30)))),
            "status": rng.choice(["warned", "penalized", "suspended"]),
            "label_source": "distributor_flag",
            "label_confidence": round(rng.uniform(0.75, 0.90), 3),
        })

    return pd.DataFrame(records)


def generate_collated_ground_truth(
    realtime_df, ml_scores_df, analyst_df, heuristic_df,
    behavioral_df, appeal_df, takedown_df
):
    """
    COLLATED GROUND TRUTH: Merges all sources into a single labeled dataset.
    This is what IAR uses to evaluate model performance.
    Each event gets the highest-confidence label from any source that has assessed it.
    """
    # Start with all events
    collated = realtime_df[["event_id"]].copy()
    collated = collated.merge(ml_scores_df[["event_id", "fraud_score", "classification"]], on="event_id", how="left")

    # Collect all labels
    all_labels = []

    for source_df in [analyst_df, heuristic_df, appeal_df, takedown_df]:
        if len(source_df) > 0 and "event_id" in source_df.columns:
            labels = source_df[["event_id", "is_fraud_label", "label_source", "label_confidence"]].copy()
            all_labels.append(labels)

    # For behavioral decay, join via user_id
    if len(behavioral_df) > 0:
        user_events = realtime_df[["event_id", "user_id"]].merge(
            behavioral_df[["user_id", "is_fraud_label", "label_source", "label_confidence"]],
            on="user_id", how="inner"
        )
        if len(user_events) > 0:
            all_labels.append(user_events[["event_id", "is_fraud_label", "label_source", "label_confidence"]])

    if all_labels:
        labels_combined = pd.concat(all_labels, ignore_index=True)

        # For each event, take the highest-confidence label
        best_labels = labels_combined.sort_values("label_confidence", ascending=False).drop_duplicates("event_id", keep="first")

        collated = collated.merge(
            best_labels[["event_id", "is_fraud_label", "label_source", "label_confidence"]],
            on="event_id", how="left"
        )

        # Count how many sources contributed
        source_counts = labels_combined.groupby("event_id")["label_source"].nunique().reset_index()
        source_counts.columns = ["event_id", "n_label_sources"]
        collated = collated.merge(source_counts, on="event_id", how="left")
    else:
        collated["is_fraud_label"] = None
        collated["label_source"] = None
        collated["label_confidence"] = None
        collated["n_label_sources"] = 0

    collated["n_label_sources"] = collated["n_label_sources"].fillna(0).astype(int)
    collated["has_ground_truth"] = collated["label_source"].notna()

    return collated


def generate_pipeline_data():
    """Generate all pipeline datasets."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pipeline_dir = OUTPUT_DIR / "pipelines"
    pipeline_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("PIPELINE 1: REAL-TIME STREAM EVENTS")
    print("=" * 60)

    print("\n1a. Raw stream events (what arrives from Pub/Sub)...")
    realtime = generate_realtime_events()
    realtime.to_csv(pipeline_dir / "p1_raw_stream_events.csv", index=False)
    print(f"    -> {len(realtime)} events | {len(realtime.columns)} columns")
    print(f"    Columns: {list(realtime.columns)}")

    print("\n1b. Account feature enrichment (BigQuery feature store lookup)...")
    accounts = generate_enrichment_account_features(realtime)
    accounts.to_csv(pipeline_dir / "p1_account_features.csv", index=False)
    print(f"    -> {len(accounts)} unique users | {len(accounts.columns)} columns")

    print("\n1c. Track/content metadata (content catalog lookup)...")
    tracks = generate_enrichment_track_features(realtime)
    tracks.to_csv(pipeline_dir / "p1_track_features.csv", index=False)
    print(f"    -> {len(tracks)} unique tracks | {len(tracks.columns)} columns")

    print("\n1d. Network-level signals (Dataflow streaming aggregation)...")
    network = generate_enrichment_network_signals(realtime)
    network.to_csv(pipeline_dir / "p1_network_signals.csv", index=False)
    print(f"    -> {len(network)} unique IPs | {len(network.columns)} columns")

    print("\n1e. ML model scores (StreamShield classification output)...")
    ml_scores = generate_ml_scores(realtime)
    ml_scores.to_csv(pipeline_dir / "p1_ml_scores.csv", index=False)
    print(f"    -> {len(ml_scores)} scored events | {len(ml_scores.columns)} columns")
    print(f"    Quarantine: {(ml_scores['classification'] == 'quarantine').sum()}")
    print(f"    Review: {(ml_scores['classification'] == 'review').sum()}")
    print(f"    Pass: {(ml_scores['classification'] == 'pass').sum()}")

    print("\n" + "=" * 60)
    print("PIPELINE 2: GROUND TRUTH ASSEMBLY (RETROSPECTIVE)")
    print("=" * 60)

    print("\n2a. Analyst decisions (hours to 1 day latency)...")
    gt_analyst = generate_gt_analyst_decisions(ml_scores)
    gt_analyst.to_csv(pipeline_dir / "p2_gt_analyst_decisions.csv", index=False)
    print(f"    -> {len(gt_analyst)} review-zone decisions | {len(gt_analyst.columns)} columns")

    print("\n2b. Heuristic rule flags (real-time)...")
    gt_heuristic = generate_gt_heuristic_flags(realtime)
    gt_heuristic.to_csv(pipeline_dir / "p2_gt_heuristic_flags.csv", index=False)
    print(f"    -> {len(gt_heuristic)} flagged events | {len(gt_heuristic.columns)} columns")

    print("\n2c. Behavioral decay analysis (30-90 day retrospective)...")
    gt_behavioral = generate_gt_behavioral_decay(realtime)
    gt_behavioral.to_csv(pipeline_dir / "p2_gt_behavioral_decay.csv", index=False)
    print(f"    -> {len(gt_behavioral)} decay accounts | {len(gt_behavioral.columns)} columns")

    print("\n2d. Appeal outcomes (weeks latency)...")
    gt_appeals = generate_gt_appeal_outcomes(ml_scores)
    gt_appeals.to_csv(pipeline_dir / "p2_gt_appeal_outcomes.csv", index=False)
    print(f"    -> {len(gt_appeals)} appeal decisions | {len(gt_appeals.columns)} columns")

    print("\n2e. Confirmed takedowns (months latency)...")
    gt_takedowns = generate_gt_confirmed_takedowns(realtime)
    gt_takedowns.to_csv(pipeline_dir / "p2_gt_confirmed_takedowns.csv", index=False)
    print(f"    -> {len(gt_takedowns)} confirmed fraud events | {len(gt_takedowns.columns)} columns")

    print("\n2f. Distributor flags (months latency)...")
    gt_distributors = generate_gt_distributor_flags(realtime)
    gt_distributors.to_csv(pipeline_dir / "p2_gt_distributor_flags.csv", index=False)
    print(f"    -> {len(gt_distributors)} flagged distributors | {len(gt_distributors.columns)} columns")

    print("\n" + "=" * 60)
    print("COLLATED GROUND TRUTH DATASET")
    print("=" * 60)

    collated = generate_collated_ground_truth(
        realtime, ml_scores, gt_analyst, gt_heuristic,
        gt_behavioral, gt_appeals, gt_takedowns
    )
    collated.to_csv(pipeline_dir / "p2_collated_ground_truth.csv", index=False)

    has_gt = collated["has_ground_truth"].sum()
    print(f"\n    -> {len(collated)} total events")
    print(f"    -> {has_gt} events with ground truth ({has_gt/len(collated):.1%})")
    print(f"    -> {len(collated) - has_gt} events without ground truth ({(len(collated)-has_gt)/len(collated):.1%})")

    if has_gt > 0:
        by_source = collated[collated["has_ground_truth"]].groupby("label_source").size()
        print(f"\n    Labels by source:")
        for source, count in by_source.items():
            print(f"      {source}: {count}")

        multi = (collated["n_label_sources"] > 1).sum()
        print(f"\n    Multi-source labels: {multi} events")

    print("\n" + "=" * 60)
    print(f"All pipeline data saved to: {pipeline_dir}")
    print(f"Total files: {len(list(pipeline_dir.glob('*.csv')))}")
    print("=" * 60)

    return {
        "realtime": realtime,
        "accounts": accounts,
        "tracks": tracks,
        "network": network,
        "ml_scores": ml_scores,
        "gt_analyst": gt_analyst,
        "gt_heuristic": gt_heuristic,
        "gt_behavioral": gt_behavioral,
        "gt_appeals": gt_appeals,
        "gt_takedowns": gt_takedowns,
        "gt_distributors": gt_distributors,
        "collated": collated,
    }


if __name__ == "__main__":
    generate_pipeline_data()
