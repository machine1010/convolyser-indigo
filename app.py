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
        padding: 20px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 600;
        color: #dc2626;
        margin-top: 40px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .why-section, .solution-section, .use-cases-section {
        background: rgba(255, 255, 255, 0.05);
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        line-height: 1.8;
        color: #e5e7eb;
    }
    
    .use-case-item {
        background: rgba(220, 38, 38, 0.1);
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        border-left: 3px solid #dc2626;
    }
    
    .use-case-title {
        font-weight: 600;
        color: #ef4444;
        margin-bottom: 8px;
    }
    
    .logo-container {
        position: absolute;
        top: 10px;
        left: 20px;
        z-index: 999;
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


def _stepper():
    """Display progress stepper"""
    stages = ["landing", "audio", "json1", "json2", "ready", "processing", "result"]
    labels = ["Upload Audio", "JSON File 1", "JSON File 2", "Explore", "Result"]
    try:
        idx = max(1, min(5, stages.index(st.session_state.step)))
    except ValueError:
        idx = 1

    chips = []
    for i, lbl in enumerate(labels, 1):
        cls = "step active" if i <= idx else "step"
        chips.append(f'<span class="{cls}">{lbl}</span>')

    st.markdown(
        f'<div style="text-align: center; margin: 30px 0;">{"".join(chips)}</div>',
        unsafe_allow_html=True
    )


# ==================== MAIN FLOW ====================
if st.session_state.step == "landing":
    # Add logo/image in top-left corner
    logo_col, content_col = st.columns([1, 5])
    with logo_col:
        # Replace 'logo.png' with your actual image file path
        # You can use st.image() with a local file or URL
        try:
            st.image("logo.png", width=150)
        except:
            # Fallback if image not found - displays a placeholder
            st.markdown('<div class="logo-container">🎧</div>', unsafe_allow_html=True)
    
    with content_col:
        st.markdown("")  # Empty space for alignment
    
    st.markdown('<h1 class="hero-title">🎧 Conversation Intelligence Platform</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Upload an audio file, provide two JSON configuration files, then explore real‑time outputs — all on a polished red theme.</p>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.step = "audio"
            st.rerun()
    
    # ==================== NEW SECTIONS ====================
    
    # Section 1: Why We Created This Platform
    st.markdown('<h2 class="section-title">Why We Created This Platform</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="why-section">
        After recognizing the need for efficient audio conversation analysis in government and organizational surveys, we developed this platform to bridge the gap between raw audio data and actionable insights. This platform was created as an independent solution, performing direct audio transcription and intelligent analysis without relying on multiple third-party services. Our goal is to provide accurate, detailed, and structured insights from Hindi language conversations, particularly for political surveys and citizen engagement initiatives.
    </div>
    """, unsafe_allow_html=True)
    
    # Section 2: Our Solution & Key Benefits
    st.markdown('<h2 class="section-title">Our Solution & Key Benefits</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="solution-section">
        <p><strong>🎯 What We Offer:</strong></p>
        <ul style="line-height: 2;">
            <li><strong>Direct Audio Transcription:</strong> Convert Hindi audio recordings into accurate text transcripts</li>
            <li><strong>Intelligent Analysis:</strong> Extract meaningful insights, sentiment, and key themes from conversations</li>
            <li><strong>Structured Output:</strong> Receive analysis in organized JSON format for easy integration</li>
            <li><strong>Quality Scoring:</strong> Evaluate question quality and response accuracy automatically</li>
            <li><strong>Survey Insights:</strong> Generate actionable data points for decision-making</li>
        </ul>
        
        <p style="margin-top: 20px;"><strong>✨ Key Advantages:</strong></p>
        <ul style="line-height: 2;">
            <li>No dependency on multiple third-party services</li>
            <li>Optimized for Hindi language processing</li>
            <li>Designed specifically for political and social surveys</li>
            <li>Real-time processing with visual progress tracking</li>
            <li>Export-ready results in JSON format</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Section 3: Use Cases
    st.markdown('<h2 class="section-title">Use Cases & Applications</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="use-cases-section">
        <div class="use-case-item">
            <div class="use-case-title">🏛️ Political Campaigns & Surveys</div>
            <div>Analyze voter feedback, understand public sentiment, and track campaign effectiveness through structured conversation analysis.</div>
        </div>
        
        <div class="use-case-item">
            <div class="use-case-title">🏢 Government Citizen Engagement</div>
            <div>Process citizen feedback calls, complaints, and suggestions to improve public services and policy decisions.</div>
        </div>
        
        <div class="use-case-item">
            <div class="use-case-title">📊 Market Research</div>
            <div>Convert customer interviews and focus group discussions into actionable insights for product development and marketing strategies.</div>
        </div>
        
        <div class="use-case-item">
            <div class="use-case-title">🎓 Academic Research</div>
            <div>Transcribe and analyze qualitative research interviews for social science and behavioral studies.</div>
        </div>
        
        <div class="use-case-item">
            <div class="use-case-title">📞 Call Center Quality Assurance</div>
            <div>Evaluate call quality, agent performance, and customer satisfaction through automated conversation analysis.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #9ca3af; margin-top: 40px;">Built with ❤️ for meaningful conversations</p>',
        unsafe_allow_html=True
    )

elif st.session_state.step == "audio":
    _stepper()
    st.markdown('<h2 class="section-title">📁 Upload Audio File</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>ℹ️ Instructions:</strong><br>
        Upload an audio file (MP3, WAV, M4A, or OGG format). This will be transcribed and analyzed.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose audio file",
        type=["mp3", "wav", "m4a", "ogg"],
        help="Supported formats: MP3, WAV, M4A, OGG"
    )
    
    if uploaded:
        st.session_state.audio_file = uploaded
        st.session_state.audio_path = _save_temp(uploaded, ".mp3")
        st.success(f"✅ Uploaded: {uploaded.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = "landing"
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.step = "json1"
                st.rerun()
    else:
        if st.button("⬅️ Back to Home", use_container_width=False):
            st.session_state.step = "landing"
            st.rerun()

elif st.session_state.step == "json1":
    _stepper()
    st.markdown('<h2 class="section-title">📄 Upload JSON Configuration 1</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>ℹ️ Instructions:</strong><br>
        Upload the first JSON configuration file for transcription settings.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose first JSON file",
        type=["json"],
        key="json1_uploader"
    )
    
    if uploaded:
        st.session_state.json_file_1 = uploaded
        st.session_state.json_path_1 = _save_temp(uploaded, ".json")
        st.success(f"✅ Uploaded: {uploaded.name}")
        
        with st.expander("📋 Preview JSON Content"):
            try:
                content = json.loads(uploaded.getvalue().decode("utf-8"))
                st.json(content)
            except Exception as e:
                st.error(f"Error reading JSON: {e}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = "audio"
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.step = "json2"
                st.rerun()
    else:
        if st.button("⬅️ Back", use_container_width=False):
            st.session_state.step = "audio"
            st.rerun()

elif st.session_state.step == "json2":
    _stepper()
    st.markdown('<h2 class="section-title">📄 Upload JSON Configuration 2</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>ℹ️ Instructions:</strong><br>
        Upload the second JSON configuration file for analysis settings.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose second JSON file",
        type=["json"],
        key="json2_uploader"
    )
    
    if uploaded:
        st.session_state.json_file_2 = uploaded
        st.session_state.json_path_2 = _save_temp(uploaded, ".json")
        st.success(f"✅ Uploaded: {uploaded.name}")
        
        with st.expander("📋 Preview JSON Content"):
            try:
                content = json.loads(uploaded.getvalue().decode("utf-8"))
                st.json(content)
            except Exception as e:
                st.error(f"Error reading JSON: {e}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = "json1"
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.step = "ready"
                st.rerun()
    else:
        if st.button("⬅️ Back", use_container_width=False):
            st.session_state.step = "json1"
            st.rerun()

elif st.session_state.step == "ready":
    _stepper()
    st.markdown('<h2 class="section-title">🚀 Ready to Process</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>✅ All files uploaded successfully!</strong><br>
        Review your uploads below and click "Start Processing" when ready.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎵 Audio File")
        if st.session_state.audio_file:
            st.write(f"📁 {st.session_state.audio_file.name}")
            st.audio(st.session_state.audio_file)
    
    with col2:
        st.markdown("### 📄 JSON Config 1")
        if st.session_state.json_file_1:
            st.write(f"📁 {st.session_state.json_file_1.name}")
            if st.button("👁️ View", key="view_json1"):
                content = json.loads(st.session_state.json_file_1.getvalue().decode("utf-8"))
                st.json(content)
    
    with col3:
        st.markdown("### 📄 JSON Config 2")
        if st.session_state.json_file_2:
            st.write(f"📁 {st.session_state.json_file_2.name}")
            if st.button("👁️ View", key="view_json2"):
                content = json.loads(st.session_state.json_file_2.getvalue().decode("utf-8"))
                st.json(content)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "json2"
            st.rerun()
    with col2:
        if st.button("▶️ Start Processing", use_container_width=True):
            st.session_state.step = "processing"
            st.rerun()

elif st.session_state.step == "processing":
    _stepper()
    st.markdown('<h2 class="section-title">⚙️ Processing...</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>🔄 Processing your files...</strong><br>
        This may take a few moments. Please wait while we transcribe and analyze your audio.
    </div>
    """, unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Simulate processing stages
        status_text.text("📝 Stage 1/3: Transcribing audio...")
        progress_bar.progress(33)
        time.sleep(1)
        
        status_text.text("🔍 Stage 2/3: Analyzing content...")
        progress_bar.progress(66)
        time.sleep(1)
        
        status_text.text("✨ Stage 3/3: Generating insights...")
        progress_bar.progress(90)
        
        # Run the actual pipeline
        transcription_path, analysis_path = run_pipeline(
            audio_path=str(st.session_state.audio_path),
            json_path_1=str(st.session_state.json_path_1),
            json_path_2=str(st.session_state.json_path_2)
        )
        
        st.session_state.transcription_path = transcription_path
        st.session_state.analysis_path = analysis_path
        
        # Load results
        with open(transcription_path, "r", encoding="utf-8") as f:
            st.session_state.transcription_raw = f.read()
        
        with open(analysis_path, "r", encoding="utf-8") as f:
            st.session_state.analysis_raw = f.read()
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        time.sleep(1)
        
        st.session_state.step = "result"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during processing: {e}")
        if st.button("🔄 Try Again"):
            st.session_state.step = "ready"
            st.rerun()

elif st.session_state.step == "result":
    _stepper()
    st.markdown('<h2 class="section-title">📊 Results</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <strong>✅ Processing completed successfully!</strong><br>
        View your transcription and analysis results below. You can download the JSON files for further use.
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Transcription", "🔍 Analysis"])
    
    with tab1:
        st.markdown("### 📝 Transcription Output")
        
        if st.session_state.transcription_raw:
            try:
                trans_json = json.loads(st.session_state.transcription_raw)
                st.json(trans_json)
                
                st.download_button(
                    label="⬇️ Download Transcription JSON",
                    data=st.session_state.transcription_raw,
                    file_name="transcription.json",
                    mime="application/json",
                    use_container_width=True
                )
            except json.JSONDecodeError:
                st.markdown(f"``````")
        else:
            st.warning("No transcription data available")
    
    with tab2:
        st.markdown("### 🔍 Analysis Output")
        
        if st.session_state.analysis_raw:
            try:
                analysis_json = json.loads(st.session_state.analysis_raw)
                st.json(analysis_json)
                
                st.download_button(
                    label="⬇️ Download Analysis JSON",
                    data=st.session_state.analysis_raw,
                    file_name="analysis.json",
                    mime="application/json",
                    use_container_width=True
                )
            except json.JSONDecodeError:
                st.markdown(f"``````")
        else:
            st.warning("No analysis data available")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process Another", use_container_width=True):
            # Reset state
            for key in ["audio_file", "json_file_1", "json_file_2", "transcription_raw", "analysis_raw"]:
                st.session_state[key] = None
            st.session_state.step = "landing"
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()
