import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

# -- VIOLET FANCY THEME AND GLOWING BUTTON CSS --
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(155deg, #8C37FE 0%, #0B0038 50%, #1B014A 100%);
    color: #ededf6; min-height: 100vh;
}
.stepper-box {
    display: flex; align-items: center; gap:0.6em; margin-bottom: 1.6em; margin-top:1.0em;
    justify-content: flex-start; flex-wrap: wrap;
}
.step-box-fancy {
    background: linear-gradient(95deg,#DC2626 77%,rgba(150,50,185,0.90) 100%);
    box-shadow: 0 4px 24px #ab3bfd40, 0 1px 10px #a3121c20;
    border-radius: 26px; color: #fff; font-size: 1.16rem; font-weight: 600;
    border: 2px solid #b91c1c; 
    padding: 1.0em 1.5em;
    min-width: 140px;
    display: flex; align-items: center;
    letter-spacing: 0.2px;
    position: relative;
    z-index: 11;
    transition: box-shadow 0.17s;
}
.step-box-fancy:after {
    content:'';
    display:block;
    position: absolute; inset:0;
    border-radius: 26px; z-index:-1;
    box-shadow: 0 2px 48px #a959ff40;
}
.step-symbol { font-size:2.3em; margin-right:0.75em; filter:drop-shadow(0 2px 8px #511e80C0);}
.step-separator {
    font-size: 2.1em; color: #c083fa; margin: 0 0.5em 0 0.5em; user-select: none;
    padding-bottom: 0.1em;
}
.header-bar {
    display: flex; align-items: center;
    padding: 2.1rem 2.2rem 0.8rem 2.2rem;
    background: linear-gradient(90deg,#35063c70 42%, transparent 100%);
    border-radius: 0 0 52px 0;
    margin-bottom: 0.7em;
}
.brand-logo {
    height: 60px; border-radius: 20px; margin-right: 20px;
    box-shadow: 0 8px 24px #c55efd38;
}
.header-title {
    font-weight: 800; font-size: 2.48rem; letter-spacing: 2px;
    color: #fff; margin-bottom: 0.17rem; font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    text-shadow:0 2px 12px #9d6afe66;
}
.header-caption {
    font-size: 1.14rem; color: #c3b6fa; opacity: 1.0; margin-top:0.1rem; margin-bottom: 1.55rem;
    font-weight: 400; letter-spacing: 0.4px;
}
.carousel-shade {
    position: absolute;
    right:0; top:88px;
    width:45vw; min-width:304px; max-width:700px;
    height:390px; z-index:5;
    border-radius:2.1em;
    background: linear-gradient(88deg,#3a1659a0 6%, #b56bff22 50%, #472ca20d 100%);
    box-shadow: 0 0 90px 0 #b674ff22, 0 9px 94px 10px #9631dc15;
}
.slider-container {
    position:absolute; top:95px; right:2vw;
    width:45vw; min-width:304px; max-width:700px;
    height:390px; z-index:18; border-radius:2.1em; overflow:hidden;
    background: rgba(104,34,177,0.12);
    box-shadow:0 0 70px 0 #b774ff22, 0 9px 85px 10px #7e0ddf18;
    display:flex; align-items:center; justify-content:center;
}
.slider-img {
    width:100%; height:100%; object-fit:cover; border-radius:2em; transition:all 0.5s;
    animation: kenburns 12s infinite alternate; box-shadow: 0 12px 40px #b083fa32;
}
@keyframes kenburns {
    0% { transform: scale(1) translateY(0); }
    100% { transform: scale(1.05) translateY(-12px);}
}
.get-started-row {
    position:fixed; left:32px; bottom:32px; z-index:150;
}
.glow-btn {
    background: radial-gradient(#a1fdff33, #dc2626 96%, #340231 100%);
    color:#fff;font-size:1.22em;font-weight:800;
    padding:0.82em 2.2em;border-radius:2.3em;
    border:none;
    letter-spacing:1.2px;
    box-shadow: 0 0 30px #b233e740, 0 8px 22px #a3121c49;
    transition: box-shadow 0.18s, outline 0.12s;
    outline: 2.2px solid #ff296b0c;
    animation: breathglow 2.1s infinite alternate;
}
.glow-btn:hover, .glow-btn:focus {
    box-shadow: 0 0 80px #ff3be799, 0 6px 36px #a3121c80;
    background: radial-gradient(#e83f9533, #9d14e6 96%, #41126a 100%);
    outline: 2.6px solid #c238ff5c;
}
@keyframes breathglow {
    from { box-shadow:0 0 20px #cb83f933, 0 8px 20px #a3121c49;}
    to   { box-shadow:0 0 55px #c264f966, 0 18px 38px #c3125c80;}
}
/* Hide default Streamlit UI */
header, .stToolbar, .stStatusWidget, .stDecoration {display:none !important;}
</style>
""", unsafe_allow_html=True)

SLIDER_IMAGES = ["slider1.jpg", "slider2.jpg", "slider3.jpg"] # Supply your actual image paths!

def render_slider(img_list, interval=5):
    import streamlit.components.v1 as components
    slider_html = """
    <div id="slider" class='slider-container'>
      <img id="slideimg" class='slider-img' src='%s'/>
    </div>
    <script>
    let imgs = %s; let idx = 0;
    function showImg() {
      let slideimg = document.getElementById('slideimg');
      if (slideimg) slideimg.src = imgs[idx];
      idx = (idx+1) %% imgs.length;
    }
    setInterval(showImg, %d*1000);
    </script>
    """ % (img_list[0], json.dumps(img_list), interval)
    components.html(slider_html, height=390)

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
    tmp.write(uploaded_file.getvalue()); tmp.flush(); tmp.close()
    return Path(tmp.name)

# --- HEADER DESIGN ---
st.markdown(
    "<div class='header-bar'>"
    "<img src='https://ybrantworks.com/logo-dark.png' class='brand-logo'/>"
    "<div><div class='header-title'>ConvoCheck Intelligence</div>"
    "<div class='header-caption'>Verify Every Voice, Unlock Every Insight <span style='font-size:1.24rem;color:#ffffff70;margin-left:0.7em;'>⚡️</span></div></div></div>",
    unsafe_allow_html=True
)
st.markdown("<div class='carousel-shade'></div>", unsafe_allow_html=True)
render_slider(SLIDER_IMAGES)

# --- STEPPER DESIGN ---
steps = [
    ("audio", "📤","Upload audio"),
    ("license", "🔑","Add Access key"),
    ("ready", "📊","Explore Insight"),
    ("result", "🎯","Result")
]
step_markup = ""
for i, (_, icon, label) in enumerate(steps):
    step_markup += f"<div class='step-box-fancy'><span class='step-symbol'>{icon}</span>{label}</div>"
    if i < len(steps)-1:
        step_markup += "<span class='step-separator'>&#x27A1;</span>"
st.markdown(f"<div class='stepper-box'>{step_markup}</div>", unsafe_allow_html=True)

# --- MAIN UI STEPS ---
if st.session_state.step == "landing":
    st.markdown('<div class="step-box-fancy" style="margin-top:24px;text-align:center;">Welcome — click “Get started” (below) to begin.</div>', unsafe_allow_html=True)

elif st.session_state.step == "audio":
    st.markdown('<div class="step-box-fancy"><span class="step-symbol">📤</span>Upload conversation audio</div>', unsafe_allow_html=True)
    st.caption("Accepted formats: wav, mp3, m4a, aac, flac, ogg")
    audio = st.file_uploader("Choose an audio file", type=["wav","mp3","m4a","aac","flac","ogg"], key="audio_upl")
    if audio: st.audio(audio)
    c1, c2 = st.columns([0.22, 0.78])
    with c1:
        st.button("← Back", on_click=lambda: st.session_state.update({"step":"landing"}))
    with c2:
        if audio and st.button("Continue ➝ Access key"):
            st.session_state.audio_file = audio
            st.session_state.audio_path = _save_temp(audio, ".audio")
            st.session_state.step = "license"

elif st.session_state.step == "license":
    st.markdown('<div class="step-box-fancy"><span class="step-symbol">🔑</span>Upload license key</div>', unsafe_allow_html=True)
    st.caption("Accepted formats: txt, json, key, lic")
    keyf = st.file_uploader("Choose a license key file", type=["txt","json","key","lic"], key="lic_upl")
    c1, c2 = st.columns([0.22, 0.78])
    with c1:
        st.button("← Back", on_click=lambda: st.session_state.update({"step":"audio"}))
    with c2:
        if keyf and st.button("Continue ➝ Explore Insight"):
            st.session_state.license_file = keyf
            st.session_state.license_path = _save_temp(keyf, ".lic")
            st.session_state.step = "ready"

elif st.session_state.step == "ready":
    st.markdown('<div class="step-box-fancy"><span class="step-symbol">📊</span>Review & Explore</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="step-box-fancy"><span class="step-symbol">🎯</span>Result & Downloads</div>', unsafe_allow_html=True)
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

# --- BEAUTIFUL FLOATING "GET STARTED" BUTTON (bottom-left) ---
st.markdown("""
<div class='get-started-row'>
    <button class="glow-btn" onclick="window.location.replace('?step=audio')">
        <span style="font-size:1.3em;vertical-align:middle;">▶️</span>
        &nbsp;Get Started
    </button>
</div>
""", unsafe_allow_html=True)
