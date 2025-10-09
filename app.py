import json
import time
import tempfile
from pathlib import Path

import streamlit as st
from dummy_processor import run_pipeline

# ----- Violet Theme CSS -----
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(180deg, #6C3DD6 0%, #08001A 100%);
    color: #ece6fa;
    min-height: 100vh;
}
.stApp { font-family: 'Inter', Arial, sans-serif;}
.step-box {
    background: linear-gradient(93deg,#dc2626 65%,#6c3dd620 100%);
    border-radius: 18px;
    padding: 1.3rem 1.1rem;
    color: #fff;
    font-size: 1.05rem;
    box-shadow: 0 2px 14px 0 rgba(140,40,89,0.15);
    border: 2px solid #b91c1c;
    display: flex; align-items: center;
}
.step-symbol { font-size:2em; margin-right:0.6em;}
.step-separator { margin: 0 0.7em; font-size:1.6em; color:#fff8;}
.get-started-row {
    position:fixed; left:32px; bottom:24px; z-index:100;
}
.slider-container {
    position:absolute; top:62px; right:3vw; width:44vw; min-width:290px; max-width:540px;
    height:340px; z-index:10; border-radius:1.5rem; overflow:hidden;
    background:rgba(90,22,168,0.14); box-shadow:0 0 60px 0 rgba(67,24,115,0.12);
}
.slider-img {
    object-fit:cover; width:100%; height:100%; border-radius:1.4rem; transition:all 0.6s;
}
.header-bar { display:flex;align-items:center; padding:2rem 1.7rem 0.8rem 2rem;}
.brand-logo { height:48px; border-radius:10px; margin-right:16px;}
.header-title { font-weight:700; font-size:2.18rem; letter-spacing:1px; color:#f6f0fd; margin-bottom:0.1rem;}
.header-caption { font-size:1.03rem; color:#d9ccf1; opacity:0.85; font-weight:400; margin-bottom:1.3rem;}
header, .stToolbar, .stStatusWidget, .stDecoration {display:none !important;}
</style>
""", unsafe_allow_html=True)

# ----- Slider Images and JS -----
SLIDER_IMAGES = ["slider1.jpg","slider2.jpg","slider3.jpg"]

def render_slider(img_list, interval=3):
    import streamlit.components.v1 as components
    slider_html = """
    <div id="slider" class='slider-container'>
      <img id="slideimg" class='slider-img' src='%s'/>
    </div>
    <script>
    let imgs = %s;
    let idx = 0;
    function showImg() {
      let slideimg = document.getElementById('slideimg');
      if (slideimg) slideimg.src = imgs[idx];
      idx = (idx + 1) %% imgs.length;
    }
    setInterval(showImg, %d*1000);
    </script>
    """ % (img_list[0], json.dumps(img_list), interval)
    components.html(slider_html, height=340)

# ----- Session State -----
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

def _save_temp(uploaded_file, suffix: str) -> Path:
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush(); tmp.close()
    return Path(tmp.name)

# ----- Header -----
st.markdown(
    "<div class='header-bar'>"
    "<img src='https://ybrantworks.com/logo-dark.png' class='brand-logo'/>"
    "<div><div class='header-title'>ConvoCheck Intelligence</div>"
    "<div class='header-caption'>Verify Every Voice, Unlock Every Insight</div></div></div>",
    unsafe_allow_html=True
)
render_slider(SLIDER_IMAGES)

# ----- Steps -----
steps = [
    ("audio","📤","Upload audio"),
    ("license","🔑","Add Access key"),
    ("ready","📊","Explore Insight"),
    ("result","🎯","Result")
]
step_boxes = ""
for i, (_, icon, label) in enumerate(steps):
    step_boxes += f"<div class='step-box'><span class='step-symbol'>{icon}</span>{label}</div>"
    if i < len(steps)-1:
        step_boxes += "<span class='step-separator'>&#x276D;</span>"
st.markdown(f"<div style='display:flex;flex-wrap:wrap;align-items:center;margin-bottom:14px;'>{step_boxes}</div>", unsafe_allow_html=True)

# ----- Step UI -----
if st.session_state.step == "landing":
    st.markdown('<div class="step-box" style="margin-top:24px;">Welcome — click “Get started” to begin.</div>', unsafe_allow_html=True)

elif st.session_state.step == "audio":
    st.markdown('<div class="step-box"><span class="step-symbol">📤</span>Upload conversation audio</div>', unsafe_allow_html=True)
    st.caption("Accepted formats: wav, mp3, m4a, aac, flac, ogg")
    audio = st.file_uploader("Choose an audio file", type=["wav","mp3","m4a","aac","flac","ogg"], key="audio_upl")
    if audio: st.audio(audio)
    c1, c2 = st.columns([0.2, 0.8])
    with c1:
        st.button("Back", on_click=lambda: st.session_state.update({"step":"landing"}))
    with c2:
        if audio and st.button("Continue ➝ Access key"):
            st.session_state.audio_file = audio
            st.session_state.audio_path = _save_temp(audio, ".audio")
            st.session_state.step = "license"

elif st.session_state.step == "license":
    st.markdown('<div class="step-box"><span class="step-symbol">🔑</span>Upload license key</div>', unsafe_allow_html=True)
    st.caption("Accepted formats: txt, json, key, lic")
    keyf = st.file_uploader("Choose a license key file", type=["txt","json","key","lic"], key="lic_upl")
    c1, c2 = st.columns([0.2, 0.8])
    with c1:
        st.button("Back", on_click=lambda: st.session_state.update({"step":"audio"}))
    with c2:
        if keyf and st.button("Continue ➝ Explore Insight"):
            st.session_state.license_file = keyf
            st.session_state.license_path = _save_temp(keyf, ".lic")
            st.session_state.step = "ready"

elif st.session_state.step == "ready":
    st.markdown('<div class="step-box"><span class="step-symbol">📊</span>Review & Explore</div>', unsafe_allow_html=True)
    st.write({
        "audio": getattr(st.session_state.audio_file, "name", None),
        "license": getattr(st.session_state.license_file, "name", None),
    })
    if st.button("Explore", type="primary"):
        st.session_state.step = "processing"

elif st.session_state.step == "processing":
    with st.spinner("Running analysis…"):
        try:
            t_path, a_path, t_content, a_content = run_pipeline(
                audio_path=Path(st.session_state.audio_path),
                license_path=Path(st.session_state.license_path),
            )
            st.session_state.transcription_path = t_path
            st.session_state.analysis_path = a_path
            try:
                st.session_state.transcription_raw = Path(t_path).read_text(encoding="utf-8")
            except Exception:
                st.session_state.transcription_raw = ""
            try:
                st.session_state.analysis_raw = Path(a_path).read_text(encoding="utf-8")
            except Exception:
                st.session_state.analysis_raw = ""
        except Exception as e:
            st.session_state.transcription_raw = ""
            st.session_state.analysis_raw = ""
        time.sleep(0.3)
    st.session_state.step = "result"
    st.rerun()

elif st.session_state.step == "result":
    st.markdown('<div class="step-box"><span class="step-symbol">🎯</span>Result: Download output files below</div>', unsafe_allow_html=True)
    st.download_button(
        "Download Transcription Output",
        data=st.session_state.transcription_raw or "",
        file_name="transcription_output.txt",
        mime="text/plain",
    )
    st.download_button(
        "Download Analysis Output",
        data=st.session_state.analysis_raw or "",
        file_name="analysis_output.txt",
        mime="text/plain",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Run again"):
            for k in [
                "step","audio_file","license_file","audio_path","license_path",
                "transcription_path","analysis_path","transcription_raw","analysis_raw"
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            _init_state()
    with c2:
        if st.button("Exit"):
            st.stop()

# Get Started button
st.markdown("""
<div class='get-started-row'>
    <form>
        <button type="button" style="
        background: linear-gradient(95deg,#dc2626,#b91c1c);
        color:#fff;font-size:1.2em;font-weight:700;
        padding:0.7em 2em;border-radius:1.2em;
        box-shadow:0 10px 24px 0 rgba(140,40,89,0.20);
        border:none;
        " onclick="window.location.replace('?step=audio')">Get Started</button>
    </form>
</div>
""", unsafe_allow_html=True)
