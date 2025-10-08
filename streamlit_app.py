# app.py
import json
import time
import tempfile
from pathlib import Path

import streamlit as st
from dummy_processor import run_pipeline

st.set_page_config(page_title="Data App", page_icon="✨", layout="wide")

# ---------- Styles to mimic a simple hero ----------
HERO_CSS = """
<style>
.hero {
  text-align: center;
  padding: 4rem 1rem 2rem 1rem;
}
.hero h1 {
  font-size: 3rem;
  line-height: 1.1;
  margin-bottom: 0.75rem;
}
.hero p {
  color: #6b7280;
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
}
.hero .btn {
  display: inline-block;
  background: #ef4444;
  color: white;
  padding: 0.75rem 1.25rem;
  border-radius: 0.5rem;
  margin: 0 0.5rem;
  text-decoration: none;
  font-weight: 600;
}
.hero .btn.secondary {
  background: #111827;
}
.card {
  background: #ecfdf5;
  border-radius: 0.75rem;
  padding: 1rem;
}
</style>
"""
st.markdown(HERO_CSS, unsafe_allow_html=True)

# ---------- Session State ----------
def init_state():
    defaults = {
        "step": "landing",      # landing -> audio -> license -> ready -> processing -> result
        "audio_file": None,
        "license_file": None,
        "audio_path": None,
        "license_path": None,
        "result_path": None,
        "result_obj": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def reset_all():
    for k in list(st.session_state.keys()):
        if k in ("step", "audio_file", "license_file", "audio_path", "license_path", "result_path", "result_obj"):
            del st.session_state[k]
    init_state()

def save_to_temp(uploaded_file: "UploadedFile", suffix: str) -> Path:
    # Persist in-memory upload to a real temp file to get an OS path.
    # Determine suffix by provided arg or fall back to original name.
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

# ---------- UI Flow ----------
if st.session_state.step == "landing":
    st.markdown(
        """
        <div class="hero">
          <h1>A faster way to build and share data apps</h1>
          <p>Turn Python scripts into a simple app flow in minutes — no front‑end work required.</p>
          <a class="btn" href="#" onclick="window.parent.postMessage({type:'streamlit:setStep', step:'audio'}, '*'); return false;">Get started</a>
          <a class="btn secondary" href="#" onclick="return false;">Try the live playground</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Handle the JS anchor by exposing a small listener.
    st.write("")  # spacer

    # Fallback server-side button for environments where JS is restricted.
    if st.button("Get started"):
        st.session_state.step = "audio"

elif st.session_state.step == "audio":
    st.header("1) Upload conversation audio")
    st.caption("Accepted: wav, mp3, m4a, aac, flac, ogg")
    audio = st.file_uploader(
        "Choose an audio file", type=["wav", "mp3", "m4a", "aac", "flac", "ogg"], key="audio_uploader"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state.step = "landing"
    with col2:
        if audio is not None:
            st.audio(audio)
            if st.button("Continue"):
                st.session_state.audio_file = audio
                st.session_state.audio_path = save_to_temp(audio, ".audio")
                st.session_state.step = "license"

elif st.session_state.step == "license":
    st.header("2) Upload license key file")
    st.caption("Accepted: txt, json, key, lic")
    keyf = st.file_uploader(
        "Choose a license key file", type=["txt", "json", "key", "lic"], key="license_uploader"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state.step = "audio"
    with col2:
        if keyf is not None:
            if st.button("Continue"):
                st.session_state.license_file = keyf
                st.session_state.license_path = save_to_temp(keyf, ".lic")
                st.session_state.step = "ready"

elif st.session_state.step == "ready":
    st.header("3) Review and explore")
    with st.container():
        st.markdown("#### Selected files")
        st.write(
            {
                "audio": getattr(st.session_state.audio_file, "name", None),
                "license": getattr(st.session_state.license_file, "name", None),
            }
        )
    if st.button("Explore"):
        st.session_state.step = "processing"

elif st.session_state.step == "processing":
    st.header("Running analysis…")
    with st.spinner("Please wait while the processor generates results"):
        # Call the dummy backend.
        result_path = run_pipeline(
            audio_path=Path(st.session_state.audio_path),
            license_path=Path(st.session_state.license_path),
        )
        st.session_state.result_path = str(result_path)
        # Load JSON for display.
        try:
            st.session_state.result_obj = json.loads(Path(result_path).read_text())
        except Exception:
            st.session_state.result_obj = {"error": "Failed to read JSON result.", "path": str(result_path)}
        time.sleep(0.3)
    st.session_state.step = "result"
    st.rerun()

elif st.session_state.step == "result":
    st.header("Result")
    if st.session_state.result_obj is not None:
        st.json(st.session_state.result_obj, expanded=2)
        st.download_button(
            "Download JSON",
            data=json.dumps(st.session_state.result_obj, indent=2),
            file_name="result.json",
            mime="application/json",
        )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run again"):
            reset_all()
            st.session_state.step = "landing"
    with col2:
        if st.button("Exit"):
            st.stop()

# Small JS hook to make the hero anchor button advance the step.
st.markdown(
    """
    <script>
    window.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'streamlit:setStep') {
        const step = event.data.step;
        const s = window.parent.streamlitDocSend;
        if (s) s({type: 'streamlit:setComponentValue', args: {step}});
      }
    });
    </script>
    """,
    unsafe_allow_html=True,
)
# Also handle the synthetic component message via query param fallback.
if "_component_value" in st.query_params and "step" in st.query_params["_component_value"]:
    st.session_state.step = st.query_params["_component_value"]["step"]
