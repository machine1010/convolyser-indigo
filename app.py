import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

# Set page config with wide layout
st.set_page_config(
    page_title="BrantWorks Conversation Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS for gradient background with lines and reposition Get Started button
st.markdown(
    """
    <style>
    /* Background gradient with diagonal lines */
    body {
        background: linear-gradient(135deg, #3a1c71, #d76d77, #ffaf7b);
        background-size: 200% 200%;
        animation: gradientBG 15s ease infinite;
        position: relative;
        overflow-x: hidden;
    }
    @keyframes gradientBG {
        0%{background-position:0% 50%}
        50%{background-position:100% 50%}
        100%{background-position:0% 50%}
    }
    /* Diagonal lines overlay */
    body::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        background-image:
            repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 20px),
            repeating-linear-gradient(-45deg, rgba(255,255,255,0.05) 0, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 20px);
        z-index: -1;
    }

    /* Move Get Started button container to bottom left */
    .cta-row {
        display: flex !important;
        justify-content: flex-start !important; /* align left */
        align-items: flex-end !important; /* align bottom */
        height: 100px; /* fixed height container */
        position: relative;
        padding-left: 20px;
    }

    /* Optionally, add margin-top to push button down if inside container */
    .cta-row > button:first-child {
        margin-top: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state defaults if not present
def initstate():
    defaults = dict(
        step="landing",
        audiofile=None,
        licensefile=None,
        audiopath=None,
        licensepath=None,
        transcriptionpath=None,
        analysispath=None,
        transcriptionraw=None,
        analysisraw=None,
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


initstate()


def savetempuploadedfile(uploadedfile, suffix: str = ""):
    from pathlib import Path

    ext = Path(uploadedfile.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploadedfile.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def stepper(stages):
    labels = {
        "landing": "Upload audio",
        "audio": "License key",
        "license": "Explore",
        "ready": "Result",
    }
    try:
        idx = max(0, min(len(stages) - 1, stages.index(st.session_state.step)))
    except ValueError:
        idx = 0
    chips = []
    for i, lbl in enumerate(labels.values()):
        cls = "step active" if i == idx else "step"
        chips.append(f'<div class="{cls}">{lbl}</div>')
    st.markdown(
        f'<div class="stepper">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )


with st.container():
    collogo, colcta = st.columns([0.7, 0.3])
    with collogo:
        st.image("assets/logo.png", use_container_width=False)
    with colcta:
        # "Get started" button is moved to bottom left by CSS above
        if st.session_state.step == "landing":
            if st.button("Get started", type="primary"):
                st.session_state.step = "audio"

st.markdown("---")

stepper(["landing", "audio", "license", "ready", "processing", "result"])

if st.session_state.step == "landing":
    st.markdown('<div class="card">Welcome, click Get started to begin.</div>', unsafe_allow_html=True)

elif st.session_state.step == "audio":
    with st.container():
        st.subheader("Upload conversation audio")
        st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg")
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
                st.session_state.audiopath = savetempuploadedfile(audio, ".audio")
                st.session_state.step = "license"

elif st.session_state.step == "license":
    with st.container():
        st.subheader("Upload license key")
        st.caption("Accepted: txt, json, key, lic")
        keyf = st.file_uploader("Choose a license key file", type=["txt", "json", "key", "lic"], key="keylicupl")
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            if st.button("Back"):
                st.session_state.step = "audio"
        with c2:
            if keyf and st.button("Continue Explore"):
                st.session_state.licensefile = keyf
                st.session_state.licensepath = savetempuploadedfile(keyf, ".lic")
                st.session_state.step = "ready"

elif st.session_state.step == "ready":
    with st.container():
        st.subheader("Review")
        st.write("Audio file:", getattr(st.session_state.audiofile, "name", None))
        st.write("License file:", getattr(st.session_state.licensefile, "name", None))
        if st.button("Explore", type="primary"):
            st.session_state.step = "processing"

elif st.session_state.step == "processing":
    with st.spinner("Running analysis..."):
        try:
            tpath, apath, tcontent, acontent = runpipeline(
                audiopath=Path(st.session_state.audiopath), licensepath=Path(st.session_state.licensepath)
            )
            st.session_state.transcriptionpath = tpath
            st.session_state.analysispath = apath
            st.session_state.transcriptionraw = Path(tpath).read_text(encoding="utf-8")
            st.session_state.analysisraw = Path(apath).read_text(encoding="utf-8")
        except Exception as e:
            st.session_state.transcriptionraw = f"Pipeline failed: {e}"
            st.session_state.analysisraw = None
        time.sleep(0.3)
        st.session_state.step = "result"
        st.experimental_rerun()

elif st.session_state.step == "result":
    with st.container():
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
                initstate()
        with c2:
            if st.button("Exit"):
                st.stop()
