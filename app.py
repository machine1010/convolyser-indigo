import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

# Page config
st.set_page_config(
    page_title="BrantWorks Conversation Intelligence",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS for violet gradient background with animated lines
st.markdown(
    """
    <style>
    /* Violet gradient background */
    body, .main {
        background: linear-gradient(135deg, #7F00FF, #E100FF);
        background-attachment: fixed;
        position: relative;
        overflow-x: hidden;
    }
    /* Animated diagonal lines */
    body::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: 100vw;
        pointer-events: none;
        background:
            repeating-linear-gradient(
                45deg,
                rgba(255,255,255,0.1),
                rgba(255,255,255,0.1) 1px,
                transparent 1px,
                transparent 10px
            );
        animation: moveLines 15s linear infinite;
        z-index: 0;
    }
    @keyframes moveLines {
        0% { background-position: 0 0; }
        100% { background-position: 100px 100px; }
    }
    /* Ensure main containers stack above the lines */
    .main > div {
        position: relative;
        z-index: 1;
    }
    /* Position Get Started button bottom left */
    .cta-row {
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 2;
        width: auto !important;
    }
    /* Optional: style button if needed */
    .stButton>button {
        background-color: #7F00FF;
        border-color: #E100FF;
        color: white;
        font-weight: bold;
        padding: 0.5em 1.5em;
        border-radius: 8px;
        box-shadow: 0 3px 6px rgba(225, 0, 255, 0.3);
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #E100FF;
        box-shadow: 0 6px 12px rgba(127, 0, 255, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def initstate():
    step = {
        "landing": None,
        "audiofile": None,
        "licensefile": None,
        "audiopath": None,
        "licensepath": None,
        "transcriptionpath": None,
        "analysispath": None,
        "transcriptionraw": None,
        "analysisraw": None,
    }
    for k, v in step.items():
        if k not in st.session_state:
            st.session_state[k] = v

def savetempuploadedfile(uploadedfile, suffix=""):
    ext = Path(uploadedfile.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploadedfile.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

def stepper():
    stages = ["landing", "audio", "license", "ready", "processing", "result"]
    labels = ["Upload audio", "License key", "Explore", "Result"]
    try:
        idx = max(1, min(4, stages.index(st.session_state.step)))
    except ValueError:
        idx = 1
    chips = []
    for i, lbl in enumerate(labels, 1):
        cls = "step active" if i == idx else "step"
        chips.append(f'<div class="{cls}">{lbl}</div>')
    st.markdown(f'<div class="stepper">{"".join(chips)}</div>', unsafe_allow_html=True)

initstate()

if "step" not in st.session_state:
    st.session_state.step = "landing"

# Layout columns for logo and cta button row on the top
col_logo, col_cta = st.columns([0.7, 0.3])

with col_logo:
    st.markdown(
        """
        <div class="navbar">
            <div class="brand"><img src="assets/logo.png" width="auto" height="40"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# NOTE: The top CTA area is kept empty because we move the button container down left
with col_cta:
    st.markdown("")

# Main content for landing step
if st.session_state.step == "landing":
    st.markdown(
        """
        <div class="hero">
            <h1>Conversation insights, instantly</h1>
            <p class="small-muted">Upload a call, apply your license, then explore real-time outputs all on a polished violet theme.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add some padding divs to create vertical space before the fixed Get Started button
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

    # Repositioned Get Started button in a fixed container bottom left
    st.markdown(
        """
        <div class="cta-row">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Use st.sidebar or an absolute positioned div through the next lines to keep the button bottom left
    # Using empty space for layout, button placed at bottom left using component trick below:

    # Trick to place button fixed bottom left using st.markdown and session_state button handling
    
    # Place button in a container with overlay
    get_started_clicked = st.button("Get started", type="primary")

    if get_started_clicked:
        st.session_state.step = "audio"
        st.experimental_rerun()

else:
    # Retain all the other steps as is with existing logic
    if st.session_state.step == "audio":
        with st.container(border=True):
            st.subheader("Upload conversation audio")
            st.caption("Accepted wav, mp3, m4a, aac, flac, ogg audio")
            audio = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a", "aac", "flac", "ogg"], key="audioupl")
            c1, c2 = st.columns([0.2, 0.8])
            with c1:
                if st.button("Back"):
                    st.session_state.step = "landing"
                    st.experimental_rerun()
            with c2:
                if audio and st.button("Continue"):
                    st.session_state.audiofile = audio
                    st.session_state.audiopath = savetempuploadedfile(audio, ".audio")
                    st.session_state.step = "license"
                    st.experimental_rerun()

    elif st.session_state.step == "license":
        with st.container(border=True):
            st.subheader("Upload license key")
            st.caption("Accepted txt, json, key, lic")
            keyf = st.file_uploader("Choose a license key file", type=["txt", "json", "key", "lic"], key="keylicupl")
            c1, c2 = st.columns([0.2, 0.8])
            with c1:
                if st.button("Back"):
                    st.session_state.step = "audio"
                    st.experimental_rerun()
            with c2:
                if keyf and st.button("Continue"):
                    st.session_state.licensefile = keyf
                    st.session_state.licensepath = savetempuploadedfile(keyf, ".lic")
                    st.session_state.step = "ready"
                    st.experimental_rerun()

    elif st.session_state.step == "ready":
        with st.container(border=True):
            st.subheader("Review")
            st.write(f"Audio File: {getattr(st.session_state.audiofile, 'name', None)}")
            st.write(f"License File: {getattr(st.session_state.licensefile, 'name', None)}")
            if st.button("Explore", type="primary"):
                st.session_state.step = "processing"
                st.experimental_rerun()

    elif st.session_state.step == "processing":
        with st.spinner("Running analysis..."):
            try:
                tpath, apath, tcontent, acontent = runpipeline(
                    audiopath=Path(st.session_state.audiopath),
                    licensepath=Path(st.session_state.licensepath),
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
            st.experimental_rerun()

    elif st.session_state.step == "result":
        with st.container(border=True):
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
                        "step", "audiofile", "licensefile", "audiopath", "licensepath",
                        "transcriptionpath", "analysispath", "transcriptionraw", "analysisraw",
                    ]:
                        if k in st.session_state:
                            del st.session_state[k]
                    initstate()
                    st.experimental_rerun()
            with c2:
                if st.button("Exit"):
                    st.stop()
