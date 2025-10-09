import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Convolyser.AI Conversation Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==== Custom Gradient Theme & Styling ====
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="st-"], .main {
        font-family: 'Inter', sans-serif !important;
        background: radial-gradient(ellipse at top right, #7d3fff 10%, #23142e 70%, #0f0817 100%);
        color: #fff;
        min-height: 100vh;
    }
    .navbar, .brand, .hero, .cta-row {
        background: transparent !important;
    }
    .stepper, .card, .stButton>button, .stDownloadButton>button, .stFileUploader>button {
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
        color: #fff !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-image: linear-gradient(90deg, #b164ff 0%, #466fff 100%) !important;
        border-radius: 24px !important;
        padding: 12px 32px !important;
        font-weight: 700 !important;
        color: #fff !important;
        border: none;
        margin: 8px 0 0 0;
        box-shadow: 0 1px 12px 0 #7d3fff22 !important;
        transition: background 200ms;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #7d3fff 0%, #9350f5 100%) !important;
        color: #fff;
    }
    h1, h2, h3, h4, h5 {
        color: #fff !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }
    .small-muted {
        color: #d2bcffcc !important;
        font-size: 1.1rem !important;
        line-height: 1.5;
    }
    /* Bottom-left button fix */
    #get-started-btn {
        position: fixed;
        left: 40px;
        bottom: 40px;
        z-index: 9999;
        margin-bottom: 0;
    }
    /* Hide default Streamlit hamburger */
    [data-testid="baseMenuButton"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# ==== Session State Initialization ====
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

# ==== Util: Save Temp Files ====
def _save_temp(uploaded_file, suffix: str) -> Path:
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

# ==== Stepper ====
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
        chips.append(f'<div class="{cls}">{lbl}</div>')
    st.markdown(
        f'<div class="stepper">{"".join(chips)}</div>',
        unsafe_allow_html=True
    )

# ==== Main App Layout ====
col_logo, col_cta = st.columns([0.7, 0.3])

with col_logo:
    # App branding/title area
    st.markdown(
        """
        <div class="navbar">
            <div class="brand">
                <h1 style="font-size:2.7rem; margin-bottom:12px;">Convolyser.AI</h1>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    # Hero
    if st.session_state.step == "landing":
        st.markdown(
            """
            <div class="hero">
                <h1>Try It Free.<br>Scale When<br>You're Ready.</h1>
                <p class="small-muted">Get started without limits. Explore Convolyser.AI at your pace—upgrade only when your insights grow too big to ignore</p>
            </div>
            """, unsafe_allow_html=True
        )

with col_cta:
    st.markdown("", unsafe_allow_html=True)
    # Optionally show other quick links here

# Stepper
if st.session_state.step != "landing":
    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    _stepper()

# ==== Landing Page (Get Started button at bottom-left) ====
if st.session_state.step == "landing":
    st.markdown(
        """
        <div style="height: 45vh"></div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Schedule Demo", key="demo", help="Schedule a demo call"):
        # Add demo scheduling logic here
        st.toast("Schedule demo feature coming soon.")
    # Fixed position Get Started at bottom-left (absolute, overlays all as per spec)
    st.markdown(
        '''
        <div id="get-started-btn">
            <form action="#" method="post">
                <button type="submit" class="stButton">
                    Get started
                </button>
            </form>
        </div>
        <script>
        const btn = window.parent.document.querySelector('button:contains("Get started")');
        if(btn) { btn.onclick = function(){window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", key: "get_started_clicked", value: true}, "*");};}
        </script>
        ''',
        unsafe_allow_html=True
    )
    # Now, Streamlit button event (acts as normal button, but positioned bottom left)
    if st.session_state.get("get_started_clicked", False) or st.button("Get started", key="getstart", help="Begin", args=()):
        st.session_state.step = "audio"
        st.session_state["get_started_clicked"] = False  # reset for repeat visits

# ==== Audio Upload Step ====
elif st.session_state.step == "audio":
    with st.container(border=True):
        st.subheader("Upload conversation audio")
        st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg audio")
        audio = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a", "aac", "flac", "ogg"], key="audioupl")
        if audio:
            st.audio(audio)
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "landing"
        with c2:
            if audio and st.button("Continue License"):
                st.session_state.audio_file = audio
                st.session_state.audio_path = _save_temp(audio, ".audio")
                st.session_state.step = "license"

# ==== License Upload Step ====
elif st.session_state.step == "license":
    with st.container(border=True):
        st.subheader("Upload license key")
        st.caption("Accepted: txt, json, key, lic")
        keyf = st.file_uploader("Choose a license key file", type=["txt", "json", "key", "lic"], key="licupl")
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "audio"
        with c2:
            if keyf and st.button("Continue Explore"):
                st.session_state.license_file = keyf
                st.session_state.license_path = _save_temp(keyf, ".lic")
                st.session_state.step = "ready"

# ==== Review & Explore Step ====
elif st.session_state.step == "ready":
    with st.container(border=True):
        st.subheader("Review")
        st.write("Audio:", getattr(st.session_state.audio_file, "name", None))
        st.write("License:", getattr(st.session_state.license_file, "name", None))
        if st.button("Explore", type="primary"):
            st.session_state.step = "processing"

# ==== Processing Step ====
elif st.session_state.step == "processing":
    with st.spinner("Running analysis ..."):
        try:
            tpath, apath, tcontent, acontent = run_pipeline(
                audio_path=Path(st.session_state.audio_path),
                license_path=Path(st.session_state.license_path)
            )
            st.session_state.transcription_path = tpath
            st.session_state.analysis_path = apath
            try:
                st.session_state.transcription_raw = Path(tpath).read_text(encoding="utf-8")
            except Exception:
                st.session_state.transcription_raw = "Failed to read transcription file"
            try:
                st.session_state.analysis_raw = Path(apath).read_text(encoding="utf-8")
            except Exception:
                st.session_state.analysis_raw = "Failed to read analysis file"
        except Exception as e:
            st.session_state.transcription_raw = f"Pipeline failed: {e}"
            st.session_state.analysis_raw = ""
        time.sleep(0.3)
        st.session_state.step = "result"
        st.rerun()

# ==== Result Step ====
elif st.session_state.step == "result":
    with st.container(border=True):
        st.subheader("Transcription Output (File Content)")
        st.text(st.session_state.transcription_raw or "No output or unable to read file")
        st.download_button("Download Transcription Output", data=st.session_state.transcription_raw or "", file_name="transcription_output.txt", mime="text/plain")
        st.subheader("Analysis Output (File Content)")
        st.text(st.session_state.analysis_raw or "No output or unable to read file")
        st.download_button("Download Analysis Output", data=st.session_state.analysis_raw or "", file_name="analysis_output.txt", mime="text/plain")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run again"):
                for k in ["step", "audio_file", "license_file", "audio_path", "license_path", "transcription_path", "analysis_path", "transcription_raw", "analysis_raw"]:
                    if k in st.session_state:
                        del st.session_state[k]
                _init_state()
        with c2:
            if st.button("Exit"):
                st.stop()
