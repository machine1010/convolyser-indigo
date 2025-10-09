import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

st.set_page_config(
    page_title="YBrantWorks Conversation Intelligence",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for gradient background with animated lines
st.markdown("""
    <style>
    body, .stApp {
        background: linear-gradient(135deg, #191654 0%, #43c6ac 100%);
        position: relative;
        overflow-x: hidden;
    }
    /* Animated background lines */
    .lines-bg {
        pointer-events: none;
        position: absolute;
        width: 100vw;
        height: 100vh;
        top: 0;
        left: 0;
        z-index: 0;
    }

    .line {
        position: absolute;
        width: 100vw;
        height: 2px;
        background: rgba(255,255,255,0.08);
        animation: lineanim 8s linear infinite;
    }

    .line:nth-child(1) { top: 20%; }
    .line:nth-child(2) { top: 40%; animation-delay: 2s; }
    .line:nth-child(3) { top: 60%; animation-delay: 4s; }
    .line:nth-child(4) { top: 80%; animation-delay: 6s; }

    @keyframes lineanim {
        from { transform: translateX(-20vw); }
        to { transform: translateX(20vw); }
    }

    /* Center main block */
    .maincenter {
        z-index: 2;
        position: relative;
    }

    .step-img {
        width: 100%;
        max-width: 350px;
        display: block;
        margin: 0 auto 16px auto;
        border-radius: 20px;
        box-shadow: 0 8px 40px rgba(0,0,30,0.08);
        border: 2px solid #2fa4ff22;
        background: #21233b;
    }

    .get-started-btn {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin: 0 0 40px 0;
    }
    </style>

    <div class="lines-bg">
        <div class="line"></div>
        <div class="line"></div>
        <div class="line"></div>
        <div class="line"></div>
    </div>
""", unsafe_allow_html=True)

def init_state():
    for k, v in {
        'step': 'landing',
        'audiofile': None,
        'licensefile': None,
        'audiopath': None,
        'licensepath': None,
        'transcriptionpath': None,
        'analysispath': None,
        'transcriptionraw': None,
        'analysisraw': None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def save_temp(uploadedfile, suffix:str = ""):
    ext = Path(uploadedfile.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploadedfile.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

# Step image map (adjust file names as per your step snapshots)
step_images = {
    "landing": "assets/snapshot_step1.png",
    "audio": "assets/snapshot_step2.png",
    "license": "assets/snapshot_step3.png",
    "ready": "assets/snapshot_step4.png",
}

step_labels = {
    "landing": "Step 1: Start",
    "audio": "Step 2: Upload Audio",
    "license": "Step 3: Provide License",
    "ready": "Step 4: Review and Analyze",
}

st.markdown('<div class="maincenter">', unsafe_allow_html=True)

# --- Navbar and Branding/Logo (optional) ---

# Step-by-step UI, one below another, with image per step
cur_step = st.session_state["step"]

step_order = ["landing", "audio", "license", "ready"]

for step in step_order:
    if step == cur_step:
        # Show image for this step
        st.image(step_images[step], use_column_width=False, caption=step_labels[step], output_format="PNG", clamp=True, channels="RGB", width=320)
        if step == "landing":
            # Custom "Get Started" button row, right aligned as per snapshot
            st.markdown('<div class="get-started-btn">', unsafe_allow_html=True)
            if st.button("Get Started", type="primary", key="get_started_btn"):
                st.session_state["step"] = "audio"
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)
        elif step == "audio":
            st.subheader("Upload conversation audio")
            st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg audio")
            audio = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a", "aac", "flac", "ogg"], key="audioupl")
            if audio:
                st.audio(audio)
            c1, c2 = st.columns([0.2, 0.8])
            with c1:
                if st.button("Back", key="back_audio"):
                    st.session_state["step"] = "landing"
            with c2:
                if audio and st.button("Continue ➔ License"):
                    st.session_state["audiofile"] = audio
                    st.session_state["audiopath"] = save_temp(audio, ".audio")
                    st.session_state["step"] = "license"
        elif step == "license":
            st.subheader("Upload license key")
            st.caption("Accepted: txt, json, key, lic")
            keyf = st.file_uploader("Choose a license key file", type=["txt", "json", "key", "lic"], key="licupl")
            c1, c2 = st.columns([0.2, 0.8])
            with c1:
                if st.button("Back", key="back_license"):
                    st.session_state["step"] = "audio"
            with c2:
                if keyf and st.button("Continue ➔ Review"):
                    st.session_state["licensefile"] = keyf
                    st.session_state["licensepath"] = save_temp(keyf, ".lic")
                    st.session_state["step"] = "ready"
        elif step == "ready":
            st.subheader("Review")
            st.write("Audio file:", getattr(st.session_state["audiofile"], "name", None),
                     "\nLicense:", getattr(st.session_state["licensefile"], "name", None))
            if st.button("Explore (Run Analysis)", type="primary", key="go_processing"):
                st.session_state["step"] = "processing"

if st.session_state["step"] == "processing":
    with st.spinner("Running analysis ..."):
        try:
            tpath, apath, tcontent, acontent = runpipeline(
                audiopath=Path(st.session_state["audiopath"]),
                licensepath=Path(st.session_state["licensepath"]),
            )
            st.session_state["transcriptionpath"] = tpath
            st.session_state["analysispath"] = apath
            try:
                st.session_state["transcriptionraw"] = Path(tpath).read_text(encoding="utf-8")
            except Exception:
                st.session_state["transcriptionraw"] = "Failed to read transcription file"
            try:
                st.session_state["analysisraw"] = Path(apath).read_text(encoding="utf-8")
            except Exception:
                st.session_state["analysisraw"] = "Failed to read analysis file"
        except Exception as e:
            st.session_state["transcriptionraw"] = f"Pipeline failed: {e}"
            st.session_state["analysisraw"] = ""
        time.sleep(0.3)
        st.session_state["step"] = "result"
        st.experimental_rerun()

elif st.session_state["step"] == "result":
    with st.container(border=True):
        st.subheader("Transcription Output File Content")
        st.text(st.session_state["transcriptionraw"] or "No output or unable to read file")
        st.download_button(
            "Download Transcription Output",
            data=st.session_state["transcriptionraw"] or "",
            file_name="transcriptionoutput.txt", mime="text/plain"
        )
        st.subheader("Analysis Output File Content")
        st.text(st.session_state["analysisraw"] or "No output or unable to read file")
        st.download_button(
            "Download Analysis Output",
            data=st.session_state["analysisraw"] or "",
            file_name="analysisoutput.txt", mime="text/plain"
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run again"):
                for k in [
                    "step", "audiofile", "licensefile", "audiopath", "licensepath",
                    "transcriptionpath", "analysispath", "transcriptionraw", "analysisraw"
                ]:
                    if k in st.session_state:
                        del st.session_state[k]
                init_state()
        with c2:
            if st.button("Exit"):
                st.stop()

st.markdown('</div>', unsafe_allow_html=True)
