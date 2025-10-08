# app.py
import json
import time
import tempfile
from pathlib import Path

import streamlit as st
from dummy_processor import run_pipeline  # same dummy backend

# ---------------------------------------------------------
# Page setup (must be first Streamlit call on the page)
# ---------------------------------------------------------
st.set_page_config(
    page_title="YBrantWorks • Conversation Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)  # [web:36]

# ---------------------------------------------------------
# Theming helpers and CSS
# ---------------------------------------------------------
THEME_PRIMARY = "#dc2626"  # Tailwind red-600 vibe
APP_CSS = f"""
<style>
/* App background: layered deep-red gradient + subtle grid + film grain */
[data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1200px 700px at -10% -20%, rgba(239,68,68,0.18), transparent 55%),
    radial-gradient(900px 550px at 110% 10%, rgba(220,38,38,0.16), transparent 60%),
    radial-gradient(1000px 600px at 50% 120%, rgba(127,29,29,0.16), transparent 60%),
    linear-gradient(180deg, #0b0b10 0%, #0a0a0a 60%, #08080a 100%);
}}

[data-testid="stAppViewContainer"]::before {{
  content: "";
  position: fixed;
  inset: 0;
  background:
    repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 40px),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 40px);
  pointer-events: none;
  mask-image: radial-gradient(ellipse at center, rgba(0,0,0,0.6) 0%, rgba(0,0,0,1) 70%);
}}

[data-testid="stAppViewContainer"]::after {{
  content: "";
  position: fixed;
  inset: 0;
  background: url('data:image/svg+xml;utf8,\
  <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">\
  <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/></filter>\
  <rect width="100%" height="100%" filter="url(%23n)" opacity="0.025"/></svg>') repeat;
  pointer-events: none;
}}

.hide-chrome [data-testid="stToolbar"] {{ display: none !important; }}
.hide-chrome [data-testid="stDecoration"] {{ display: none !important; }}
.hide-chrome [data-testid="stStatusWidget"] {{ display: none !important; }}

/* Header / hero */
.navbar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 0.5rem 0.75rem 0.25rem; border-bottom: 1px solid rgba(255,255,255,0.06);
}}
.brand {{
  display: flex; align-items: center; gap: 0.65rem; color: #fff;
  font-weight: 700; letter-spacing: 0.3px; font-size: 1.05rem;
}}
.brand img {{ height: 28px; border-radius: 6px; }}
.cta-row {{ display: flex; gap: 0.65rem; }}

.btn {{
  background: linear-gradient(180deg, {THEME_PRIMARY}, #b91c1c);
  color: #fff; border: 1px solid rgba(255,255,255,0.14);
  padding: 0.6rem 1rem; border-radius: 10px; font-weight: 700;
  box-shadow: 0 6px 24px rgba(220,38,38,0.25);
}}
.btn.secondary {{
  background: linear-gradient(180deg, #111827, #0f172a);
  color: #e5e7eb; border: 1px solid rgba(255,255,255,0.08);
}}

.hero {{
  padding: 1.25rem 0 0.25rem 0;
}}
.hero h1 {{
  margin: 0; font-size: 2.3rem; line-height: 1.1; color: #f9fafb;
}}
.hero p {{
  margin: 0.35rem 0 1rem 0; color: #e5e7eb; opacity: 0.85;
}}

/* “Glass” cards and stepper */
.card {{
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 1rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  backdrop-filter: blur(10px);
}}

.stepper {{
  display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.75rem;
}}
.step {{
  padding: 0.3rem 0.6rem; border-radius: 999px; font-size: 0.85rem; color:#e5e7eb;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
}}
.step.active {{ background: {THEME_PRIMARY}; color: #fff; border-color: rgba(255,255,255,0.18); }}

.small-muted {{ color:#e5e7eb; opacity:0.7; font-size:0.9rem; }}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)  # [web:37]

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
def _init_state():
    for k, v in {
        "step": "landing",
        "audio_file": None,
        "license_file": None,
        "audio_path": None,
        "license_path": None,
        "result_obj": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()  # [web:36]

def _save_temp(uploaded_file, suffix: str) -> Path:
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush(); tmp.close()
    return Path(tmp.name)  # [web:2]

def _stepper():
    # The proper stages in order:
    stages = ["landing", "audio", "license", "ready", "processing", "result"]
    labels = ["Upload audio", "License key", "Explore", "Result"]

    try:
        # Map current step to an index (1-based for steps after landing)
        idx = max(1, min(4, stages.index(st.session_state.step)))
    except ValueError:
        idx = 1  # fallback to first step

    chips = []
    for i, lbl in enumerate(labels, 1):
        cls = "step active" if i <= idx else "step"
        chips.append(f'<div class="{cls}">{i}. {lbl}</div>')
    st.markdown(f'<div class="stepper">{"".join(chips)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# Header / Hero
# ---------------------------------------------------------
col_logo, col_cta = st.columns([0.7, 0.3])
with col_logo:
    st.markdown('<div class="navbar">', unsafe_allow_html=True)  # [web:37]
    left, right = st.columns([0.8, 0.2])
    with left:
        st.markdown('<div class="brand">', unsafe_allow_html=True)  # [web:37]
        st.image("assets/logo.png", use_container_width=False)  # [attached_image:2]
        st.markdown("</div>", unsafe_allow_html=True)  # [web:37]
    with right:
        st.image("assets/icon.png", use_container_width=False)  # [attached_image:1]
    st.markdown("</div>", unsafe_allow_html=True)  # [web:37]

with col_logo:
    st.markdown('<div class="hero">', unsafe_allow_html=True)  # [web:37]
    st.markdown("<h1>Conversation insights, instantly</h1>", unsafe_allow_html=True)  # [attached_file:3]
    st.markdown('<p class="small-muted">Upload a call, apply your license, then explore real‑time outputs — all on a polished red theme.</p>', unsafe_allow_html=True)  # [web:22]
    st.markdown("</div>", unsafe_allow_html=True)  # [web:37]

with col_cta:
    st.markdown('<div class="cta-row">', unsafe_allow_html=True)  # [web:37]
    if st.session_state.step == "landing":
        if st.button("Get started", type="primary"):
            st.session_state.step = "audio"
    st.markdown("</div>", unsafe_allow_html=True)  # [web:37]

st.markdown("<hr style='border-color:rgba(255,255,255,0.08)'>", unsafe_allow_html=True)  # [web:37]
_stepper()  # [web:37]

# ---------------------------------------------------------
# Flow
# ---------------------------------------------------------
if st.session_state.step == "landing":
    st.markdown('<div class="card">Welcome — click “Get started” to begin.</div>', unsafe_allow_html=True)  # [web:37]

elif st.session_state.step == "audio":
    with st.container(border=True):
        st.subheader("Upload conversation audio")
        st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg")
        audio = st.file_uploader("Choose an audio file", type=["wav","mp3","m4a","aac","flac","ogg"], key="audio_upl")  # [web:2]
        if audio:
            st.audio(audio)  # [web:2]
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "landing"
        with c2:
            if audio and st.button("Continue ➝ License"):
                st.session_state.audio_file = audio
                st.session_state.audio_path = _save_temp(audio, ".audio")  # [web:2]
                st.session_state.step = "license"

elif st.session_state.step == "license":
    with st.container(border=True):
        st.subheader("Upload license key")
        st.caption("Accepted: txt, json, key, lic")
        keyf = st.file_uploader("Choose a license key file", type=["txt","json","key","lic"], key="lic_upl")  # [web:2]
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "audio"
        with c2:
            if keyf and st.button("Continue ➝ Explore"):
                st.session_state.license_file = keyf
                st.session_state.license_path = _save_temp(keyf, ".lic")  # [web:2]
                st.session_state.step = "ready"

elif st.session_state.step == "ready":
    with st.container(border=True):
        st.subheader("Review")
        st.write({
            "audio": getattr(st.session_state.audio_file, "name", None),
            "license": getattr(st.session_state.license_file, "name", None),
        })  # [web:36]
        if st.button("Explore", type="primary"):
            st.session_state.step = "processing"

elif st.session_state.step == "processing":
    with st.spinner("Running analysis…"):
        result_path1, result_path2, result_obj1, result_obj2 = run_pipeline(
            audio_path=Path(st.session_state.audio_path),
            license_path=Path(st.session_state.license_path),
        )
        st.session_state.result_path1 = result_path1
        st.session_state.result_path2 = result_path2
        st.session_state.result_obj1 = result_obj1
        st.session_state.result_obj2 = result_obj2
    st.session_state.step = "result"
    st.rerun()

elif st.session_state.step == "result":
    with st.container(border=True):
        st.subheader("Transcription Output")
        st.json(st.session_state.result_obj1, expanded=2)
        st.download_button(
            "Download Transcription JSON",
            data=json.dumps(st.session_state.result_obj1, indent=2),
            file_name="transcription_output.json",
            mime="application/json",
        )
        st.subheader("Analysis Output")
        st.json(st.session_state.result_obj2, expanded=2)
        st.download_button(
            "Download Analysis JSON",
            data=json.dumps(st.session_state.result_obj2, indent=2),
            file_name="analysis_output.json",
            mime="application/json",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run again"):
                for k in [
                    "step", "audio_file", "license_file", "audio_path",
                    "license_path", "result_obj1", "result_obj2",
                    "result_path1", "result_path2"
                ]:
                    if k in st.session_state:
                        del st.session_state[k]
                _init_state()
        with c2:
            if st.button("Exit"):
                st.stop()
