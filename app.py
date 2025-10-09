import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

st.set_page_config(
    page_title="YBrantWorks Conversation Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #4B0082 0%, #000000 100%);
        color: white;
        min-height: 100vh;
        font-family: "Montserrat", "Roboto", sans-serif;
    }
    /* Adjust default text color for visibility */
    .css-1d391kg, .css-1v0mbdj, .css-1aumxhk, .css-1frv0r7, h1, h2, h3, h4, h5, h6, p, span, label {
        color: white !important;
    }
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.4em;
    }
    .hero p {
        font-size: 1.2rem;
        opacity: 0.90;
        margin-bottom: 1.4em;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #A020F0 0%, #4B0082 100%);
        color: white;
        font-weight: 600;
        padding: 0.65em 1.7em;
        border-radius: 40px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 180px;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #4B0082 0%, #A020F0 100%);
        color: white;
    }
    .bottom-left-button {
        position: fixed;
        bottom: 36px;
        left: 36px;
        z-index: 100;
    }
    .main-content {
        margin-bottom: 80px;
        margin-top: 32px;
    }
    .card {
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 1.2em 2em;
        margin-bottom: 1.7em;
        box-shadow: 0 2px 18px 0 rgba(80,20,150,0.13);
    }
    hr {
        border-color: rgba(255,255,255,0.07);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

def save_temp_uploaded_file(uploadedfile, suffix=""):
    ext = Path(uploadedfile.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploadedfile.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

if st.session_state.step == "landing":
    st.markdown(
        """
        <div class="hero">
            <h1>Try It Free. Scale When You're Ready.</h1>
            <p>Get started without limits. Explore Conversation Intelligence. Upgrade only when your insights grow too big to ignore.</p>
        </div>
        <div class="card">
            <h3>Let's Connect and Grow Smarter</h3>
            <p>Have questions or want to see how our platform can help? Just fill out the form—we'll get back to you soon.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif st.session_state.step == "audio":
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
            st.session_state.audiofile = audio
            st.session_state.audiopath = save_temp_uploaded_file(audio, ".audio")
            st.session_state.step = "license"

elif st.session_state.step == "license":
    st.subheader("Upload license key")
    st.caption("Accepted: txt, json, key, lic files")
    keyf = st.file_uploader("Choose a license key file", type=["txt", "json", "key", "lic"], key="keylicupl")
    c1, c2 = st.columns([0.2, 0.8])
    with c1:
        if st.button("Back"):
            st.session_state.step = "audio"
    with c2:
        if keyf and st.button("Continue Explore"):
            st.session_state.licensefile = keyf
            st.session_state.licensepath = save_temp_uploaded_file(keyf, ".lic")
            st.session_state.step = "ready"

elif st.session_state.step == "ready":
    st.subheader("Review & Confirm")
    st.write("Audio file:", getattr(st.session_state.audiofile, "name", None))
    st.write("License file:", getattr(st.session_state.licensefile, "name", None))
    if st.button("Explore"):
        st.session_state.step = "processing"

elif st.session_state.step == "processing":
    with st.spinner("Running analysis..."):
        try:
            tpath, apath, tcontent, acontent = run_pipeline(
                audiopath=Path(st.session_state.audiopath),
                licensepath=Path(st.session_state.licensepath),
                transcriptionpath=st.session_state.transcriptionpath,
                analysispath=st.session_state.analysispath,
            )
            st.session_state.transcriptionpath = tpath
            st.session_state.analysispath = apath
            try:
                st.session_state.transcriptionraw = Path(tpath).read_text(encoding="utf-8")
            except Exception:
                st.session_state.transcriptionraw = "Failed to read transcription file"
            try:
                st.session_state.analysisraw = Path(apath).read_text(encoding="utf-8")
            except Exception:
                st.session_state.analysisraw = "Failed to read analysis file"
        except Exception as e:
            st.session_state.transcriptionraw = f"Pipeline failed: {e}"
            st.session_state.analysisraw = ""
            time.sleep(0.3)

        st.session_state.step = "result"
        st.rerun()

elif st.session_state.step == "result":
    st.subheader("Transcription Output File Content")
    st.text(st.session_state.transcriptionraw or "No output or unable to read file")
    st.download_button(
        "Download Transcription Output",
        data=st.session_state.transcriptionraw or "",
        file_name="transcriptionoutput.txt",
        mime="text/plain",
    )
    st.subheader("Analysis Output File Content")
    st.text(st.session_state.analysisraw or "No output or unable to read file")
    st.download_button(
        "Download Analysis Output",
        data=st.session_state.analysisraw or "",
        file_name="analysisoutput.txt",
        mime="text/plain",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Run again"):
            for k in [
                "step",
                "audiofile",
                "licensefile",
                "audiopath",
                "licensepath",
                "transcriptionpath",
                "analysispath",
                "transcriptionraw",
                "analysisraw",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            init_state()
    with c2:
        if st.button("Exit"):
            st.stop()

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div class="bottom-left-button">
""", unsafe_allow_html=True)

if st.session_state.step == "landing":
    if st.button("Get started", key="bottom_get_started"):
        st.session_state.step = "audio"

st.markdown("</div>", unsafe_allow_html=True)
