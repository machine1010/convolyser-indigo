import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummy_processor import run_pipeline

st.set_page_config(
    page_title="YBrantWorks • Conversation Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: #ffffff;
    }

    .stButton>button {
        background: linear-gradient(90deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(220, 38, 38, 0.3);
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #b91c1c 0%, #991b1b 100%);
        box-shadow: 0 6px 12px rgba(220, 38, 38, 0.5);
        transform: translateY(-2px);
    }

    .upload-section {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed #dc2626;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        transition: all 0.3s ease;
    }

    .upload-section:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: #ef4444;
    }

    .step {
        display: inline-block;
        padding: 8px 16px;
        margin: 0 8px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.1);
        color: #9ca3af;
        font-size: 14px;
        font-weight: 500;
    }

    .step.active {
        background: linear-gradient(90deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #dc2626 0%, #ef4444 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 20px;
    }

    .subtitle {
        text-align: center;
        color: #d1d5db;
        font-size: 1.2rem;
        margin-bottom: 40px;
    }

    .info-card {
        background: rgba(220, 38, 38, 0.1);
        border-left: 4px solid #dc2626;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
    }

    .file-preview-card {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.15), rgba(185, 28, 28, 0.1));
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .file-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ef4444;
        margin-bottom: 10px;
    }

    .file-size {
        font-size: 0.9rem;
        color: #9ca3af;
    }

    .audio-player-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid rgba(220, 38, 38, 0.2);
    }

    .success-badge {
        display: inline-block;
        background: rgba(5, 150, 105, 0.2);
        color: #10b981;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid rgba(5, 150, 105, 0.3);
    }

    .feature-badge {
        display: inline-block;
        background: rgba(220, 38, 38, 0.2);
        color: #ef4444;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 4px;
    }

    .stDownloadButton>button {
        background: linear-gradient(90deg, #059669 0%, #047857 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #047857 0%, #065f46 100%);
        transform: translateY(-2px);
    }

    .json-viewer {
        background: #1f2937;
        border-radius: 8px;
        padding: 15px;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def _init_state():
    """Initialize session state variables"""
    for k, v in {
        "step": "landing",
        "audio_file": None,
        "json_file_1": None,
        "json_file_2": None,
        "audio_path": None,
        "json_path_1": None,
        "json_path_2": None,
        "transcription_path": None,
        "analysis_path": None,
        "transcription_raw": None,
        "analysis_raw": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

def _save_temp(uploaded_file, suffix: str) -> Path:
    """Save uploaded file to temporary location"""
    ext = Path(uploaded_file.name).suffix or suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getvalue())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

def _format_file_size(bytes_size):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def _stepper():
    """Display progress stepper"""
    steps = [
        ("Audio", "audio"),
        ("JSON 1", "json1"),
        ("JSON 2", "json2"),
        ("Processing", "processing"),
        ("Results", "results"),
    ]
    current = st.session_state.step

    html_parts = ['<div style="text-align: center; margin: 30px 0;">']
    for label, step_id in steps:
        active_class = "active" if step_id == current else ""
        html_parts.append(f'<span class="step {active_class}">{label}</span>')
    html_parts.append('</div>')

    st.markdown("".join(html_parts), unsafe_allow_html=True)

# ==================== LANDING PAGE ====================
if st.session_state.step == "landing":
    _stepper()

    # Add logo at top left
    col_logo, col_spacer = st.columns([1, 4])
    with col_logo:
        st.markdown('<div style="margin: 10px 0 30px 0;">', unsafe_allow_html=True)
        # Uncomment and replace with your logo file
        # st.image('logo.png', width=150)
        st.markdown('<div style="background: linear-gradient(90deg, #dc2626, #ef4444); padding: 20px; border-radius: 12px; text-align: center; font-size: 1.5rem; font-weight: 700; color: white;">🎧 YBrant</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<h1 class="hero-title">🎧 Conversation Intelligence Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Upload an audio file, provide two JSON configuration files, then explore real‑time outputs — all on a polished red theme.</p>', unsafe_allow_html=True)

    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="info-card">
            <h3 style="color: #ef4444;">🎯 Smart Processing</h3>
            <p>Advanced AI-powered conversation analysis with real-time insights</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3 style="color: #ef4444;">⚡ Lightning Fast</h3>
            <p>Process audio files quickly with optimized transcription pipeline</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card">
            <h3 style="color: #ef4444;">📊 Rich Analytics</h3>
            <p>Comprehensive JSON outputs with detailed conversation metrics</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.step = "audio"
            st.rerun()

# ==================== AUDIO UPLOAD ====================
elif st.session_state.step == "audio":
    _stepper()

    st.markdown('<h2 style="color: #dc2626;">📁 Step 1: Upload Audio File</h2>', unsafe_allow_html=True)
    st.markdown("Upload your audio file for conversation analysis")

    # Supported formats as badges
    st.markdown("""
    <div style="margin: 15px 0;">
        <span class="feature-badge">MP3</span>
        <span class="feature-badge">WAV</span>
        <span class="feature-badge">M4A</span>
        <span class="feature-badge">OGG</span>
        <span class="feature-badge">FLAC</span>
    </div>
    """, unsafe_allow_html=True)

    audio_file = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "ogg", "flac"],
        key="audio_uploader"
    )

    if audio_file:
        st.session_state.audio_file = audio_file

        # File preview card with size
        file_size = _format_file_size(len(audio_file.getvalue()))
        st.markdown(f"""
        <div class="file-preview-card">
            <div class="file-name">📎 {audio_file.name}</div>
            <div class="file-size">Size: {file_size}</div>
            <span class="success-badge">✓ Upload Complete</span>
        </div>
        """, unsafe_allow_html=True)

        # Audio player with container
        st.markdown('<div class="audio-player-container">', unsafe_allow_html=True)
        st.markdown("#### 🎵 Audio Preview")
        st.audio(audio_file, format=f'audio/{audio_file.name.split(".")[-1]}')
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = "landing"
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.audio_path = _save_temp(audio_file, ".m4a")
                st.session_state.step = "json1"
                st.rerun()

# ==================== JSON FILE 1 UPLOAD ====================
elif st.session_state.step == "json1":
    _stepper()

    st.markdown('<h2 style="color: #dc2626;">📄 Step 2: Upload JSON File 1</h2>', unsafe_allow_html=True)
    st.markdown("Upload the first JSON configuration file")

    json_file_1 = st.file_uploader(
        "Choose first JSON file",
        type=["json"],
        key="json1_uploader"
    )

    if json_file_1:
        st.session_state.json_file_1 = json_file_1

        file_size = _format_file_size(len(json_file_1.getvalue()))
        st.markdown(f"""
        <div class="file-preview-card">
            <div class="file-name">📎 {json_file_1.name}</div>
            <div class="file-size">Size: {file_size}</div>
            <span class="success-badge">✓ Upload Complete</span>
        </div>
        """, unsafe_allow_html=True)

        # Preview JSON content
        with st.expander("👁️ Preview JSON Content"):
            try:
                json_content = json.loads(json_file_1.getvalue().decode("utf-8"))
                st.json(json_content)
            except:
                st.warning("Could not preview JSON content")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = "audio"
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.json_path_1 = _save_temp(json_file_1, ".json")
                st.session_state.step = "json2"
                st.rerun()

# ==================== JSON FILE 2 UPLOAD ====================
elif st.session_state.step == "json2":
    _stepper()

    st.markdown('<h2 style="color: #dc2626;">📄 Step 3: Upload JSON File 2</h2>', unsafe_allow_html=True)
    st.markdown("Upload the second JSON configuration file")

    json_file_2 = st.file_uploader(
        "Choose second JSON file",
        type=["json"],
        key="json2_uploader"
    )

    if json_file_2:
        st.session_state.json_file_2 = json_file_2

        file_size = _format_file_size(len(json_file_2.getvalue()))
        st.markdown(f"""
        <div class="file-preview-card">
            <div class="file-name">📎 {json_file_2.name}</div>
            <div class="file-size">Size: {file_size}</div>
            <span class="success-badge">✓ Upload Complete</span>
        </div>
        """, unsafe_allow_html=True)

        # Preview JSON content
        with st.expander("👁️ Preview JSON Content"):
            try:
                json_content = json.loads(json_file_2.getvalue().decode("utf-8"))
                st.json(json_content)
            except:
                st.warning("Could not preview JSON content")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = "json1"
                st.rerun()
        with col2:
            if st.button("Process All Files ➡️", use_container_width=True):
                st.session_state.json_path_2 = _save_temp(json_file_2, ".json")
                st.session_state.step = "processing"
                st.rerun()

# ==================== PROCESSING ====================
elif st.session_state.step == "processing":
    _stepper()

    st.markdown('<h2 style="color: #dc2626;">⚙️ Processing Files</h2>', unsafe_allow_html=True)

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Processing steps with progress updates
    status_text.text("🔄 Initializing pipeline...")
    progress_bar.progress(10)
    time.sleep(0.5)

    status_text.text("🎤 Transcribing audio...")
    progress_bar.progress(30)

    try:
        # Run the actual pipeline
        transcription_path, analysis_path = run_pipeline(
            audio_path=str(st.session_state.audio_path),
            json_path_1=str(st.session_state.json_path_1),
            json_path_2=str(st.session_state.json_path_2),
        )

        progress_bar.progress(70)
        status_text.text("🧠 Analyzing conversation...")
        time.sleep(0.5)

        progress_bar.progress(90)
        status_text.text("✅ Finalizing results...")

        # Store results in session state
        st.session_state.transcription_path = transcription_path
        st.session_state.analysis_path = analysis_path

        # Load JSON content for display
        with open(transcription_path, "r", encoding="utf-8") as f:
            st.session_state.transcription_raw = json.load(f)
        with open(analysis_path, "r", encoding="utf-8") as f:
            st.session_state.analysis_raw = json.load(f)

        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        time.sleep(1)

        st.session_state.step = "results"
        st.rerun()

    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        if st.button("🔄 Try Again"):
            st.session_state.step = "audio"
            st.rerun()

# ==================== RESULTS ====================
elif st.session_state.step == "results":
    _stepper()

    st.markdown('<h2 style="color: #dc2626;">📊 Results</h2>', unsafe_allow_html=True)
    st.success("✅ All files processed successfully!")

    # Summary cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="info-card">
            <h3 style="color: #ef4444;">📝 Transcription</h3>
            <p>Complete conversation transcript with timestamps</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3 style="color: #ef4444;">📈 Analysis</h3>
            <p>Detailed conversation insights and metrics</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Transcription section
    st.markdown("### 📝 Transcription Output")

    col1, col2 = st.columns([3, 1])
    with col1:
        with st.expander("👁️ View Transcription JSON", expanded=True):
            st.json(st.session_state.transcription_raw)
    with col2:
        st.download_button(
            label="📥 Download",
            data=json.dumps(st.session_state.transcription_raw, indent=2),
            file_name="transcription.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Analysis section
    st.markdown("### 📈 Analysis Output")

    col1, col2 = st.columns([3, 1])
    with col1:
        with st.expander("👁️ View Analysis JSON", expanded=True):
            st.json(st.session_state.analysis_raw)
    with col2:
        st.download_button(
            label="📥 Download",
            data=json.dumps(st.session_state.analysis_raw, indent=2),
            file_name="analysis.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Process Another File", use_container_width=True):
            # Reset session state
            for key in ["audio_file", "json_file_1", "json_file_2", "audio_path", 
                        "json_path_1", "json_path_2", "transcription_path", 
                        "analysis_path", "transcription_raw", "analysis_raw"]:
                st.session_state[key] = None
            st.session_state.step = "landing"
            st.rerun()
