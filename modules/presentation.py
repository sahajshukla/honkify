"""Immersive Presentation Mode — Spatial zooming through the StreamShield architecture."""

import streamlit as st
import streamlit.components.v1 as components


def render():
    st.set_page_config(layout="wide") if False else None  # already set in app.py

    # Full-screen immersive presentation using custom HTML/CSS/JS
    components.html(PRESENTATION_HTML, height=720, scrolling=False)


PRESENTATION_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', sans-serif;
    background: #121212;
    color: #FFFFFF;
    overflow: hidden;
    width: 100%;
    height: 100vh;
  }

  .presentation {
    width: 100%;
    height: 100vh;
    position: relative;
    overflow: hidden;
  }

  /* Slide container */
  .slide {
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.6s ease, transform 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    transform: scale(0.9);
    pointer-events: none;
    padding: 40px;
  }

  .slide.active {
    opacity: 1;
    transform: scale(1);
    pointer-events: all;
  }

  .slide.zoom-in {
    transform: scale(1.15);
    opacity: 0;
  }

  .slide.zoom-out {
    transform: scale(0.85);
    opacity: 0;
  }

  /* Slide layouts */
  .slide-content {
    max-width: 1100px;
    width: 100%;
  }

  .slide-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 8px;
    line-height: 1.1;
  }

  .slide-subtitle {
    font-size: 18px;
    color: #B3B3B3;
    margin-bottom: 32px;
    line-height: 1.5;
    max-width: 700px;
  }

  .badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 500px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 16px;
  }
  .badge-critical { background: rgba(232,17,91,0.2); color: #E8115B; }
  .badge-high { background: rgba(255,100,55,0.2); color: #FF6437; }
  .badge-medium { background: rgba(245,155,35,0.2); color: #F59B23; }
  .badge-info { background: rgba(80,155,245,0.2); color: #509BF5; }
  .badge-green { background: rgba(29,185,84,0.2); color: #1DB954; }

  /* Cards grid */
  .cards { display: grid; gap: 16px; }
  .cards-2 { grid-template-columns: 1fr 1fr; }
  .cards-3 { grid-template-columns: 1fr 1fr 1fr; }
  .cards-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
  .cards-5 { grid-template-columns: 1fr 1fr 1fr 1fr 1fr; }

  .card {
    background: #181818;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid rgba(83,83,83,0.25);
    transition: border-color 0.3s;
  }
  .card:hover { border-color: rgba(83,83,83,0.6); }

  .card-title {
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .card-body {
    font-size: 13px;
    color: #B3B3B3;
    line-height: 1.6;
  }

  .card-accent {
    border-left: 3px solid;
  }

  /* Stat boxes */
  .stat-box {
    background: #181818;
    border-radius: 8px;
    padding: 18px 20px;
    border: 1px solid rgba(83,83,83,0.25);
    text-align: center;
  }
  .stat-label {
    font-size: 11px;
    color: #B3B3B3;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 6px;
  }
  .stat-value {
    font-size: 28px;
    font-weight: 800;
  }
  .stat-delta {
    font-size: 13px;
    margin-top: 4px;
  }

  /* Architecture flow */
  .flow {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .flow-node {
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    text-align: center;
  }
  .flow-arrow { color: #535353; font-size: 22px; }

  /* Finding box */
  .finding {
    border-radius: 8px;
    padding: 24px;
    margin-top: 20px;
    border-left: 4px solid;
    background: #181818;
  }
  .finding-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
  }
  .finding-body {
    font-size: 14px;
    color: #B3B3B3;
    line-height: 1.7;
  }

  /* Navigation */
  .nav {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 16px;
    z-index: 100;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(12px);
    padding: 10px 24px;
    border-radius: 500px;
    border: 1px solid rgba(83,83,83,0.3);
  }
  .nav-btn {
    background: none;
    border: 1px solid rgba(83,83,83,0.4);
    color: #B3B3B3;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  .nav-btn:hover { background: #282828; color: #fff; border-color: #535353; }

  .nav-progress {
    font-size: 12px;
    color: #535353;
    min-width: 60px;
    text-align: center;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .nav-dots {
    display: flex;
    gap: 6px;
  }
  .nav-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #535353;
    transition: all 0.3s;
    cursor: pointer;
  }
  .nav-dot.active { background: #1DB954; width: 20px; border-radius: 3px; }

  /* Spotify logo */
  .spotify-logo {
    position: fixed;
    top: 20px;
    left: 24px;
    z-index: 100;
    opacity: 0.4;
  }

  /* Slide number */
  .section-indicator {
    position: fixed;
    top: 20px;
    right: 24px;
    z-index: 100;
    font-size: 11px;
    color: #535353;
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }

  /* Title slide special */
  .title-slide {
    text-align: center;
  }
  .title-slide .slide-title {
    font-size: 56px;
    margin-bottom: 12px;
    background: linear-gradient(135deg, #1DB954, #1ED760);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .title-slide .slide-subtitle {
    font-size: 20px;
    max-width: 100%;
    margin: 0 auto 40px;
  }

  /* Highlight text */
  .hl-green { color: #1DB954; font-weight: 700; }
  .hl-red { color: #E8115B; font-weight: 700; }
  .hl-amber { color: #F59B23; font-weight: 700; }
  .hl-blue { color: #509BF5; font-weight: 700; }
  .hl-white { color: #FFFFFF; font-weight: 700; }

  /* Keyboard hint */
  .key-hint {
    position: fixed;
    bottom: 72px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 11px;
    color: #535353;
    z-index: 100;
    opacity: 0.5;
    transition: opacity 2s;
  }
</style>
</head>
<body>
<div class="presentation" id="presentation">

  <!-- Spotify Logo -->
  <div class="spotify-logo">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="#1DB954">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
    </svg>
  </div>

  <div class="section-indicator" id="sectionIndicator">STREAMSHIELD</div>

  <!-- SLIDE 0: Title -->
  <div class="slide active" data-section="StreamShield">
    <div class="slide-content title-slide">
      <div style="margin-bottom:24px;">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="#1DB954">
          <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
        </svg>
      </div>
      <div class="slide-title">StreamShield</div>
      <div class="slide-subtitle" style="color:#B3B3B3;">IAR Preliminary Assessment</div>
      <div style="color:#535353; font-size:14px;">Internal Audit & Risk</div>
    </div>
  </div>

  <!-- SLIDE 1: System Overview -->
  <div class="slide" data-section="System Overview">
    <div class="slide-content">
      <span class="badge badge-info">CONTEXT</span>
      <div class="slide-title">How StreamShield Works</div>
      <div class="slide-subtitle">A near-real-time AI processing layer between Spotify's streaming pipeline and downstream systems.</div>

      <div class="flow" style="margin-bottom:28px;">
        <div class="flow-node" style="background:rgba(80,155,245,0.15); border:1px solid #509BF5; color:#509BF5;">Pub/Sub<br><span style="font-size:10px;color:#B3B3B3;">8M events/sec</span></div>
        <span class="flow-arrow">&rarr;</span>
        <div class="flow-node" style="background:rgba(245,155,35,0.15); border:1px solid #F59B23; color:#F59B23;">Dataflow<br><span style="font-size:10px;color:#B3B3B3;">Enrich</span></div>
        <span class="flow-arrow">&rarr;</span>
        <div class="flow-node" style="background:rgba(29,185,84,0.15); border:1px solid #1DB954; color:#1DB954;">ML Model<br><span style="font-size:10px;color:#B3B3B3;">Score</span></div>
        <span class="flow-arrow">&rarr;</span>
        <div class="flow-node" style="background:rgba(232,17,91,0.15); border:1px solid #E8115B; color:#E8115B;">&gt;95%<br><span style="font-size:10px;">Quarantine</span></div>
        <div class="flow-node" style="background:rgba(245,155,35,0.15); border:1px solid #F59B23; color:#F59B23;">70-95%<br><span style="font-size:10px;">Review</span></div>
        <div class="flow-node" style="background:rgba(29,185,84,0.15); border:1px solid #1DB954; color:#1DB954;">&lt;70%<br><span style="font-size:10px;">Pass</span></div>
      </div>

      <div class="cards cards-4">
        <div class="stat-box"><div class="stat-label">Streams Processed</div><div class="stat-value" style="color:#1DB954;">Billions</div><div class="stat-delta" style="color:#B3B3B3;">monthly</div></div>
        <div class="stat-box"><div class="stat-label">Auto-Quarantined</div><div class="stat-value" style="color:#E8115B;">3%</div></div>
        <div class="stat-box"><div class="stat-label">Human Review</div><div class="stat-value" style="color:#F59B23;">5%</div></div>
        <div class="stat-box"><div class="stat-label">Fraud Reduction</div><div class="stat-value" style="color:#1DB954;">40%</div><div class="stat-delta" style="color:#1DB954;">vs. prior methods</div></div>
      </div>
    </div>
  </div>

  <!-- SLIDE 2: Model Drift -->
  <div class="slide" data-section="Model Drift">
    <div class="slide-content">
      <span class="badge badge-critical">CRITICAL RISK</span>
      <div class="slide-title">Model Performance Degradation</div>
      <div class="slide-subtitle">The catalog acquisition changed what content looks like. The model didn't update.</div>

      <div class="cards cards-4" style="margin-bottom:24px;">
        <div class="stat-box"><div class="stat-label">Precision Before</div><div class="stat-value" style="color:#1DB954;">94.0%</div></div>
        <div class="stat-box"><div class="stat-label">Precision After</div><div class="stat-value" style="color:#E8115B;">82%</div><div class="stat-delta" style="color:#E8115B;">&darr; 12 points</div></div>
        <div class="stat-box"><div class="stat-label">New Catalog FP Rate</div><div class="stat-value" style="color:#E8115B;">6.6x</div><div class="stat-delta" style="color:#B3B3B3;">vs existing content</div></div>
        <div class="stat-box"><div class="stat-label">PSI Score</div><div class="stat-value" style="color:#E8115B;">&gt;0.20</div><div class="stat-delta" style="color:#E8115B;">CRITICAL</div></div>
      </div>

      <div class="cards cards-2">
        <div class="card card-accent" style="border-left-color:#E8115B;">
          <div class="card-title" style="color:#E8115B;">Why New Catalog Breaks the Model</div>
          <div class="card-body">Folk songs run 200s+ (model expects 120-180s). Regional artists have concentrated fanbases (looks like bot farms). New accounts with minimal profiles (looks like fake accounts). Shared ISP infrastructure (looks like coordinated bots).</div>
        </div>
        <div class="card card-accent" style="border-left-color:#1DB954;">
          <div class="card-title" style="color:#1DB954;">Recommendation</div>
          <div class="card-body">Expedited model retraining within <span class="hl-white">14 days</span>, not next quarter. Implement automated PSI monitoring with alerts. Establish mandatory model evaluation within 7 days of significant platform changes.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 3: Automation Bias -->
  <div class="slide" data-section="Automation Bias">
    <div class="slide-content">
      <span class="badge badge-high">HIGH RISK</span>
      <div class="slide-title">Automation Bias in Human Review</div>
      <div class="slide-subtitle">92% agreement isn't calibration. It's a workflow design problem.</div>

      <div class="cards cards-2" style="margin-bottom:24px;">
        <div class="card" style="border-top:3px solid #E8115B;">
          <div class="card-title" style="color:#E8115B;">High-Bias Analysts (3 of 8)</div>
          <div class="card-body">
            Agreement rate: <span class="hl-red">&gt;97%</span><br>
            Avg review time: <span class="hl-red">&lt;90 seconds</span><br>
            Override rate: <span class="hl-red">&lt;3%</span><br><br>
            These analysts read the LLM summary, see the recommendation, and click approve.
          </div>
        </div>
        <div class="card" style="border-top:3px solid #1DB954;">
          <div class="card-title" style="color:#1DB954;">Independent Analysts (5 of 8)</div>
          <div class="card-body">
            Agreement rate: <span class="hl-green">~85%</span><br>
            Avg review time: <span class="hl-green">3-4 minutes</span><br>
            Override rate: <span class="hl-green">~15%</span><br><br>
            These analysts examine the evidence and form independent judgments.
          </div>
        </div>
      </div>

      <div class="finding" style="border-left-color:#F59B23; background:rgba(245,155,35,0.05);">
        <div class="finding-title" style="color:#F59B23;">Root Cause</div>
        <div class="finding-body">The workflow presents a <span class="hl-white">completed LLM analysis and recommendation</span> before the analyst forms their own view. The analyst reviews a finished product, not raw evidence. 92% agreement is a predictable outcome of this design.</div>
      </div>
    </div>
  </div>

  <!-- SLIDE 4: Signal Card Solution -->
  <div class="slide" data-section="Signal Card">
    <div class="slide-content">
      <span class="badge badge-green">PROPOSED SOLUTION</span>
      <div class="slide-title">Signal Confirmation Card</div>
      <div class="slide-subtitle">Replace narrative-based review with structured signal assessment. Same time, verifiable independence.</div>

      <div style="background:#181818; border-radius:8px; padding:24px; border:1px solid rgba(83,83,83,0.25); font-family:monospace; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(83,83,83,0.3); padding-bottom:12px; margin-bottom:12px;">
          <span style="font-weight:700; font-size:15px;">CASE #12345</span>
          <span style="color:#B3B3B3; font-size:13px;">Score: 87.3%</span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; font-size:13px;">
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Account age: <span class="hl-red">12 days</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Devices: <span class="hl-red">1</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Duration: <span class="hl-green">185s</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Tracks/day: <span class="hl-red">589</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Skip rate: <span class="hl-red">4%</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">VPN: <span class="hl-red">Yes</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Locations: <span class="hl-red">8 countries</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Same-IP: <span class="hl-red">47 accounts</span></div>
          <div style="padding:8px; background:#0a0a0a; border-radius:4px;">Signals: <span class="hl-red">7/8</span></div>
        </div>
        <div style="margin-top:14px; color:#535353; font-size:12px; font-style:italic;">AI recommendation revealed AFTER analyst submits their decision</div>
      </div>

      <div class="cards cards-3">
        <div class="stat-box"><div class="stat-label">Time per Case</div><div class="stat-value" style="color:#1DB954;font-size:22px;">60-90s</div><div class="stat-delta" style="color:#B3B3B3;">Zero free text</div></div>
        <div class="stat-box"><div class="stat-label">At 200 Cases/Day</div><div class="stat-value" style="color:#1DB954;font-size:22px;">~3.5 hrs</div><div class="stat-delta" style="color:#B3B3B3;">Comparable to current</div></div>
        <div class="stat-box"><div class="stat-label">Output</div><div class="stat-value" style="color:#1DB954;font-size:22px;">Structured</div><div class="stat-delta" style="color:#B3B3B3;">Auto-analyzable audit trail</div></div>
      </div>
    </div>
  </div>

  <!-- SLIDE 5: Ground Truth Gap -->
  <div class="slide" data-section="Ground Truth">
    <div class="slide-content">
      <span class="badge badge-critical">CRITICAL INSIGHT</span>
      <div class="slide-title" style="font-size:38px;">86% of Streams Are Never Validated</div>
      <div class="slide-subtitle">The production system classifies every stream but cannot know if its decisions are correct.</div>

      <div class="cards cards-2" style="margin-bottom:20px;">
        <div class="card card-accent" style="border-left-color:#F59B23;">
          <div class="card-title" style="color:#F59B23;">Pipeline 1: Real-Time (under 200ms)</div>
          <div class="card-body">11 raw fields &rarr; enriched to 47 fields &rarr; ML score &rarr; decision.<br><br><span class="hl-red">No ground truth available at classification time.</span> The system cannot self-evaluate.</div>
        </div>
        <div class="card card-accent" style="border-left-color:#1DB954;">
          <div class="card-title" style="color:#1DB954;">Pipeline 2: Ground Truth (hours to months)</div>
          <div class="card-body">6 independent sources contribute labels retrospectively:<br>Heuristic rules (95%), Analyst decisions (80%), Appeals (95%), Behavioral decay (70%), Confirmed takedowns (99%), Distributor flags (85%)</div>
        </div>
      </div>

      <div class="finding" style="border-left-color:#E8115B; background:rgba(232,17,91,0.05);">
        <div class="finding-title" style="color:#E8115B;">The Gap</div>
        <div class="finding-body">Only <span class="hl-white">14%</span> of streams receive any label. No source systematically validates the <span class="hl-white">92% of streams that pass through as legitimate</span>. If the model is missing fraud in that population, there is no feedback signal to detect it.</div>
      </div>
    </div>
  </div>

  <!-- SLIDE 6: Catalog Onboarding -->
  <div class="slide" data-section="Catalog Protocol">
    <div class="slide-content">
      <span class="badge badge-green">PROPOSED SOLUTION</span>
      <div class="slide-title">Catalog Onboarding Protocol</div>
      <div class="slide-subtitle">Adjust the system when new content arrives. Err toward leniency with compensating controls.</div>

      <div class="cards cards-3" style="margin-bottom:20px;">
        <div class="card card-accent" style="border-left-color:#509BF5;">
          <div class="card-title" style="color:#509BF5;">Grace Period (90 days)</div>
          <div class="card-body">Raise auto-quarantine threshold from 95% to 98% for new catalog content. Default to monitoring with provisional royalties for review-zone cases.</div>
        </div>
        <div class="card card-accent" style="border-left-color:#F59B23;">
          <div class="card-title" style="color:#F59B23;">Error Asymmetry</div>
          <div class="card-body">A false positive directly harms a legitimate artist. A false negative is a small, recoverable royalty leakage spread across the pool. The default should reflect this.</div>
        </div>
        <div class="card card-accent" style="border-left-color:#1DB954;">
          <div class="card-title" style="color:#1DB954;">Compensating Controls</div>
          <div class="card-body">Network-level fraud intelligence still catches coordinated operations. Distributor penalties (&#8364;10/track) create deterrence. Retroactive clawback recovers royalties.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 7: Defense in Depth -->
  <div class="slide" data-section="Defense in Depth">
    <div class="slide-content">
      <span class="badge badge-info">FRAMEWORK</span>
      <div class="slide-title">Defense in Depth</div>
      <div class="slide-subtitle">No single control solves fraud. Five layers compensate for each other's weaknesses.</div>

      <div class="cards cards-5">
        <div class="card" style="border-top:3px solid #1DB954; text-align:center;">
          <div style="color:#535353; font-size:10px; letter-spacing:1px; margin-bottom:6px;">LAYER 1</div>
          <div class="card-title" style="color:#1DB954;">ML Model</div>
          <div class="card-body">Real-time per-stream scoring</div>
          <div style="color:#535353; font-size:11px; margin-top:8px;">Real-time</div>
        </div>
        <div class="card" style="border-top:3px solid #509BF5; text-align:center;">
          <div style="color:#535353; font-size:10px; letter-spacing:1px; margin-bottom:6px;">LAYER 2</div>
          <div class="card-title" style="color:#509BF5;">Human Review</div>
          <div class="card-body">Signal confirmation card</div>
          <div style="color:#535353; font-size:11px; margin-top:8px;">Hours</div>
        </div>
        <div class="card" style="border-top:3px solid #F59B23; text-align:center;">
          <div style="color:#535353; font-size:10px; letter-spacing:1px; margin-bottom:6px;">LAYER 3</div>
          <div class="card-title" style="color:#F59B23;">Network Analysis</div>
          <div class="card-body">Entity-level patterns</div>
          <div style="color:#535353; font-size:11px; margin-top:8px;">Days</div>
        </div>
        <div class="card" style="border-top:3px solid #AF2896; text-align:center;">
          <div style="color:#535353; font-size:10px; letter-spacing:1px; margin-bottom:6px;">LAYER 4</div>
          <div class="card-title" style="color:#AF2896;">Distributor</div>
          <div class="card-body">Accountability + penalties</div>
          <div style="color:#535353; font-size:11px; margin-top:8px;">Months</div>
        </div>
        <div class="card" style="border-top:3px solid #E8115B; text-align:center;">
          <div style="color:#535353; font-size:10px; letter-spacing:1px; margin-bottom:6px;">LAYER 5</div>
          <div class="card-title" style="color:#E8115B;">Clawback</div>
          <div class="card-body">Retroactive recovery</div>
          <div style="color:#535353; font-size:11px; margin-top:8px;">Retroactive</div>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 8: Engagement Plan -->
  <div class="slide" data-section="Engagement Plan">
    <div class="slide-content">
      <span class="badge badge-info">DELIVERABLE 3</span>
      <div class="slide-title">IAR Engagement Plan</div>
      <div class="slide-subtitle">Combined advisory + assurance engagement. 8 weeks, 3 phases.</div>

      <div class="cards cards-3">
        <div class="card card-accent" style="border-left-color:#509BF5;">
          <div class="card-title" style="color:#509BF5;">Phase 1: Planning (Weeks 1-2)</div>
          <div class="card-body">Stakeholder interviews: Head of Fraud, ML Engineering, Analysts, Content & Rights, Finance, Ads, Legal<br><br>Document processes, gather model documentation, analyst data, appeal logs, LLM outputs</div>
        </div>
        <div class="card card-accent" style="border-left-color:#1DB954;">
          <div class="card-title" style="color:#1DB954;">Phase 2: Testing (Weeks 3-6)</div>
          <div class="card-body">Model drift analysis &bull; Threshold sensitivity &bull; Automation bias (challenge cases) &bull; LLM output quality sampling &bull; False positive analysis by genre &bull; Appeal process review &bull; Downstream data integrity &bull; Change management</div>
        </div>
        <div class="card card-accent" style="border-left-color:#F59B23;">
          <div class="card-title" style="color:#F59B23;">Phase 3: Reporting (Weeks 7-8)</div>
          <div class="card-body">Draft findings with risk ratings<br>Validate with Fraud team<br>Present to leadership<br>Coordinate with external auditors on SOX<br>Track remediation commitments</div>
        </div>
      </div>

      <div class="finding" style="border-left-color:#E8115B; background:rgba(232,17,91,0.05); margin-top:16px;">
        <div class="finding-body"><span class="hl-red">Urgent:</span> Model retraining should not wait for the engagement to complete. That is an active risk getting worse daily.</div>
      </div>
    </div>
  </div>

  <!-- SLIDE 9: Prototype -->
  <div class="slide" data-section="Prototype">
    <div class="slide-content">
      <span class="badge badge-green">DELIVERABLE 4</span>
      <div class="slide-title">StreamShield Audit Assistant</div>
      <div class="slide-subtitle">Working prototype deployed on GCP Cloud Run. Reads from live BigQuery, Pub/Sub, and Cloud Storage.</div>

      <div class="cards cards-3" style="margin-bottom:20px;">
        <div class="card" style="border-top:3px solid #1DB954;"><div class="card-title" style="color:#1DB954;">Drift Monitor</div><div class="card-body">Precision/recall trends, PSI tracking, catalog impact analysis (6.6x false flag rate)</div></div>
        <div class="card" style="border-top:3px solid #509BF5;"><div class="card-title" style="color:#509BF5;">Threshold Analyzer</div><div class="card-body">Interactive sliders, ROC curves, confusion matrix, financial impact</div></div>
        <div class="card" style="border-top:3px solid #F59B23;"><div class="card-title" style="color:#F59B23;">Bias Detector</div><div class="card-body">Per-analyst patterns, time distribution, signal card mockup</div></div>
        <div class="card" style="border-top:3px solid #FF6437;"><div class="card-title" style="color:#FF6437;">Data Pipelines</div><div class="card-body">Real-time vs ground truth flows, 14% coverage gap</div></div>
        <div class="card" style="border-top:3px solid #AF2896;"><div class="card-title" style="color:#AF2896;">AI Audit Agent</div><div class="card-body">Generates structured findings from data. Risk heatmap.</div></div>
        <div class="card" style="border-top:3px solid #E8115B;"><div class="card-title" style="color:#E8115B;">Live Infrastructure</div><div class="card-body">BigQuery queries, Pub/Sub events, GCS data lake — all real GCP backends</div></div>
      </div>

      <div style="text-align:center; padding:16px; background:#181818; border-radius:8px; border:1px solid rgba(83,83,83,0.25);">
        <span style="color:#B3B3B3; font-size:14px;">Live at </span>
        <span style="color:#1DB954; font-size:14px; font-weight:700;">streamshield-audit-811557100247.us-central1.run.app</span>
      </div>
    </div>
  </div>

  <!-- SLIDE 10: Close -->
  <div class="slide" data-section="Summary">
    <div class="slide-content title-slide">
      <div class="slide-title" style="font-size:36px; margin-bottom:24px;">Priority Recommendations</div>

      <div style="text-align:left; max-width:700px; margin:0 auto;">
        <div style="display:flex; align-items:baseline; gap:14px; margin-bottom:18px;">
          <span class="badge badge-critical" style="min-width:30px; text-align:center;">1</span>
          <span style="font-size:16px; color:#FFFFFF;">Expedited model retraining within <span class="hl-green">14 days</span></span>
        </div>
        <div style="display:flex; align-items:baseline; gap:14px; margin-bottom:18px;">
          <span class="badge badge-critical" style="min-width:30px; text-align:center;">2</span>
          <span style="font-size:16px; color:#FFFFFF;">Catalog onboarding protocol with grace periods and adjusted thresholds</span>
        </div>
        <div style="display:flex; align-items:baseline; gap:14px; margin-bottom:18px;">
          <span class="badge badge-high" style="min-width:30px; text-align:center;">3</span>
          <span style="font-size:16px; color:#FFFFFF;">Replace narrative review with signal confirmation card</span>
        </div>
        <div style="display:flex; align-items:baseline; gap:14px; margin-bottom:18px;">
          <span class="badge badge-high" style="min-width:30px; text-align:center;">4</span>
          <span style="font-size:16px; color:#FFFFFF;">Bring classification thresholds into the SOX control framework</span>
        </div>
        <div style="display:flex; align-items:baseline; gap:14px; margin-bottom:18px;">
          <span class="badge badge-medium" style="min-width:30px; text-align:center;">5</span>
          <span style="font-size:16px; color:#FFFFFF;">Expand ground truth coverage with systematic validation of passed streams</span>
        </div>
      </div>

      <div style="margin-top:40px; color:#535353; font-size:15px;">
        StreamShield is delivering value. It needs governance to match its impact.
      </div>
    </div>
  </div>

</div>

<!-- Navigation -->
<div class="nav">
  <button class="nav-btn" onclick="prevSlide()">&#8592;</button>
  <div class="nav-dots" id="navDots"></div>
  <button class="nav-btn" onclick="nextSlide()">&#8594;</button>
  <div class="nav-progress" id="navProgress">1 / 11</div>
</div>

<div class="key-hint" id="keyHint">Press &larr; &rarr; arrow keys to navigate</div>

<script>
  const slides = document.querySelectorAll('.slide');
  const navDots = document.getElementById('navDots');
  const navProgress = document.getElementById('navProgress');
  const sectionIndicator = document.getElementById('sectionIndicator');
  const keyHint = document.getElementById('keyHint');
  let current = 0;

  // Create dots
  slides.forEach((_, i) => {
    const dot = document.createElement('div');
    dot.className = 'nav-dot' + (i === 0 ? ' active' : '');
    dot.onclick = () => goToSlide(i);
    navDots.appendChild(dot);
  });

  function updateNav() {
    document.querySelectorAll('.nav-dot').forEach((d, i) => {
      d.className = 'nav-dot' + (i === current ? ' active' : '');
    });
    navProgress.textContent = (current + 1) + ' / ' + slides.length;
    sectionIndicator.textContent = slides[current].dataset.section || '';
  }

  function goToSlide(n) {
    if (n === current || n < 0 || n >= slides.length) return;
    const direction = n > current ? 'zoom-in' : 'zoom-out';
    slides[current].className = 'slide ' + direction;
    current = n;
    slides[current].className = 'slide active';
    updateNav();
  }

  function nextSlide() { goToSlide(current + 1); }
  function prevSlide() { goToSlide(current - 1); }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); nextSlide(); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); prevSlide(); }
    keyHint.style.opacity = '0';
  });

  // Hide hint after 5 seconds
  setTimeout(() => { keyHint.style.opacity = '0'; }, 5000);
</script>
</body>
</html>
"""
