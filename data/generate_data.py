"""
Synthetic data generator for StreamShield Audit Assistant.
Generates realistic data with embedded audit-relevant patterns:
  - Model drift after catalog acquisition (day 120)
  - Automation bias signals in analyst reviews
  - False positive clusters (viral campaigns)
  - Appeal process inequities
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
OUTPUT_DIR = Path(__file__).parent / "cached"


def generate_streaming_events(n=50000, seed=SEED):
    """Generate streaming events with fraud scores and ground truth labels."""
    rng = np.random.default_rng(seed)

    # Time: 180 days of data
    days = 180
    dates = pd.date_range("2025-10-01", periods=days, freq="D")
    event_dates = rng.choice(dates, size=n)
    event_dates = pd.to_datetime(event_dates)

    # Day index for each event (for drift modeling)
    day_idx = ((event_dates - dates[0]).days).values

    # Users and tracks
    n_users = 8000
    n_tracks = 5000
    user_ids = [f"user_{i:05d}" for i in range(n_users)]
    track_ids = [f"track_{i:05d}" for i in range(n_tracks)]
    artist_ids = [f"artist_{i:04d}" for i in range(600)]

    # Artist sizes
    artist_size_map = {}
    for a in artist_ids:
        r = rng.random()
        artist_size_map[a] = "major" if r < 0.1 else "mid" if r < 0.35 else "indie"

    # Genres — new catalog acquisition is heavy on latin, classical, and regional genres
    genres = ["pop", "hip-hop", "rock", "electronic", "ambient", "lo-fi", "latin", "classical", "r&b", "country", "regional-folk", "cumbia"]
    genre_weights = [0.18, 0.16, 0.11, 0.09, 0.07, 0.06, 0.08, 0.04, 0.07, 0.04, 0.05, 0.05]
    # Genres that the new catalog brought in heavily
    new_catalog_genres = {"latin", "classical", "regional-folk", "cumbia"}

    devices = ["mobile_ios", "mobile_android", "desktop", "smart_speaker", "web_player", "tv"]
    device_weights = [0.35, 0.25, 0.2, 0.1, 0.07, 0.03]

    countries = ["US", "GB", "DE", "BR", "MX", "SE", "IN", "JP", "FR", "AU", "NG", "KR"]
    country_weights = [0.3, 0.1, 0.08, 0.08, 0.06, 0.05, 0.08, 0.05, 0.06, 0.04, 0.05, 0.05]

    # Generate base fields
    selected_users = rng.choice(user_ids, size=n)
    selected_tracks = rng.choice(track_ids, size=n)
    selected_artists = rng.choice(artist_ids, size=n)
    selected_genres = rng.choice(genres, size=n, p=genre_weights)
    selected_devices = rng.choice(devices, size=n, p=device_weights)
    selected_countries = rng.choice(countries, size=n, p=country_weights)

    # Duration: legitimate streams 30-300s, fraudulent tend to be shorter
    durations = rng.normal(150, 60, size=n).clip(10, 600).astype(int)

    # Catalog acquisition flag (tracks added after day 120)
    # New catalog content is heavily weighted toward latin, classical, regional-folk, cumbia
    is_new_catalog = rng.random(n) < np.where(day_idx >= 120, 0.35, 0.05)
    # Override genres for new catalog content — they come from the acquired catalog's genres
    for i in range(n):
        if is_new_catalog[i] and day_idx[i] >= 120:
            if rng.random() < 0.6:  # 60% of new catalog is in acquired genres
                selected_genres[i] = rng.choice(["latin", "classical", "regional-folk", "cumbia"])

    # Ground truth fraud: ~7% of streams are actually fraudulent
    # New catalog content has LOWER actual fraud rate (it's legitimate content being misclassified)
    is_fraudulent = np.zeros(n, dtype=bool)
    for i in range(n):
        if is_new_catalog[i]:
            is_fraudulent[i] = rng.random() < 0.03  # only 3% fraud in new catalog (mostly legit)
        else:
            is_fraudulent[i] = rng.random() < 0.07  # 7% fraud in existing content

    # Fraudulent streams have different characteristics
    durations = np.where(is_fraudulent, rng.normal(35, 15, n).clip(10, 120).astype(int), durations)
    # New catalog legitimate content has different duration patterns (longer folk songs, shorter classical pieces)
    for i in range(n):
        if is_new_catalog[i] and not is_fraudulent[i]:
            if selected_genres[i] in ("regional-folk", "cumbia"):
                durations[i] = int(rng.normal(200, 80))  # longer folk songs
            elif selected_genres[i] == "classical":
                durations[i] = int(rng.normal(280, 120))  # longer classical pieces
    durations = np.clip(durations, 10, 600)

    # Fraud score generation with drift
    # Pre-acquisition (day < 120): model is well-calibrated
    # Post-acquisition (day >= 120): model degrades, more false positives
    fraud_scores = np.zeros(n)

    for i in range(n):
        if is_fraudulent[i]:
            # True fraud: model should score high
            if day_idx[i] < 120:
                fraud_scores[i] = rng.beta(8, 1.5)  # high scores, well-calibrated
            else:
                # Post-drift: some fraud slips through (lower scores)
                fraud_scores[i] = rng.beta(6, 2)  # slightly lower, more false negatives
        else:
            # Legitimate: model should score low
            if day_idx[i] < 120:
                fraud_scores[i] = rng.beta(1.5, 10)  # low scores, well-calibrated
            else:
                # Post-drift: more false positives, especially for new catalog
                if is_new_catalog[i] and selected_genres[i] in new_catalog_genres:
                    # New catalog + acquired genre = highest false positive risk
                    # Model sees new accounts, regional concentration, unfamiliar durations
                    fraud_scores[i] = rng.beta(3.0, 4.5)  # significantly elevated scores
                elif is_new_catalog[i]:
                    fraud_scores[i] = rng.beta(2.5, 5)  # elevated for other new catalog
                elif selected_genres[i] in ("ambient", "lo-fi"):
                    fraud_scores[i] = rng.beta(2.2, 6)  # ambient/lo-fi gets flagged more
                else:
                    fraud_scores[i] = rng.beta(1.8, 8)  # slight increase for all

    fraud_scores = fraud_scores.clip(0.01, 0.99)

    # Classification based on thresholds
    classification = np.where(
        fraud_scores > 0.95, "quarantine",
        np.where(fraud_scores > 0.70, "review", "pass")
    )

    # Viral campaign cluster: 80 streams from 5 indie artists, days 135-145, scored 85-94%, all legitimate
    viral_mask = (day_idx >= 135) & (day_idx <= 145) & (~is_fraudulent)
    viral_candidates = np.where(viral_mask)[0]
    viral_count = min(80, len(viral_candidates))
    viral_indices = rng.choice(viral_candidates, viral_count, replace=False) if viral_count > 0 else np.array([], dtype=int)
    if len(viral_indices) > 0:
        fraud_scores[viral_indices] = rng.uniform(0.85, 0.94, len(viral_indices))
        classification[viral_indices] = "review"
        selected_artists[viral_indices] = rng.choice(["artist_0501", "artist_0502", "artist_0503", "artist_0504", "artist_0505"], len(viral_indices))
        for a in ["artist_0501", "artist_0502", "artist_0503", "artist_0504", "artist_0505"]:
            artist_size_map[a] = "indie"

    artist_sizes = [artist_size_map[a] for a in selected_artists]

    ip_subnets = [f"10.{rng.integers(1, 255)}.{rng.integers(1, 255)}" for _ in range(n)]

    df = pd.DataFrame({
        "stream_id": [f"str_{i:06d}" for i in range(n)],
        "user_id": selected_users,
        "track_id": selected_tracks,
        "artist_id": selected_artists,
        "timestamp": event_dates,
        "duration_sec": durations,
        "device_type": selected_devices,
        "country": selected_countries,
        "ip_subnet": ip_subnets,
        "genre": selected_genres,
        "artist_size": artist_sizes,
        "is_new_catalog": is_new_catalog,
        "fraud_score": np.round(fraud_scores, 4),
        "classification": classification,
        "is_actually_fraudulent": is_fraudulent,
    })

    return df.sort_values("timestamp").reset_index(drop=True)


def generate_analyst_reviews(n_days=18, cases_per_day=200, seed=SEED):
    """Generate analyst review data with automation bias patterns."""
    rng = np.random.default_rng(seed + 1)

    analysts = {
        "analyst_A": {"bias_rate": 0.98, "avg_time": 65, "name": "A. Chen"},
        "analyst_B": {"bias_rate": 0.97, "avg_time": 72, "name": "B. Okafor"},
        "analyst_C": {"bias_rate": 0.975, "avg_time": 80, "name": "C. Petrov"},
        "analyst_D": {"bias_rate": 0.90, "avg_time": 180, "name": "D. Johansson"},
        "analyst_E": {"bias_rate": 0.84, "avg_time": 240, "name": "E. Gutierrez"},
        "analyst_F": {"bias_rate": 0.91, "avg_time": 155, "name": "F. Kim"},
        "analyst_G": {"bias_rate": 0.88, "avg_time": 200, "name": "G. Sharma"},
        "analyst_H": {"bias_rate": 0.93, "avg_time": 130, "name": "H. Mueller"},
    }

    records = []
    dates = pd.date_range("2026-03-15", periods=n_days, freq="B")  # business days

    actions = ["quarantine", "monitor", "clear"]
    action_weights = [0.25, 0.35, 0.40]

    case_counter = 0
    for date in dates:
        daily_cases = cases_per_day + rng.integers(-20, 20)
        for _ in range(daily_cases):
            analyst_id = rng.choice(list(analysts.keys()))
            profile = analysts[analyst_id]

            # LLM recommendation
            llm_rec = rng.choice(actions, p=action_weights)

            # Analyst decision: biased analysts agree more
            if rng.random() < profile["bias_rate"]:
                analyst_dec = llm_rec  # agrees with LLM
            else:
                # Independent decision
                other_actions = [a for a in actions if a != llm_rec]
                analyst_dec = rng.choice(other_actions)

            # Time to decision: biased analysts are faster
            base_time = profile["avg_time"]
            time_sec = max(20, int(rng.normal(base_time, base_time * 0.3)))

            # Hour of day affects time (afternoon = faster = more fatigued)
            hour = rng.integers(9, 18)
            if hour >= 15:
                time_sec = int(time_sec * 0.8)  # afternoon fatigue = faster/less careful

            fraud_score = round(rng.uniform(0.70, 0.95), 4)

            records.append({
                "case_id": f"case_{case_counter:05d}",
                "analyst_id": analyst_id,
                "analyst_name": profile["name"],
                "review_date": date,
                "review_hour": hour,
                "fraud_score": fraud_score,
                "llm_recommendation": llm_rec,
                "analyst_decision": analyst_dec,
                "agreed_with_llm": llm_rec == analyst_dec,
                "time_to_decision_sec": time_sec,
            })
            case_counter += 1

    return pd.DataFrame(records)


def generate_model_performance(n_days=180, seed=SEED):
    """Generate daily model performance metrics showing drift after day 120."""
    rng = np.random.default_rng(seed + 2)
    dates = pd.date_range("2025-10-01", periods=n_days, freq="D")

    records = []
    for i, date in enumerate(dates):
        if i < 120:
            # Pre-acquisition: stable, good performance
            precision = 0.94 + rng.normal(0, 0.008)
            recall = 0.91 + rng.normal(0, 0.010)
            fpr = 0.028 + rng.normal(0, 0.004)
            fnr = 0.09 + rng.normal(0, 0.010)
            psi = 0.02 + abs(rng.normal(0, 0.008))
        else:
            # Post-acquisition: gradual degradation
            decay = (i - 120) / 60  # 0 to 1 over 60 days
            decay = min(decay, 1.0)

            precision = 0.94 - (0.12 * decay) + rng.normal(0, 0.012)
            recall = 0.91 - (0.06 * decay) + rng.normal(0, 0.015)
            fpr = 0.028 + (0.055 * decay) + rng.normal(0, 0.006)
            fnr = 0.09 + (0.06 * decay) + rng.normal(0, 0.012)
            psi = 0.02 + (0.18 * decay) + abs(rng.normal(0, 0.015))

        precision = np.clip(precision, 0.5, 1.0)
        recall = np.clip(recall, 0.5, 1.0)
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = np.clip(fpr, 0.005, 0.15)
        fnr = np.clip(fnr, 0.02, 0.25)
        psi = np.clip(psi, 0.0, 0.5)

        total_streams = int(rng.normal(18_000_000, 1_500_000))
        quarantine_pct = 0.03 + (0.015 * (decay if i >= 120 else 0))
        review_pct = 0.05 + (0.008 * (decay if i >= 120 else 0))

        records.append({
            "date": date,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "psi_score": round(psi, 4),
            "total_streams": total_streams,
            "quarantine_count": int(total_streams * quarantine_pct),
            "review_count": int(total_streams * review_pct),
            "pass_count": int(total_streams * (1 - quarantine_pct - review_pct)),
        })

    return pd.DataFrame(records)


def generate_appeal_cases(n=200, seed=SEED):
    """Generate appeal cases showing process inequities."""
    rng = np.random.default_rng(seed + 3)
    dates = pd.date_range("2025-10-15", periods=150, freq="D")

    records = []
    for i in range(n):
        artist_type = rng.choice(["major", "mid", "indie"], p=[0.15, 0.30, 0.55])

        appeal_date = rng.choice(dates)

        # Resolution time depends on artist type (inequity pattern)
        if artist_type == "major":
            days_to_resolve = max(5, int(rng.normal(12, 4)))
        elif artist_type == "mid":
            days_to_resolve = max(8, int(rng.normal(25, 8)))
        else:
            days_to_resolve = max(12, int(rng.normal(38, 12)))

        resolution_date = appeal_date + pd.Timedelta(days=days_to_resolve)

        # Outcome: major labels more likely to win appeals
        if artist_type == "major":
            outcome = rng.choice(["overturned", "upheld", "partial"], p=[0.55, 0.25, 0.20])
        elif artist_type == "mid":
            outcome = rng.choice(["overturned", "upheld", "partial"], p=[0.40, 0.40, 0.20])
        else:
            outcome = rng.choice(["overturned", "upheld", "partial"], p=[0.35, 0.45, 0.20])

        original_score = round(rng.uniform(0.70, 0.99), 4)
        original_class = "quarantine" if original_score > 0.95 else "review"

        # Estimated royalties at stake
        streams_affected = int(rng.lognormal(10, 1.5))
        royalties_at_stake = round(streams_affected * rng.uniform(0.003, 0.005), 2)

        records.append({
            "appeal_id": f"appeal_{i:04d}",
            "artist_id": f"artist_{rng.integers(0, 600):04d}",
            "artist_type": artist_type,
            "original_fraud_score": original_score,
            "original_classification": original_class,
            "appeal_date": appeal_date,
            "resolution_date": resolution_date,
            "days_to_resolve": days_to_resolve,
            "outcome": outcome,
            "streams_affected": streams_affected,
            "estimated_royalties_usd": royalties_at_stake,
        })

    return pd.DataFrame(records)


def generate_all():
    """Generate all datasets and save to CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating streaming events (50K records)...")
    events = generate_streaming_events()

    # Save FULL audit dataset (with ground truth — what IAR uses to evaluate)
    events.to_csv(OUTPUT_DIR / "streaming_events.csv", index=False)

    # Save PRODUCTION dataset (no ground truth — what StreamShield sees in real-time)
    production_cols = [c for c in events.columns if c != "is_actually_fraudulent"]
    events[production_cols].to_csv(OUTPUT_DIR / "streaming_events_production.csv", index=False)

    print(f"  -> {len(events)} events | {events['is_actually_fraudulent'].mean():.1%} fraud rate (audit view)")
    print(f"  -> Production view: {len(production_cols)} columns (no ground truth)")
    print(f"     Quarantined: {(events['classification'] == 'quarantine').mean():.1%}")
    print(f"     Review: {(events['classification'] == 'review').mean():.1%}")
    print(f"     Pass: {(events['classification'] == 'pass').mean():.1%}")

    print("\nGenerating analyst reviews (~3.6K records)...")
    reviews = generate_analyst_reviews()
    reviews.to_csv(OUTPUT_DIR / "analyst_reviews.csv", index=False)
    agreement = reviews["agreed_with_llm"].mean()
    print(f"  -> {len(reviews)} reviews | Overall agreement rate: {agreement:.1%}")

    print("\nGenerating model performance (180 days)...")
    perf = generate_model_performance()
    perf.to_csv(OUTPUT_DIR / "model_performance.csv", index=False)
    pre = perf[perf["date"] < "2026-01-29"]
    post = perf[perf["date"] >= "2026-01-29"]
    print(f"  -> Pre-acquisition avg precision: {pre['precision'].mean():.3f}")
    print(f"  -> Post-acquisition avg precision: {post['precision'].mean():.3f}")

    print("\nGenerating appeal cases (200 records)...")
    appeals = generate_appeal_cases()
    appeals.to_csv(OUTPUT_DIR / "appeal_cases.csv", index=False)
    print(f"  -> {len(appeals)} appeals | Avg resolution: {appeals['days_to_resolve'].mean():.0f} days")
    for at in ["major", "mid", "indie"]:
        subset = appeals[appeals["artist_type"] == at]
        print(f"     {at}: avg {subset['days_to_resolve'].mean():.0f} days, overturn rate {(subset['outcome'] == 'overturned').mean():.0%}")

    print("\nAll datasets generated successfully.")
    return events, reviews, perf, appeals


if __name__ == "__main__":
    generate_all()
