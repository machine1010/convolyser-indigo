import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

# --- Premium violet modern theme ---
st.markdown("""
<style>
body, .stApp {
    background: radial-gradient(circle at 68% 44%, #A669FE 0%, #2F0051 68%) !important;
    min-height: 100vh;
}
.header-box {
    margin-top:32px; margin-bottom:28px;
    background: linear-gradient(96deg, #617AFFe0 56%, #1B0038ea 100%);
    border-radius:28px;
    box-shadow:0 4px 24px #b783ff28, 0 1px 10px #31034a25;
    padding:2.2rem 2.7rem 2.1rem 2.7rem;
    text-align:left;
}
.header-title {
    font-size:2.8rem; font-weight:940; color:#fff;
    letter-spacing:2px; font-family:'Segoe UI', 'Inter', Arial,sans-serif;
    margin-bottom:0.42em;
    text-shadow:0 2px 14px #B695FF88;
}
.header-caption {
    font-size:1.3em;color:#fcf8fe;opacity:0.92;
    font-weight:500;letter-spacing:0.5px;margin-bottom:0.9em;
}
.step-grid {
    display:grid; grid-template-columns: 1fr 1fr; gap:2.6em 3.7em;
    margin-top:12px; margin-bottom:18px; justify-items:center; align-items:center;
}
.step-card {
    background: linear-gradient(96deg,#bc3370 52%,#a46afe 99%);
    box-shadow:0 2px 26px #9100de28, 0 1.5px 8px #ad0f44d1;
    border-radius:22px;display:flex;flex-direction:column;align-items:center;justify-content:center;
    padding:1.7rem 2.4rem; font-size:1.14em; color:#fff; font-weight:700;
    letter-spacing:0.3px; border:2px solid #dc2626;
    transition:box-shadow 0.18s;
    min-width:210px; min-height:118px;
    position:relative;
}
.step-icon {font-size:2.6em; margin-bottom:0.19em;}
.step-arrow {
    font-size:2.2em;color:#efeffb;filter:drop-shadow(0 1px 7px #b674ff88);
    position:absolute;right:-2.5em;top:48%
}
#get-btn-row {position:fixed;left:32px;bottom:36px;z-index:100;}
#start-btn {
    background: linear-gradient(95deg,#dc2626,#a46afe 96%);
    color:#fff;font-size:1.3em;font-weight:700;
    padding:0.82em 2.1em;border-radius:2em;border:none;
    letter-spacing:1.1px;
    box-shadow: 0 0 44px #B233E740,0 8px 22px #c4281c59;
    transition:box-shadow 0.16s,outline 0.11s;
    outline:2.2px solid #ff296b0c;
    animation:fadebtn 1.9s infinite alternate;
}
@keyframes fadebtn {
    from{box-shadow:0 0 22px #bb83f933,0 6px 18px #c4281c59;}
    to{box-shadow:0 0 60px #c264f966,0 16px 35px #c4281c99;}
}
.carousel-area {
    position:absolute; top:110px; right:2vw;
    max-width:530px; min-width:314px; width:42vw;
    height:340px;
    border-radius:1.7em;
    box-shadow:0 0 60px #b674ff35,0 9px 85px 10px #9631dc18;
    overflow:hidden;
    z-index:9;
    background:linear-gradient(90deg,#41028f44 55%,#511e8060 100%);
}
.carousel-img {
    width:100%; height:100%; object-fit:cover; border-radius:1.7em;
    transition:all 0.5s;
    animation:kenburns 10s infinite alternate;
}
@keyframes kenburns { 0%{transform:scale(1.05);}100%{transform:scale(1.11);}}
header, .stToolbar, .stStatusWidget, .stDecoration {display:none!important;}
</style>
""", unsafe_allow_html=True)

CAROUSEL_IMAGES = ["slider1.jpg","slider2.jpg","slider3.jpg"] # put your images here

def render_carousel(imgs, interval=4):
    import streamlit.components.v1 as components
    html = """
        <div class="carousel-area">
            <img id="carimg" class="carousel-img" src='%s'/>
        </div>
        <script>
        let imgs=%s;let idx=0;
        function showImg(){var c=document.getElementById('carimg');
        if(c)c.src=imgs[idx]; idx=(idx+1)%%imgs.length;}
        setInterval(showImg,%d*1000);
        </script>
    """ % (imgs[0], json.dumps(imgs), interval)
    components.html(html, height=340)

def _init_state():
    for k,v in {
        "step":"landing",
        "audio_file":None, "license_file":None,
        "audio_path":None, "license_path":None,
        "transcription_path":None, "analysis_path":None,
        "transcription_raw":None, "analysis_raw":None,
    }.items():
        if k not in st.session_state: st.session_state[k]=v
_init_state()

def _save_temp(uploaded_file,suffix:str)->Path:
    ext=Path(uploaded_file.name).suffix or suffix
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=ext)
    tmp.write(uploaded_file.getvalue()); tmp.flush(); tmp.close()
    return Path(tmp.name)

# --- header panel (like convolyser.ai) ---
st.markdown(f"""
<div class="header-box">
  <div class="header-title">ConvoCheck Intelligence</div>
  <div class="header-caption">Verify Every Voice, Unlock Every Insight <span style='font-size:1.4rem;color:#fff4;margin-left:0.95em;'>&#9889;</span></div>
</div>
""", unsafe_allow_html=True)
render_carousel(CAROUSEL_IMAGES)

# --- grid step cards, arrows between ---
steps_grid=[
    ("audio","📤","Upload audio"),
    ("license","🔑","Add Access key"),
    ("ready","📊","Explore Insight"),
    ("result","🎯","Result")
]
st.markdown("<div class='step-grid'>",unsafe_allow_html=True)
for i,(key,icon,label) in enumerate(steps_grid):
    st.markdown(
        f"<div class='step-card'><span class='step-icon'>{icon}</span>{label}"
        +(f"<span class='step-arrow'>&#8594;</span>" if i%2==0 and i<len(steps_grid)-1 else "")+"</div>",
        unsafe_allow_html=True
    )
st.markdown("</div>",unsafe_allow_html=True)

# --- main logic steps ---
if st.session_state.step=="landing":
    st.markdown('<div class="step-card" style="font-size:1.17em;margin-top:25px;margin-left:16px;text-align:center;">Welcome — click <b>Get Started</b> at bottom to begin.</div>',unsafe_allow_html=True)

elif st.session_state.step=="audio":
    st.markdown('<div class="step-card"><span class="step-icon">📤</span>Upload conversation audio</div>',unsafe_allow_html=True)
    st.caption("Accepted formats: wav, mp3, m4a, aac, flac, ogg")
    audio=st.file_uploader("Choose audio file",type=["wav","mp3","m4a","aac","flac","ogg"],key="audio_upl")
    if audio: st.audio(audio)
    c1,c2=st.columns([0.24,0.76])
    with c1:
        st.button("← Back", on_click=lambda: st.session_state.update({"step":"landing"}))
    with c2:
        if audio and st.button("Continue ➝ Access key"):
            st.session_state.audio_file=audio
            st.session_state.audio_path=_save_temp(audio,".audio")
            st.session_state.step="license"

elif st.session_state.step=="license":
    st.markdown('<div class="step-card"><span class="step-icon">🔑</span>Upload license key</div>',unsafe_allow_html=True)
    st.caption("Accepted formats: txt, json, key, lic")
    keyf=st.file_uploader("Choose a license key file",type=["txt","json","key","lic"],key="lic_upl")
    c1,c2=st.columns([0.24,0.76])
    with c1:
        st.button("← Back", on_click=lambda: st.session_state.update({"step":"audio"}))
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
        except Exception as e: 
            st.session_state.transcription_raw=""
            st.session_state.analysis_raw=""
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

# -- animated glowing Get Started button (bottom left, always accessible) --
st.markdown("""
<div id='get-btn-row'>
    <button id="start-btn" onclick="window.location.replace('?step=audio')">
        <span style="font-size:1.28em;">▶️</span> Get Started
    </button>
</div>
""", unsafe_allow_html=True)
