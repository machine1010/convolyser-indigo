import json
import time
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd
from dummy_processor import run_pipeline

st.set_page_config(
    page_title="YBrantWorks • Conversation Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Modern UX-focused CSS with industry standards
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Base styles with better typography */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #f1f5f9;
        padding: 1rem 2rem;
    }
    
    /* Modern glassmorphic card design */
    .upload-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .upload-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        border-color: rgba(220, 38, 38, 0.4);
    }
    
    /* Enhanced button design */
    .stButton>button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.75rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
        letter-spacing: 0.02em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%);
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.5);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    .stDownloadButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.35);
    }
    
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.45);
    }
    
    /* Modern stepper with better visual feedback */
    .stepper-container {
        text-align: center;
        padding: 2.5rem 0 3rem 0;
        margin-bottom: 1.5rem;
    }
    
    .step {
        display: inline-block;
        padding: 0.7rem 1.4rem;
        margin: 0 0.6rem;
        border-radius: 28px;
        background: rgba(51, 65, 85, 0.5);
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(148, 163, 184, 0.15);
    }
    
    .step.active {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        box-shadow: 0 6px 16px rgba(220, 38, 38, 0.45);
        border-color: rgba(220, 38, 38, 0.6);
        transform: scale(1.08);
    }
    
    /* Hero section with better hierarchy */
    .hero-title {
        font-size: 3.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, #dc2626 0%, #f87171 50%, #dc2626 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1.25rem;
        letter-spacing: -0.025em;
        line-height: 1.1;
    }
    
    .subtitle {
        text-align: center;
        color: #cbd5e1;
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 3rem;
        line-height: 1.7;
        max-width: 44rem;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Section headers with better spacing */
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4rem;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 3px solid rgba(220, 38, 38, 0.35);
        letter-spacing: -0.02em;
    }
    
    .faq-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4rem;
        margin-bottom: 2rem;
    }
    
    .column-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 1.75rem;
    }
    
    /* Info cards with glassmorphism */
    .info-card {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.12) 0%, rgba(220, 38, 38, 0.06) 100%);
        border-left: 4px solid #dc2626;
        border-radius: 14px;
        padding: 1.75rem;
        margin: 1.75rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .why-section {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.12) 0%, rgba(29, 78, 216, 0.06) 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 14px;
        padding: 2rem;
        margin: 2rem 0;
        color: #e2e8f0;
        font-size: 1.05rem;
        line-height: 1.8;
        backdrop-filter: blur(10px);
    }
    
    /* Feature items with hover effects */
    .benefit-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.25rem;
        padding: 0.75rem;
        border-radius: 10px;
        transition: all 0.25s ease;
    }
    
    .benefit-item:hover {
        background: rgba(30, 41, 59, 0.4);
        transform: translateX(5px);
    }
    
    .benefit-icon {
        color: #10b981;
        font-size: 1.3rem;
        margin-top: 2px;
        flex-shrink: 0;
    }
    
    .benefit-text {
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.65;
    }
    
    /* JSON viewer with better contrast */
    .json-viewer {
        background: #1e293b;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 14px;
        padding: 1.75rem;
        max-height: 520px;
        overflow-y: auto;
        font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
        font-size: 0.875rem;
        color: #86efac;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.25);
    }
    
    /* File uploader improvements */
    .stFileUploader {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 14px;
        padding: 1.25rem;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    
    /* Expander with better feedback */
    .stExpander {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 12px;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: all 0.25s ease;
    }
    
    .stExpander:hover {
        background: rgba(30, 41, 59, 0.7);
        border-color: rgba(220, 38, 38, 0.25);
        transform: translateY(-1px);
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #f87171, #dc2626);
        border-radius: 10px;
        height: 10px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.25rem;
        background: rgba(30, 41, 59, 0.4);
        padding: 0.75rem;
        border-radius: 14px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.85rem 1.75rem;
        font-weight: 500;
        transition: all 0.25s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        color: white;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(16, 185, 129, 0.15);
        border-left: 4px solid #10b981;
        border-radius: 10px;
        padding: 1.25rem;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.15);
        border-left: 4px solid #ef4444;
        border-radius: 10px;
        padding: 1.25rem;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.15);
        border-left: 4px solid #f59e0b;
        border-radius: 10px;
        padding: 1.25rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        .subtitle {
            font-size: 1rem;
        }
        .step {
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
            margin: 0.25rem;
        }
        .main {
            padding: 1rem;
        }
    }
    
    /* Smooth scrollbar */
    ::-webkit-scrollbar {
        width: 14px;
        height: 14px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        border-radius: 8px;
        border: 2px solid rgba(30, 41, 59, 0.4);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #b91c1c, #991b1b);
    }
    
    /* Audio player styling */
    audio {
        width: 100%;
        border-radius: 12px;
        outline: none;
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
        "show_matrix": False,
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

def _generate_matrix_table(analysis_json):
    """Generate a matrix table from the analysis JSON output"""
    table_rows = []
    for section_key, section_data in analysis_json.items():
        if section_key == "summary":
            continue
        questions = section_data
        for question_key, responses in questions.items():
            if len(responses) >= 4:
                row = {
                    "Section": section_key,
                    "Question": question_key,
                    "Response 1": responses[0],
                    "Response 2": responses[1],
                    "Response 3": responses[2],
                    "Response 4": responses[3]
                }
            else:
                row = {
                    "Section": section_key,
                    "Question": question_key,
                    "Response 1": responses[0] if len(responses) > 0 else "Not Available",
                    "Response 2": responses[1] if len(responses) > 1 else "Not Available",
                    "Response 3": responses[2] if len(responses) > 2 else "Not Available",
                    "Response 4": responses[3] if len(responses) > 3 else "Not Available"
                }
            table_rows.append(row)
    df = pd.DataFrame(table_rows)
    return df

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
    st.markdown(f'<div class="stepper-container">{"".join(chips)}</div>', unsafe_allow_html=True)

def _display_logo():
    """Display logo on every page"""
    col_logo, col_spacer = st.columns([1, 4])
    with col_logo:
        st.image('logo.png', width=150)
    st.markdown("<br>", unsafe_allow_html=True)

# ==================== LANDING PAGE ====================
if st.session_state.step == "landing":
    _stepper()
    _display_logo()
    
    st.markdown('<h1 class="hero-title">🎧 Conversation Intelligence Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transform audio conversations into actionable insights with AI-powered transcription and analysis</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.step = "audio"
            st.rerun()
    
    st.markdown('<h2 class="section-title">Why We Created This Platform</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="why-section">
        After recognizing the need for efficient audio conversation analysis in government and organizational surveys, we developed this platform to bridge the gap between raw audio data and actionable insights. This platform was created as an independent solution, performing direct audio transcription and intelligent analysis without relying on multiple third-party services. Our goal is to provide accurate, detailed, and structured insights from Hindi language conversations, particularly for political surveys and citizen engagement initiatives.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-title">Our Solution & Key Benefits</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3 class="column-title">Our Solution</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Complete independence from third-party APIs and their limitations</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Direct audio processing for accurate and detailed transcription results</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Intelligent analysis system with context-aware question extraction</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Speaker diarization to identify and separate multiple speakers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<h3 class="column-title">Key Benefits</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Stable and reliable API without external dependencies</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Configurable JSON-based survey question templates</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Real-time processing with instant downloadable outputs</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-icon">✓</div>
            <div class="benefit-text">Support for Hindi language conversations with cultural context understanding</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="faq-title">Frequently Asked Questions</h2>', unsafe_allow_html=True)
    
    with st.expander("How can organizations use this platform for survey analysis?"):
        st.markdown("""Organizations can upload audio recordings of telephone surveys or field interviews along with their custom JSON configuration files. 
        The platform automatically transcribes the conversation, performs speaker diarization, and extracts specific answers to predefined survey questions. 
        This significantly reduces manual data entry time and improves accuracy in capturing survey responses.""")
    
    with st.expander("Can I customize the survey questions and analysis parameters?"):
        st.markdown("""Yes! The platform accepts two JSON configuration files that allow you to define custom survey questions, response options, and analysis parameters. 
        This makes it highly flexible for different types of surveys, whether political, social, or organizational research. 
        You can adapt the question sets to match your specific research needs.""")
    
    with st.expander("Does the platform work for long-form conversations?"):
        st.markdown("""Absolutely. The platform is designed to handle conversations of varying lengths, from short 2-3 minute calls to extended interviews. 
        The transcription engine accurately captures timestamps for each speaker segment, and the analysis module can process comprehensive conversations 
        while extracting relevant information across the entire audio duration.""")
    
    with st.expander("How accurate is the Hindi language transcription and analysis?"):
        st.markdown("""The platform uses advanced AI models specifically trained for Hindi language understanding, including various dialects and regional variations. 
        It can handle conversational Hindi with high accuracy, including code-switching between Hindi and English. 
        The analysis engine understands contextual meanings and can match responses to predefined options even when respondents use colloquial or varied phrasing.""")
    
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==================== AUDIO UPLOAD ====================
elif st.session_state.step == "audio":
    _stepper()
    _display_logo()
    
    st.markdown('<h2 style="color: #f87171; font-weight: 700;">📁 Step 1: Upload Audio File</h2>', unsafe_allow_html=True)
    st.markdown("Upload your audio file (supported formats: MP3, WAV, M4A, etc.)")
    
    audio_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg", "flac"], key="audio_uploader")
    
    if audio_file:
        st.session_state.audio_file = audio_file
        st.success(f"✅ Audio file uploaded: {audio_file.name}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Back"):
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
    _display_logo()
    
    st.markdown('<h2 style="color: #f87171; font-weight: 700;">📄 Step 2: Upload JSON File 1</h2>', unsafe_allow_html=True)
    st.markdown("Upload the first JSON configuration file")
    
    json_file_1 = st.file_uploader("Choose first JSON file", type=["json"], key="json1_uploader")
    
    if json_file_1:
        st.session_state.json_file_1 = json_file_1
        st.success(f"✅ JSON File 1 uploaded: {json_file_1.name}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Back"):
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
    _display_logo()
    
    st.markdown('<h2 style="color: #f87171; font-weight: 700;">📄 Step 3: Upload JSON File 2</h2>', unsafe_allow_html=True)
    st.markdown("Upload the second JSON configuration file")
    
    json_file_2 = st.file_uploader("Choose second JSON file", type=["json"], key="json2_uploader")
    
    if json_file_2:
        st.session_state.json_file_2 = json_file_2
        st.success(f"✅ JSON File 2 uploaded: {json_file_2.name}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step = "json1"
                st.rerun()
        with col2:
            if st.button("Process All Files ➡️", use_container_width=True):
                st.session_state.json_path_2 = _save_temp(json_file_2, ".json")
                st.session_state.step = "ready"
                st.rerun()

# ==================== READY TO PROCESS ====================
elif st.session_state.step == "ready":
    _stepper()
    _display_logo()
    
    st.markdown('<h2 style="color: #10b981; font-weight: 700;">✅ Ready to Process</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("**Files uploaded successfully:**")
    st.markdown(f"- 🎵 Audio: {st.session_state.audio_file.name if st.session_state.audio_file else 'N/A'}")
    st.markdown(f"- 📄 JSON File 1: {st.session_state.json_file_1.name if st.session_state.json_file_1 else 'N/A'}")
    st.markdown(f"- 📄 JSON File 2: {st.session_state.json_file_2.name if st.session_state.json_file_2 else 'N/A'}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = "json2"
            st.rerun()
    with col2:
        if st.button("🚀 Start Processing", use_container_width=True):
            st.session_state.step = "processing"
            st.rerun()

# ==================== PROCESSING ====================
elif st.session_state.step == "processing":
    _stepper()
    _display_logo()
    
    st.markdown('<h2 style="color: #f59e0b; font-weight: 700;">⚙️ Processing...</h2>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("📤 Uploading files...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        status_text.text("🔄 Running pipeline...")
        progress_bar.progress(40)
        
        transcription_path,_, final_path, transcription_raw, final_raw = run_pipeline(
            audio_path=st.session_state.audio_path,
            json_path_1=st.session_state.json_path_1,
            json_path_2=st.session_state.json_path_2
        )
        
        progress_bar.progress(80)
        status_text.text("✅ Processing complete!")
        
        st.session_state.transcription_path = transcription_path
        st.session_state.analysis_path = final_path
        st.session_state.transcription_raw = transcription_raw
        st.session_state.analysis_raw = final_raw
        
        progress_bar.progress(100)
        time.sleep(1)
        
        st.session_state.step = "result"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
        if st.button("🔄 Try Again"):
            st.session_state.step = "ready"
            st.rerun()

# ==================== RESULTS ====================
elif st.session_state.step == "result":
    _stepper()
    _display_logo()
    
    st.markdown('<h2 style="color: #10b981; font-weight: 700;">📊 Results</h2>', unsafe_allow_html=True)
    
    st.markdown("### 🎵 Audio Playback")
    st.markdown("Listen to the uploaded audio file:")
    try:
        with open(st.session_state.audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes)
    except Exception as e:
        st.warning(f"Could not load audio file: {str(e)}")
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📝 Transcription", "📈 Analysis"])
    
    with tab1:
        st.markdown("### Transcription Output")
        if st.session_state.transcription_raw:
            st.markdown('<div class="json-viewer">', unsafe_allow_html=True)
            st.json(st.session_state.transcription_raw)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with open(st.session_state.transcription_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Transcription JSON",
                    data=f.read(),
                    file_name="transcription.json",
                    mime="application/json"
                )
    
    with tab2:
        st.markdown("### Analysis Output")
        if st.session_state.analysis_raw:
            st.markdown('<div class="json-viewer">', unsafe_allow_html=True)
            st.json(st.session_state.analysis_raw)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with open(st.session_state.analysis_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Analysis JSON",
                    data=f.read(),
                    file_name="analysis.json",
                    mime="application/json"
                )
    
    st.markdown("---")
    
    if st.button("📊 Generate Matrix Table", use_container_width=True, key="matrix_btn"):
        st.session_state.show_matrix = True
    
    if st.session_state.show_matrix:
        st.markdown("### 📊 Matrix Output")
        st.markdown("---")
        
        try:
            with open(st.session_state.analysis_path, 'r', encoding='utf-8') as f:
                final_json = json.load(f)
            
            matrix_df = _generate_matrix_table(final_json)
            
            def highlight_response4(row):
                colors = []
                for col in matrix_df.columns:
                    if col == 'Response 4':
                        val = str(row[col]).lower()
                        if 'matched' == val:
                            colors.append('color: #10b981; font-weight: 600')
                        elif 'not matched' == val:
                            colors.append('color: #ef4444; font-weight: 600')
                        elif 'fuzzy match' == val:
                            colors.append('color: #f59e0b; font-weight: 600')
                        else:
                            colors.append('')
                    else:
                        colors.append('')
                return colors
            
            styled_df = matrix_df.style.apply(highlight_response4, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)
            
            csv = matrix_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download Matrix as CSV",
                data=csv,
                file_name="matrix_output.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_matrix_csv"
            )
            
        except Exception as e:
            st.error(f"Error generating matrix: {str(e)}")
            st.exception(e)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Process New Files", use_container_width=True):
            for key in ["audio_file", "json_file_1", "json_file_2", "audio_path", "json_path_1", "json_path_2",
                       "transcription_path", "analysis_path", "transcription_raw", "analysis_raw"]:
                st.session_state[key] = None
            st.session_state.step = "landing"
            st.rerun()
    
    with col2:
        if st.button("⬅️ Back to Ready", use_container_width=True):
            st.session_state.step = "ready"
            st.rerun()
