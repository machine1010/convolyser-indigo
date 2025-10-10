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
        text-align: center;
        margin: 40px 0 20px 0;
        background: linear-gradient(90deg, #dc2626 0%, #ef4444 50%, #f87171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #d1d5db;
        margin-bottom: 30px;
        font-weight: 300;
    }
    
    .success-box {
        background: rgba(16, 185, 129, 0.1);
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .info-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        border: 1px solid rgba(220, 38, 38, 0.2);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(220, 38, 38, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #dc2626;
        margin: 40px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(220, 38, 38, 0.3);
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin: 30px 0;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid rgba(220, 38, 38, 0.2);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(220, 38, 38, 0.4);
        transform: translateY(-4px);
        box-shadow: 0 6px 16px rgba(220, 38, 38, 0.3);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 15px;
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ef4444;
        margin-bottom: 10px;
    }
    
    .feature-description {
        color: #d1d5db;
        line-height: 1.6;
    }
    
    .why-section {
        background: rgba(220, 38, 38, 0.1);
        border-left: 4px solid #dc2626;
        padding: 25px;
        border-radius: 8px;
        margin: 20px 0;
        color: #e5e7eb;
        line-height: 1.8;
    }
    
    .benefit-item {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
        border-left: 3px solid #dc2626;
        transition: all 0.3s ease;
    }
    
    .benefit-item:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(5px);
    }
    
    .benefit-title {
        font-weight: 600;
        color: #ef4444;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
    
    .tech-badge {
        display: inline-block;
        background: rgba(220, 38, 38, 0.2);
        color: #fca5a5;
        padding: 8px 16px;
        border-radius: 20px;
        margin: 5px;
        font-size: 0.9rem;
        border: 1px solid rgba(220, 38, 38, 0.3);
    }
    
    /* Logo and Company Name Styles */
    .logo-container {
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 15px;
        background: rgba(0, 0, 0, 0.3);
        padding: 10px 20px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(220, 38, 38, 0.3);
    }
    
    .logo-container img {
        height: 40px;
        width: auto;
    }
    
    .company-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    
    .company-name-highlight {
        color: #dc2626;
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

# ==================== LANDING PAGE ====================
if st.session_state.step == "landing":
    # Logo and Company Name in top-left corner
    st.markdown("""
    <div class="logo-container">
        <img src="https://via.placeholder.com/150x40/dc2626/ffffff?text=YBrantWorks" alt="Company Logo">
        <div class="company-name">
            <span class="company-name-highlight">YBrant</span>Works
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    benefits = [
        ("🎯 End-to-End Processing", "From raw audio to structured JSON insights in one seamless workflow"),
        ("🗣️ Hindi Language Expertise", "Specialized transcription and analysis optimized for Hindi conversations"),
        ("📊 Structured Output", "Generates organized JSON files with scores, summaries, and detailed analysis"),
        ("⚡ Real-Time Processing", "Fast turnaround for time-sensitive political and survey data"),
        ("🔒 Data Privacy", "Secure processing with full control over sensitive conversation data"),
        ("📈 Scalability", "Handle multiple audio files efficiently for large-scale survey projects")
    ]
    
    for title, desc in benefits:
        st.markdown(f"""
        <div class="benefit-item">
            <div class="benefit-title">{title}</div>
            <div class="feature-description">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Section 3: How It Works
    st.markdown('<h2 class="section-title">How It Works</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🎤</div>
            <div class="feature-title">1. Upload Audio</div>
            <div class="feature-description">
                Upload your Hindi conversation audio file in supported formats (MP3, WAV, etc.)
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📝</div>
            <div class="feature-title">2. Configure Analysis</div>
            <div class="feature-description">
                Provide two JSON configuration files that define transcription and analysis parameters
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">3. AI Processing</div>
            <div class="feature-description">
                Our AI engine transcribes the audio and performs intelligent analysis based on your configurations
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">4. Get Results</div>
            <div class="feature-description">
                Receive structured transcription and analysis JSON files with scores, summaries, and insights
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Section 4: Key Features
    st.markdown('<h2 class="section-title">Key Features</h2>', unsafe_allow_html=True)
    
    features = [
        ("🎯 Question Quality Analysis", "Evaluates the quality of questions asked during conversations"),
        ("✅ Answer Verification", "Validates and scores the accuracy of responses provided"),
        ("📊 Structured JSON Output", "Generates organized data files ready for further analysis"),
        ("🔍 Detailed Transcription", "Accurate speech-to-text conversion with speaker identification"),
        ("💡 Intelligent Insights", "Extracts key themes, sentiments, and actionable insights"),
        ("⚙️ Customizable Configuration", "Flexible JSON-based configuration for different analysis needs")
    ]
    
    cols = st.columns(2)
    for idx, (title, desc) in enumerate(features):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="info-card">
                <div class="feature-title">{title}</div>
                <div class="feature-description">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Section 5: Technology Stack
    st.markdown('<h2 class="section-title">Technology Stack</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <span class="tech-badge">🐍 Python</span>
        <span class="tech-badge">🤖 OpenAI GPT</span>
        <span class="tech-badge">🎙️ Whisper AI</span>
        <span class="tech-badge">🚀 Streamlit</span>
        <span class="tech-badge">📊 JSON Processing</span>
        <span class="tech-badge">🗣️ Hindi NLP</span>
        <span class="tech-badge">☁️ Cloud Ready</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Section 6: Use Cases
    st.markdown('<h2 class="section-title">Ideal Use Cases</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🗳️</div>
            <div class="feature-title">Political Surveys</div>
            <div class="feature-description">
                Analyze voter opinions and feedback from campaign conversations
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">🏛️</div>
            <div class="feature-title">Government Feedback</div>
            <div class="feature-description">
                Process citizen feedback and public consultation sessions
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📞</div>
            <div class="feature-title">Call Center Analysis</div>
            <div class="feature-description">
                Quality assessment of customer service interactions
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <div class="feature-title">Research Interviews</div>
            <div class="feature-description">
                Transcribe and analyze qualitative research conversations
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<p style="text-align: center; color: #9ca3af; margin-top: 40px;">© 2025 YBrantWorks • Powered by Advanced AI Technologies</p>', unsafe_allow_html=True)

# ==================== AUDIO UPLOAD ====================
elif st.session_state.step == "audio":
    _stepper()
    st.markdown('<h2 class="section-title">📁 Upload Audio File</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <p>Upload your Hindi conversation audio file. Supported formats: MP3, WAV, M4A, FLAC</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "flac"],
        key="audio_uploader"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()
    with col2:
        if uploaded is not None:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.audio_file = uploaded
                st.session_state.audio_path = _save_temp(uploaded, ".mp3")
                st.session_state.step = "json1"
                st.rerun()
    
    if uploaded:
        st.success("✅ Audio file loaded successfully!")
        st.audio(uploaded)

# ==================== JSON FILE 1 ====================
elif st.session_state.step == "json1":
    _stepper()
    st.markdown('<h2 class="section-title">📄 Upload JSON Configuration File 1</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <p>Upload the first JSON configuration file that defines transcription parameters.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose JSON file 1",
        type=["json"],
        key="json1_uploader"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "audio"
            st.rerun()
    with col2:
        if uploaded is not None:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.json_file_1 = uploaded
                st.session_state.json_path_1 = _save_temp(uploaded, ".json")
                st.session_state.step = "json2"
                st.rerun()
    
    if uploaded:
        st.success("✅ JSON file 1 loaded successfully!")
        try:
            data = json.loads(uploaded.getvalue().decode("utf-8"))
            st.json(data)
        except Exception as e:
            st.error(f"❌ Error parsing JSON: {e}")

# ==================== JSON FILE 2 ====================
elif st.session_state.step == "json2":
    _stepper()
    st.markdown('<h2 class="section-title">📄 Upload JSON Configuration File 2</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <p>Upload the second JSON configuration file that defines analysis parameters.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose JSON file 2",
        type=["json"],
        key="json2_uploader"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "json1"
            st.rerun()
    with col2:
        if uploaded is not None:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.json_file_2 = uploaded
                st.session_state.json_path_2 = _save_temp(uploaded, ".json")
                st.session_state.step = "ready"
                st.rerun()
    
    if uploaded:
        st.success("✅ JSON file 2 loaded successfully!")
        try:
            data = json.loads(uploaded.getvalue().decode("utf-8"))
            st.json(data)
        except Exception as e:
            st.error(f"❌ Error parsing JSON: {e}")

# ==================== READY TO PROCESS ====================
elif st.session_state.step == "ready":
    _stepper()
    st.markdown('<h2 class="section-title">🚀 Ready to Process</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="success-box">
        <h3 style="color: #10b981; margin-top: 0;">✅ All Files Uploaded Successfully!</h3>
        <p>Your audio file and configuration files are ready for processing.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="info-card">
            <h4 style="color: #ef4444;">📁 Uploaded Files:</h4>
            <ul style="color: #d1d5db;">
                <li>✅ Audio File</li>
                <li>✅ JSON Configuration 1</li>
                <li>✅ JSON Configuration 2</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <h4 style="color: #ef4444;">⚙️ Processing Steps:</h4>
            <ul style="color: #d1d5db;">
                <li>🎙️ Audio Transcription</li>
                <li>🤖 AI Analysis</li>
                <li>📊 Results Generation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "json2"
            st.rerun()
    with col2:
        if st.button("🚀 Start Processing", use_container_width=True, type="primary"):
            st.session_state.step = "processing"
            st.rerun()

# ==================== PROCESSING ====================
elif st.session_state.step == "processing":
    _stepper()
    st.markdown('<h2 class="section-title">⚙️ Processing Your Audio</h2>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    stages = [
        ("🎙️ Transcribing audio...", 0.2),
        ("🔍 Analyzing conversation...", 0.5),
        ("📊 Generating insights...", 0.8),
        ("✅ Finalizing results...", 1.0)
    ]
    
    for stage_text, progress in stages:
        status_text.markdown(f'<p style="text-align: center; color: #ef4444; font-size: 1.2rem;">{stage_text}</p>', unsafe_allow_html=True)
        progress_bar.progress(progress)
        time.sleep(0.5)
    
    # Run the actual pipeline
    try:
        transcription_file, analysis_file = run_pipeline(
            str(st.session_state.audio_path),
            str(st.session_state.json_path_1),
            str(st.session_state.json_path_2)
        )
        
        st.session_state.transcription_path = transcription_file
        st.session_state.analysis_path = analysis_file
        
        # Load the results
        with open(transcription_file, 'r', encoding='utf-8') as f:
            st.session_state.transcription_raw = json.load(f)
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            st.session_state.analysis_raw = json.load(f)
        
        st.success("✅ Processing complete!")
        time.sleep(1)
        st.session_state.step = "result"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        if st.button("🔄 Try Again"):
            st.session_state.step = "ready"
            st.rerun()

# ==================== RESULTS ====================
elif st.session_state.step == "result":
    _stepper()
    st.markdown('<h2 class="section-title">📊 Processing Results</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="success-box">
        <h3 style="color: #10b981; margin-top: 0;">✅ Processing Completed Successfully!</h3>
        <p>Your audio has been transcribed and analyzed. Explore the results below.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Transcription", "📊 Analysis"])
    
    with tab1:
        st.markdown('<h3 class="feature-title">Transcription Results</h3>', unsafe_allow_html=True)
        
        if st.session_state.transcription_raw:
            st.json(st.session_state.transcription_raw)
            
            # Download button
            st.download_button(
                label="⬇️ Download Transcription JSON",
                data=json.dumps(st.session_state.transcription_raw, indent=2, ensure_ascii=False),
                file_name="transcription.json",
                mime="application/json"
            )
    
    with tab2:
        st.markdown('<h3 class="feature-title">Analysis Results</h3>', unsafe_allow_html=True)
        
        if st.session_state.analysis_raw:
            st.json(st.session_state.analysis_raw)
            
            # Download button
            st.download_button(
                label="⬇️ Download Analysis JSON",
                data=json.dumps(st.session_state.analysis_raw, indent=2, ensure_ascii=False),
                file_name="analysis.json",
                mime="application/json"
            )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process Another File", use_container_width=True):
            # Reset session state
            for k in ["audio_file", "json_file_1", "json_file_2", "audio_path", 
                     "json_path_1", "json_path_2", "transcription_path", 
                     "analysis_path", "transcription_raw", "analysis_raw"]:
                st.session_state[k] = None
            st.session_state.step = "landing"
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()
