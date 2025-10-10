import json
import time
import tempfile
import base64
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html
from dummy_processor import run_pipeline

# ---------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="YBrantWorks • Conversation Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------
# Theme injection (Cosmic purple grid, starfield, glass cards)
# ---------------------------------------------------------------------
def _inject_theme():
    st.markdown(
        """
        <style>
        :root{
          --bg-0:#0a0516;
          --bg-1:#150a30;
          --bg-2:#2a0a52;
          --bg-3:#4a1b8c;
          --accent-0:#7a3cff;
          --accent-1:#b266ff;
          --text-0:#f5f2ff;
          --text-1:#d8ccff;
          --muted:#b9a9e6;
          --card:#ffffff0f;
          --card-border:#ffffff22;
          --card-hover:#ffffff1a;
        }
        .stApp {
          background:
            radial-gradient(1200px 600px at 50% -10%, var(--bg-2) 0%, var(--bg-1) 35%, var(--bg-0) 80%) fixed,
            linear-gradient(180deg, #000000, #000000) fixed;
          color: var(--text-0);
        }
        .stApp::before, .stApp::after{
          content:"";
          position:fixed; inset:0; pointer-events:none; z-index:0;
        }
        .stApp::before{
          background:
            linear-gradient(transparent 31px, #ffffff12 32px),
            linear-gradient(90deg, transparent 31px, #ffffff12 32px);
          background-size:32px 32px;
          mix-blend-mode:screen; opacity:0.25;
        }
        .stApp::after{
          background:
            radial-gradient(2px 2px at 20% 30%, #fff 50%, transparent 52%),
            radial-gradient(2px 2px at 70% 60%, #fff 50%, transparent 52%),
            radial-gradient(1.5px 1.5px at 40% 80%, #fff 50%, transparent 52%),
            radial-gradient(1.5px 1.5px at 85% 20%, #fff 50%, transparent 52%);
          opacity:0.35; filter:drop-shadow(0 0 6px #a884ff88);
          animation: twinkle 6s linear infinite;
        }
        @keyframes twinkle {
          0%,100%{opacity:0.25}
          50%{opacity:0.45}
        }

        h1,h2,h3,h4,h5,h6 { color: var(--text-0) !important; }
        p, span, label, small, .markdown-text-container { color: var(--text-1) !important; }
        .small-muted { color: var(--muted); font-size:0.95rem; }

        .stButton>button {
          background: linear-gradient(90deg, var(--accent-0), var(--accent-1));
          color:#fff; border:1px solid #ffffff22;
          padding:0.6rem 1rem; border-radius:0.7rem;
          font-weight:600; box-shadow:0 6px 24px #7a3cff33;
        }
        .stButton>button:hover {
          transform: translateY(-1px);
          box-shadow:0 10px 28px #b266ff40;
        }

        .stTextInput > div > div > input,
        .stFileUploader > div {
          background: #ffffff0d; color:var(--text-0);
          border:1px solid var(--card-border);
          border-radius:0.6rem;
        }

        .block-container { padding-top: 2rem; z-index:1; position:relative; }
        .card {
          background: var(--card);
          border:1px solid var(--card-border);
          border-radius: 1rem;
          padding: 1rem 1.2rem;
          transition: background .2s ease;
        }
        .card:hover { background: var(--card-hover); }

        .navbar { display:flex; align-items:center; justify-content:space-between; margin-bottom: 0.5rem; }
        .brand { display:flex; align-items:center; gap:.6rem; }
        .hero h1 { font-size: 3rem; line-height: 1.1; margin: .2rem 0 .6rem 0; }
        .cta-row { display:flex; gap:.6rem; justify-content:flex-end; align-items:center; }

        .stepper { display:flex; gap:.5rem; margin: .2rem 0 1rem 0; flex-wrap:wrap; }
        .step {
          background:#ffffff10; border:1px solid #ffffff22; color:var(--text-1);
          padding:.35rem .6rem; border-radius:.6rem; font-size:.9rem;
        }
        .step.active { background:linear-gradient(90deg, #6d33ff66, #b266ff44); color:#fff; border-color:#b266ff77; }

        hr { border-color: #ffffff18; }

        /* Carousel widget base styles */
        .cw {
          width:100%;
          border-radius:1rem;
          overflow:hidden;
          border:1px solid var(--card-border);
          background: var(--card);
          box-shadow: 0 8px 28px #00000040;
        }
        .cw .frame {
          position:relative; width:100%; height:260px;
          background: radial-gradient(600px 260px at 50% 0%, #4a1b8c33, transparent);
        }
        .cw .frame img {
          position:absolute; inset:0; width:100%; height:100%;
          object-fit:cover; transition: opacity .6s ease; opacity:0;
        }
        .cw .dots {
          position:absolute; bottom:10px; left:0; right:0;
          display:flex; gap:6px; justify-content:center; z-index:3;
        }
        .cw .dot {
          width:8px; height:8px; border-radius:999px;
          background:#ffffff66; border:1px solid #ffffffaa;
        }
        .cw .dot.active { background:#ffffff; }
        </style>
        """,
        unsafe_allow_html=True,
    )

_inject_theme()

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
def _init_state():
    for k, v in {
        "step": "landing",
        "audio_file": None,
        "license_file": None,
        "audio_path": None,
        "license_path": None,
        "transcription_path": None,
        "analysis_path": None,
        "transcription_raw": None,
        "analysis_raw": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _save_temp(uploaded_file, suffix: str) -> Path:
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

def _img_mime(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext in [".png"]:
        return "image/png"
    if ext in [".gif"]:
        return "image/gif"
    return "image/png"

def _b64_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _render_carousel(image_paths, height: int = 260):
    imgs = []
    for p in image_paths:
        pth = Path(p)
        if pth.exists():
            mime = _img_mime(pth)
            b64 = _b64_image(pth)
            imgs.append(f'data:{mime};base64,{b64}')
    if not imgs:
        return  # nothing to render
    # Build HTML
    dots = "".join([f'<div class="dot" data-i="{i}"></div>' for i in range(len(imgs))])
    tags = "".join([f'<img src="{src}" />' for src in imgs])
    html(
        f"""
        <div class="cw">
          <div class="frame" style="height:{height}px">
            {tags}
            <div class="dots">{dots}</div>
          </div>
        </div>
        <script>
          (function(){{
            const root = window.frameElement?.parentElement || document;
            const scope = root.querySelectorAll('.cw').item(-1) || root;
            const imgs = scope.querySelectorAll('.frame img');
            const dots = scope.querySelectorAll('.dot');
            let i = 0;
            function show(n){{
              imgs.forEach((im,ix)=> im.style.opacity = (ix===n?1:0));
              dots.forEach((d,ix)=> d.classList.toggle('active', ix===n));
            }}
            show(0);
            let timer = setInterval(()=>{{ i = (i+1)%imgs.length; show(i); }}, 2800);
            dots.forEach((d,ix)=>{{
              d.addEventListener('click',()=>{{ i=ix; show(i); clearInterval(timer); timer=setInterval(()=>{{ i=(i+1)%imgs.length; show(i); }}, 2800); }});
            }});
          }})();
        </script>
        """,
        height=height + 16,
    )

def _stepper():
    stages = ["landing", "audio", "license", "ready", "processing", "result"]
    labels = ["Upload audio", "License key", "Explore", "Result"]
    try:
        idx = max(1, min(4, stages.index(st.session_state.step)))
    except ValueError:
        idx = 1
    chips = []
    for i, lbl in enumerate(labels, 1):
        cls = "step active" if i <= idx else "step"
        chips.append(f'<div class="{cls}">{i}. {lbl}</div>')
    st.markdown(f'<div class="stepper">{"".join(chips)}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Navbar + Hero
# ---------------------------------------------------------------------
col_logo, col_cta = st.columns([0.7, 0.3])

with col_logo:
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    left, right = st.columns([0.8, 0.2])
    with left:
        st.markdown('<div class="brand">', unsafe_allow_html=True)
        try:
            st.image("assets/logo.png", use_container_width=False)
        except Exception:
            st.markdown("YBrantWorks", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        try:
            st.image("assets/icon.png", use_container_width=False)
        except Exception:
            pass
    st.markdown("</div>", unsafe_allow_html=True)

with col_logo:
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("<h1>Conversation insights, instantly</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="small-muted">Upload a call, apply a license, then explore real‑time outputs — now on a cosmic purple theme.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cta:
    st.markdown('<div class="cta-row">', unsafe_allow_html=True)
    if st.session_state.step == "landing":
        if st.button("Get started", type="primary"):
            st.session_state.step = "audio"
    st.markdown("</div>", unsafe_allow_html=True)

    # Right-side carousel under CTA
    carousel_images = [
        "assets/carousel_1.jpg",
        "assets/carousel_2.jpg",
        "assets/carousel_3.jpg",
    ]
    _render_carousel(carousel_images, height=260)

st.markdown("<hr>", unsafe_allow_html=True)
_stepper()

# ---------------------------------------------------------------------
# Flow screens
# ---------------------------------------------------------------------
if st.session_state.step == "landing":
    st.markdown('<div class="card">Welcome — click “Get started” to begin.</div>', unsafe_allow_html=True)

elif st.session_state.step == "audio":
    with st.container(border=True):
        st.subheader("Upload conversation audio")
        st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg")
        audio = st.file_uploader(
            "Choose an audio file",
            type=["wav", "mp3", "m4a", "aac", "flac", "ogg"],
            key="audio_upl",
        )
        if audio:
            st.audio(audio)
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "landing"
        with c2:
            if audio and st.button("Continue ➝ License"):
                st.session_state.audio_file = audio
                st.session_state.audio_path = _save_temp(audio, ".audio")
                st.session_state.step = "license"

elif st.session_state.step == "license":
    with st.container(border=True):
        st.subheader("Upload license key")
        st.caption("Accepted: txt, json, key, lic")
        keyf = st.file_uploader(
            "Choose a license key file",
            type=["txt", "json", "key", "lic"],
            key="lic_upl",
        )
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "audio"
        with c2:
            if keyf and st.button("Continue ➝ Explore"):
                st.session_state.license_file = keyf
                st.session_state.license_path = _save_temp(keyf, ".key")
                st.session_state.step = "ready"

elif st.session_state.step == "ready":
    with st.container(border=True):
        st.subheader("Ready to analyze")
        st.caption("Summary of inputs")
        c1, c2 = st.columns(2)
        with c1:
            st.write("Audio path:", st.session_state.audio_path)
        with c2:
            st.write("License path:", st.session_state.license_path)
        cc1, cc2 = st.columns([0.2, 0.8])
        with cc1:
            if st.button("Back"):
                st.session_state.step = "license"
        with cc2:
            if st.button("Run analysis"):
                st.session_state.step = "processing"
# --- PROCESSING (replace this entire branch) ---
elif st.session_state.step == "processing":
    with st.spinner("Transcribing and analyzing…"):
        try:
            result = run_pipeline(
                st.session_state.audio_path, st.session_state.license_path
            )

            # Reset targets
            st.session_state.transcription_path = None
            st.session_state.analysis_path = None
            st.session_state.transcription_raw = None
            st.session_state.analysis_raw = None

            if isinstance(result, dict):
                # Keep existing key compatibility but do NOT parse JSON
                tp = result.get("transcription_path") or result.get("transcript_path")
                rp = result.get("analysis_path") or result.get("report_path")
                st.session_state.transcription_path = Path(tp) if tp else None
                st.session_state.analysis_path = Path(rp) if rp else None
                st.session_state.transcription_raw = (
                    result.get("transcription_raw")
                    or result.get("transcript_raw")
                    or result.get("transcription")
                )
                st.session_state.analysis_raw = (
                    result.get("analysis_raw")
                    or result.get("report_raw")
                    or result.get("analysis")
                )
            else:
                # Treat non-dict results as a sequence of raw outputs in order
                seq = list(result) if isinstance(result, (list, tuple)) else [result]
                if len(seq) > 0:
                    st.session_state.transcription_raw = seq[0]
                if len(seq) > 1:
                    st.session_state.analysis_raw = seq[1]
                if len(seq) > 2 and isinstance(seq[2], (str, Path)) and str(seq[2]):
                    p = Path(str(seq[2]))
                    st.session_state.transcription_path = p if p.exists() else None
                if len(seq) > 3 and isinstance(seq[3], (str, Path)) and str(seq[3]):
                    p = Path(str(seq[3]))
                    st.session_state.analysis_path = p if p.exists() else None

            time.sleep(0.6)
            st.session_state.step = "result"

        except Exception as e:
            st.error(f"Processing failed: {e}")
            st.session_state.step = "ready"

    with cc2:
        if st.button("Start over"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            _init_state()
            st.session_state.step = "landing"
