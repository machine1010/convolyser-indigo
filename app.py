import streamlit as st
from pathlib import Path
import tempfile
import time

# --- Basic theme CSS like convolyser.ai ---
st.set_page_config(page_title="YBrantWorks Conversation Intelligence", page_icon="🔴", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    body, .stApp {
        background-color: #17171a;
        color: #edeef1;
        font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    }
    .brand { font-size:2rem; font-weight:800; color: #fff; }
    .navbar { display:flex; align-items:center; justify-content:left; padding-bottom:1.5rem;}
    .flow-steps {
        display:flex; flex-direction:row; justify-content:center; align-items:center; gap:2rem; margin: 2rem 0 3rem 0;
    }
    .flow-box {
        background:#232325; padding:1.8rem 2rem; border-radius:1.2rem; min-width:180px; box-shadow:0 2px 10px rgba(20,20,30,0.08);
        text-align:center; font-size:1.2rem; font-weight:600; color:#ea394b; border: 2px solid #2d2d32;
    }
    .flow-box-active {
        background: linear-gradient(128deg, #ea394b 0%, #5e1320 70%);
        color: #fff;
        border: 2px solid #ea394b;
        box-shadow: 0 4px 14px #ea394b55;
    }
    .cta-fix { position: fixed; bottom:3vw; left:3vw; }
    .cta-btn {
        background:#ea394b; color:#fff; padding:0.8rem 2.2rem; font-weight:700; border:none; border-radius:0.7rem;
        font-size:1.1rem; box-shadow:0 1px 8px #ea394b66; transition:0.2s;
    }
    .cta-btn:hover {
        background:#d92840; color:#f9f9fb;
    }
    .hero-title { font-size:2.3rem;font-weight:800;letter-spacing:-2px;margin-bottom:1rem; }
    .hero-desc { font-size:1.1rem; color:#f1adbb; margin-bottom:2rem; }
    .stDownloadButton>button { background:#232325; color:#ea394b; }
    hr { border-color:#ea394b22; }
    </style>
""", unsafe_allow_html=True)

# --- Brand Row ---
st.markdown(
    """<div class='navbar'>
        <img src='https://raw.githubusercontent.com/brandonskerritt/streamlit-brand-assets/main/logo.png' height='60'/>
        <span class='brand' style='margin-left: 1rem;'>YBrantWorks</span>
    </div>""",
    unsafe_allow_html=True
)

# --- Title & Description ---
st.markdown("<div class='hero-title'>Conversation insights, instantly</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-desc'>Upload a call, apply your license, then explore real-time outputs — all on a polished red theme.</div>", unsafe_allow_html=True)

# --- Stepper Flow Definitions ---
flow_def = [
    {"emoji": "🎤", "label": "Upload audio"},
    {"emoji": "🗝️", "label": "License key"},
    {"emoji": "🔍", "label": "Explore"},
    {"emoji": "📈", "label": "Result"},
]
step_keys = ["landing", "audio", "license", "ready", "processing", "result"]

if "step" not in st.session_state:
    st.session_state["step"] = "landing"

def step_index(step_key=None):
    if not step_key:
        step_key = st.session_state["step"]
    try:
        idx = ["landing", "audio", "license", "ready", "processing", "result"].index(step_key)
    except:
        idx = 0
    return max(0, min(3, idx-1))

idx = step_index()

# --- Horizontal Stepper with Emojis ---
stepper_boxes = []
for n, stage in enumerate(flow_def):
    box_class = "flow-box flow-box-active" if n==idx else "flow-box"
    stepper_boxes.append(f"<div class='{box_class}'>{stage['emoji']}<br>{stage['label']}</div>")
st.markdown(f"<div class='flow-steps'>{''.join(stepper_boxes)}</div>", unsafe_allow_html=True)

# --- Main content based on current step ---
if st.session_state["step"] == "landing":
    st.markdown("Welcome — click **Get started** to begin.")
elif st.session_state["step"] == "audio":
    st.subheader("Upload conversation audio")
    st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg audio")
    audio = st.file_uploader("Choose an audio file", type=["wav","mp3","m4a","aac","flac","ogg"], key="audioupl")
    if audio:
        st.audio(audio)
    col1, col2 = st.columns([0.2,0.8])
    with col1:
        if st.button("Back"):
            st.session_state["step"] = "landing"
    with col2:
        if audio and st.button("Continue: License"):
            st.session_state["audiofile"] = audio
            st.session_state["step"] = "license"
elif st.session_state["step"] == "license":
    st.subheader("Upload license key")
    st.caption("Accepted: txt, json, key, lic")
    keyf = st.file_uploader("Choose a license key file", type=["txt","json","key","lic"], key="licupl")
    col1, col2 = st.columns([0.2,0.8])
    with col1:
        if st.button("Back"):
            st.session_state["step"] = "audio"
    with col2:
        if keyf and st.button("Continue: Explore"):
            st.session_state["licensefile"] = keyf
            st.session_state["step"] = "ready"
elif st.session_state["step"] == "ready":
    st.subheader("Review")
    st.write("Audio:", getattr(st.session_state.get("audiofile"), "name", None))
    st.write("License:", getattr(st.session_state.get("licensefile"), "name", None))
    if st.button("Explore", type="primary"):
        st.session_state["step"] = "processing"
elif st.session_state["step"] == "processing":
    with st.spinner("Running analysis..."):
        time.sleep(1.5)
        st.session_state["transcriptionraw"] = "This is a sample transcription."
        st.session_state["analysisraw"] = "Analysis results: Good call quality."
        time.sleep(0.5)
        st.session_state["step"] = "result"
        st.experimental_rerun()
elif st.session_state["step"] == "result":
    st.subheader("Transcription Output")
    st.text(st.session_state.get("transcriptionraw",'No output or unable to read file'))
    st.download_button(
        label="Download Transcription Output",
        data=st.session_state.get("transcriptionraw",""),
        file_name="transcriptionoutput.txt",
        mime="text/plain"
    )
    st.subheader("Analysis Output")
    st.text(st.session_state.get("analysisraw",'No output or unable to read file'))
    st.download_button(
        label="Download Analysis Output",
        data=st.session_state.get("analysisraw",""),
        file_name="analysisoutput.txt",
        mime="text/plain"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run again"):
            for k in ["step","audiofile","licensefile","transcriptionraw","analysisraw"]:
                if k in st.session_state: del st.session_state[k]
            st.session_state["step"] = "landing"
            st.experimental_rerun()
    with col2:
        if st.button("Exit"):
            st.stop()

# --- Fixed Bottom-Left CTA ---
if st.session_state["step"] == "landing":
    st.markdown("""
        <div class='cta-fix'>
            <form action="" method="post"><button class="cta-btn" type="submit" name="action" value="start">Get started</button></form>
        </div>
        <script>
        const btn = document.querySelector("button[name='action']")
        if(btn){ btn.onclick = ()=>{ window.parent.postMessage({streamlitSetComponentValue: {step:'audio'}}, "*"); }; }
        </script>
    """, unsafe_allow_html=True)
    if st.button("Get started", key="real-get-started"):
        st.session_state["step"] = "audio"
        st.experimental_rerun()
