import json
import time
import tempfile
from pathlib import Path

import streamlit as st
from dummy_processor import run_pipeline

st.set_page_config(
    page_title="YBrantWorks • Conversation Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

THEME_PRIMARY = "#dc2626"
APP_CSS = """
<style>
/* ... CSS code unchanged ... */
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

def _init_state():
    for k, v in {
        "step": "landing",
        "audio_file": None,
        "license_file": None,
        "audio_path": None,
        "license_path": None,
        "result_obj": None,
        "result_raw": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

def _save_temp(uploaded_file, suffix: str) -> Path:
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

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

col_logo, col_cta = st.columns([0.7, 0.3])
with col_logo:
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    left, right = st.columns([0.8, 0.2])
    with left:
        st.markdown('<div class="brand">', unsafe_allow_html=True)
        st.image("assets/logo.png", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.image("assets/icon.png", use_container_width=False)
    st.markdown("</div>", unsafe_allow_html=True)

with col_logo:
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("<h1>Conversation insights, instantly</h1>", unsafe_allow_html=True)
    st.markdown('<p class="small-muted">Upload a call, apply your license, then explore real‑time outputs — all on a polished red theme.</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_cta:
    st.markdown('<div class="cta-row">', unsafe_allow_html=True)
    if st.session_state.step == "landing":
        if st.button("Get started", type="primary"):
            st.session_state.step = "audio"
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color:rgba(255,255,255,0.08)'>", unsafe_allow_html=True)
_stepper()

if st.session_state.step == "landing":
    st.markdown('<div class="card">Welcome — click “Get started” to begin.</div>', unsafe_allow_html=True)

elif st.session_state.step == "audio":
    with st.container(border=True):
        st.subheader("Upload conversation audio")
        st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg")
        audio = st.file_uploader("Choose an audio file", type=["wav","mp3","m4a","aac","flac","ogg"], key="audio_upl")
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
        keyf = st.file_uploader("Choose a license key file", type=["txt","json","key","lic"], key="lic_upl")
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "audio"
        with c2:
            if keyf and st.button("Continue ➝ Explore"):
                st.session_state.license_file = keyf
                st.session_state.license_path = _save_temp(keyf, ".lic")
                st.session_state.step = "ready"

elif st.session_state.step == "ready":
    with st.container(border=True):
        st.subheader("Review")
        st.write({
            "audio": getattr(st.session_state.audio_file, "name", None),
            "license": getattr(st.session_state.license_file, "name", None),
        })
        if st.button("Explore", type="primary"):
            st.session_state.step = "processing"

elif st.session_state.step == "processing":
    with st.spinner("Running analysis…"):
        result_path = run_pipeline(
            audio_path=Path(st.session_state.audio_path),
            license_path=Path(st.session_state.license_path),
        )
        try:
            raw_content = Path(result_path).read_text()
            st.session_state.result_raw = raw_content  # <-- store raw text output
            st.session_state.result_obj = json.loads(raw_content)
        except Exception:
            st.session_state.result_raw = "Failed to read output file content."
            st.session_state.result_obj = {"error": "Failed to read JSON."}
        time.sleep(0.3)
    st.session_state.step = "result"
    st.rerun()

elif st.session_state.step == "result":
    with st.container(border=True):
        st.subheader("Result")
        # Show raw file content as plain text (not JSON/dict)
        st.text(st.session_state.result_raw)
        st.download_button(
            "Download Output",
            data=st.session_state.result_raw,
            file_name="result.txt",
            mime="text/plain",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run again"):
                for k in ["step","audio_file","license_file","audio_path","license_path","result_obj","result_raw"]:
                    if k in st.session_state:
                        del st.session_state[k]
                _init_state()
        with c2:
            if st.button("Exit"):
                st.stop()
