import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

# --- Premium Violet + Glow + Carousel + Animated Button ---
st.markdown("""
<style>
body, .stApp {
    background: radial-gradient(circle at 64% 40%, #A669FE 0%, #1B0038 82%) !important;
    min-height: 100vh;
}
.header-bg {
    background: linear-gradient(90deg, #7D64FF40 32%, #280040 98%);
    border-radius:30px;
    box-shadow:0 6px 22px #ab3bfd50, 0 1px 13px #a3121c14;
    margin-top:32px;margin-bottom:26px;padding:2rem 3rem 1.6rem 2.6rem;
}
.header-title {
    font-size:2.7rem;font-weight:950;color:#fff;letter-spacing:2px;
    font-family:'Inter','Segoe UI',Arial,sans-serif;
    margin-bottom:0.37em;text-shadow:0 3px 18px #b788ff98;
}
.header-caption {
    font-size:1.28em;color:#fcf8fe;opacity:0.9;font-weight:550;letter-spacing:0.44px;
    margin-bottom:0.85em;
}
.grid-steps {
    display:grid; grid-template-columns: 1fr 1fr; gap:2.4em 3.8em;
    margin:12px 0 24px 2em; justify-items:center; align-items:center;
}
.step-card {
    background: linear-gradient(95deg,#bc3370 54%,#a46afe 99%);
    box-shadow:0 2px 22px #9e55ff28;
    border-radius:22px;display:flex;flex-direction:column;align-items:center;justify-content:center;
    padding:1.45rem 1.9rem;font-size:1.18em; color:#fff; font-weight:700;letter-spacing:0.24px;
    border:2px solid #dc2626;min-width:210px; min-height:115px;position:relative;
}
.step-icon {font-size:2.5em;margin-bottom:0.13em;}
.step-arrow {
    font-size:2.13em;color:#efeffb;filter:drop-shadow(0 2px 8px #b674ff8f);
    position:absolute;right:-1.7em;top:50%;transform:translateY(-60%);}
#get-btn-row {position:fixed;left:36px;bottom:36px;z-index:100;}
#start-btn {
    background: linear-gradient(95deg,#dc2626,#a46afe 96%);
    color:#fff;font-size:1.32em;font-weight:700;padding:0.82em 2.2em;
    border-radius:2em;border:none;letter-spacing:1.18px;box-shadow: 0 0 44px #B233E740,0 8px 22px #c4281c59;
    transition:box-shadow 0.16s,outline 0.11s;outline:2.2px solid #ff296b0c;
    animation:fadebtn 1.6s infinite alternate; }
@keyframes fadebtn {from{box-shadow:0 0 16px #bb83f933,0 6px 15px #c4281c59;}to{box-shadow:0 0 60px #c264f966,0 16px 35px #c4281c99;}}
.carousel-area {
    position:absolute; top:126px; right:3vw;max-width:530px;min-width:314px;width:42vw;
    height:330px; border-radius:1.6em;box-shadow:0 0 60px #b674ff35;
    overflow:hidden; z-index:9;background:linear-gradient(90deg,#41028f44 42%,#511e8060 100%);}
.carousel-img {width:100%;height:100%;object-fit:cover;border-radius:1.6em;transition:all 0.5s;animation:kenburns 10s infinite alternate;}
@keyframes kenburns {0%{transform:scale(1.05);}100%{transform:scale(1.10);}}
header, .stToolbar, .stStatusWidget, .stDecoration {display:none!important;}
</style>
""", unsafe_allow_html=True)

CAROUSEL_IMAGES = ["slider1.jpg", "slider2.jpg", "slider3.jpg"] # Place your images here

def render_carousel(imgs, interval=5):
    import streamlit.components.v1 as components
    html = """
        <div class="carousel-area">
            <img id="carimg" class="carousel-img" src='%s'/>
        </div>
        <script>
        let imgs=%s;let idx=0;
        function showImg(){var c=document.getElementById('carimg');
        if(c)c.src=imgs[idx];idx=(idx+1)%%imgs.length;}
        setInterval(showImg,%d*1000);
        </script>
    """ % (imgs[0], json.dumps(imgs), interval)
    components.html(html, height=330)

def _init_state():
    for k,v in {
        "step":"landing","audio_file":None,"license_file":None,"audio_path":None,"license_path":None,
        "transcription_path":None,"analysis_path":None,"transcription_raw":None,"analysis_raw":None,
    }.items():
        if k not in st.session_state: st.session_state[k]=v
_init_state()

def _save_temp(uploaded_file,suffix:str)->Path:
    ext=Path(uploaded_file.name).suffix or suffix
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=ext)
    tmp.write(uploaded_file.getvalue()); tmp.flush(); tmp.close()
    return Path(tmp.name)

# --- Header panel ---
st.markdown(f"""
<div class="header-bg">
  <div class="header-title">ConvoCheck Intelligence</div>
  <div class="header-caption">Verify Every Voice, Unlock Every Insight <span style='font-size:1.37em;color:#fff4;margin-left:1.05em;'>&#9889;</span></div>
</div>
""", unsafe_allow_html=True)
render_carousel(CAROUSEL_IMAGES)

# --- Steps grid ---
steps_grid=[
    ("audio","📤","Upload audio"),
    ("license","🔑","Add Access key"),
    ("ready","📊","Explore Insight"),
    ("result","🎯","Result")
]
st.markdown("<div class='grid-steps'>",unsafe_allow_html=True)
for i,(key,icon,label) in enumerate(steps_grid):
    st.markdown(f"<div class='step-card'><span class='step-icon'>{icon}</span>{label}"+(f"<span class='step-arrow'>&#8594;</span>" if i%2==0 and i<len(steps_grid)-1 else "")+"</div>",unsafe_allow_html=True)
st.markdown("</div>",unsafe_allow_html=True)

# --- Main workflow logic ---
if st.session_state.step=="landing":
    st.markdown('<div class="step-card" style="font-size:1.17em;margin-top:25px;margin-left:18px;text-align:center;">Welcome — click <b>Get Started</b> at bottom to begin.</div>',unsafe_allow_html=True)
elif st.session_state.step=="audio":
    st.markdown('<div class="step-card"><span class="step-icon">📤</span>Upload conversation audio</div>',unsafe_allow_html=True)
    st.caption("Accepted formats: wav, mp3, m4a, aac, flac, ogg")
    audio=st.file_uploader("Choose audio file",type=["wav","mp3","m4a","aac","flac","ogg"],key="audio_upl")
    if audio: st.audio(audio)
    c1,c2=st.columns([0.28,0.72])
    with c1: st.button("← Back", on_click=lambda: st.session_state.update({"step":"landing"}))
    with c2:
        if audio and st.button("Continue ➝ Access key"):
            st.session_state.audio_file=audio
            st.session_state.audio_path=_save_temp(audio,".audio")
            st.session_state.step="license"
elif st.session_state.step=="license":
    st.markdown('<div class="step-card"><span class="step-icon">🔑</span>Upload license key</div>',unsafe_allow_html=True)
    st.caption("Accepted formats: txt, json, key, lic")
    keyf=st.file_uploader("Choose a license key file",type=["txt","json","key","lic"],key="lic_upl")
    c1,c2=st.columns([0.28,0.72])
    with c1: st.button("← Back", on_click=lambda: st.session_state.update({"step":"audio"}))
    with c2:
        if keyf and st.button("Continue ➝ Explore Insight"):
            st.session_state.license_file=keyf
            st.session_state.license_path=_save_temp(keyf,".lic")
            st.session_state.step="ready"
elif st.session_state.step=="ready":
    st.markdown('<div class="step-card"><span class="step-icon">📊</span>Review & Explore</div>',unsafe_allow_html=True)
    st.write({
        "audio":getattr(st.session_state.audio_file,"name",None),
        "license":getattr(st.session_state.license_file,"name",None)
    })
    if st.button("Explore",type="primary"):
        st.session_state.step="processing"
elif st.session_state.step=="processing":
    with st.spinner("Running analysis…"):
        try:
            t_path,a_path,t_content,a_content=run_pipeline(
                audio_path=Path(st.session_state.audio_path),
                license_path=Path(st.session_state.license_path),
            )
            st.session_state.transcription_path=t_path
            st.session_state.analysis_path=a_path
            try: st.session_state.transcription_raw=Path(t_path).read_text(encoding="utf-8")
            except: st.session_state.transcription_raw=""
            try: st.session_state.analysis_raw=Path(a_path).read_text(encoding="utf-8")
            except: st.session_state.analysis_raw=""
        except Exception: st.session_state.transcription_raw=""; st.session_state.analysis_raw=""
        time.sleep(0.3)
    st.session_state.step="result"
    st.rerun()
elif st.session_state.step=="result":
    st.markdown('<div class="step-card"><span class="step-icon">🎯</span>Result & Downloads</div>',unsafe_allow_html=True)
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
    c1,c2=st.columns(2)
    with c1:
        if st.button("Run again"):
            for k in [
                "step","audio_file","license_file","audio_path","license_path",
                "transcription_path","analysis_path","transcription_raw","analysis_raw"
            ]: 
                if k in st.session_state: del st.session_state[k]
            _init_state()
    with c2:
        if st.button("Exit"): st.stop()

# -- Get Started glowy button (bottom left, working logic) --
st.markdown("""
<div id='get-btn-row'>
    <form>
        <button id="start-btn" onclick="window.location.replace('?step=audio')">
            <span style="font-size:1.28em;">▶️</span> Get Started
        </button>
    </form>
</div>
""", unsafe_allow_html=True)
