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

# Dummy user credentials
USERS = {
    "admin": {"password": "admin123", "name": "Administrator"},
    "user1": {"password": "user123", "name": "John Doe"},
    "analyst": {"password": "analyst123", "name": "Data Analyst"}
}

# Custom CSS for styling (including login page)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
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
    
    /* Login page specific styles */
    .login-container {
        max-width: 420px;
        margin: 8rem auto 0 auto;
        padding: 2.5rem;
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }
    
    .login-title {
        font-size: 2.25rem;
        font-weight: 800;
        background: linear-gradient(135deg, #dc2626 0%, #f87171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .login-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    /* Input field styling */
    .stTextInput input {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
    }
    
    .stTextInput input:focus {
        border-color: rgba(220, 38, 38, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.15) !important;
    }
    
    /* Upload card design */
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
    
    /* Button styling */
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
    }
    
    /* Stepper styling */
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
    
    /* Hero section */
    .hero-title {
        font-size: 3.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, #dc2626 0%, #f87171 50%, #dc2626 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
    
    /* Section headers */
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4rem;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 3px solid rgba(220, 38, 38, 0.35);
    }
    
    .column-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 1.75rem;
    }
    
    .faq-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4rem;
        margin-bottom: 2rem;
    }
    
    /* Info cards */
    .info-card {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.12) 0%, rgba(220, 38, 38, 0.06) 100%);
        border-left: 4px solid #dc2626;
        border-radius: 14px;
        padding: 1.75rem;
        margin: 1.75rem 0;
        backdrop-filter: blur(10px);
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
    }
    
    /* Benefit items */
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
        flex-shrink: 0;
    }
    
    .benefit-text {
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.65;
    }
    
    /* JSON viewer */
    .json-viewer {
        background: #1e293b;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 14px;
        padding: 1.75rem;
        max-height: 520px;
        overflow-y: auto;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.875rem;
        color: #86efac;
    }
    
    /* File uploader */
    .stFileUploader {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 14px;
        padding: 1.25rem;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    
    /* Expander */
    .stExpander {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 12px;
        margin-bottom: 1rem;
        transition: all 0.25s ease;
    }
    
    .stExpander:hover {
        background: rgba(30, 41, 59, 0.7);
        border-color: rgba(220, 38, 38, 0.25);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #f87171);
        border-radius: 10px;
    }
    
    /* Tabs */
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
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        color: white;
    }
    
    /* Messages */
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
    
    /* Responsive design */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .subtitle { font-size: 1rem; }
        .step { padding: 0.5rem 1rem; font-size: 0.8rem; }
        .login-container { margin-top: 4rem; padding: 2rem; }
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 14px; }
    ::-webkit-scrollbar-track { background: rgba(30, 41, 59, 0.4); border-radius: 8px; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #dc2626, #b91c1c); border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

def _init_state():
    """Initialize session state variables"""
    for k, v in {
        "authenticated": False,
        "username": None,
        "user_name": None,
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
                    "Question_no": question_key,
                    "agent_recorded": responses[0],
                    "ai_finding": responses[1],
                    "agent_asked": responses[2],
                    "symantic": responses[3]
                }
            else:
                row = {
                    "Section": section_key,
                    "Question_no": question_key,
                    "agent_recorded": responses[0] if len(responses) > 0 else "Not Available",
                    "ai_finding": responses[1] if len(responses) > 1 else "Not Available",
                    "agent_asked": responses[2] if len(responses) > 2 else "Not Available",
                    "symantic": responses[3] if len(responses) > 3 else "Not Available"
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
    col_logo, col_spacer, col_logout = st.columns([1, 3, 1])
    with col_logo:
        st.image('logo.png', width=150)
    with col_logout:
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_name = None
            st.session_state.step = "landing"
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# ==================== LOGIN PAGE ====================
if not st.session_state.authenticated:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">🎧 YBrantWorks</h1>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Conversation Intelligence Platform</p>', unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter your username", key="login_username")
    password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Login", use_container_width=True):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_name = USERS[username]["name"]
                st.success(f"Welcome, {USERS[username]['name']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display demo credentials
    st.markdown("---")
    with st.expander("📋 Demo Credentials"):
        st.markdown("""
        **Available Users:**
        - **admin** / admin123
        - **user1** / user123
        - **analyst** / analyst123
        """)

# ==================== MAIN APP (only if authenticated) ====================
elif st.session_state.authenticated:
    
    # ==================== LANDING PAGE ====================
    if st.session_state.step == "landing":
        _stepper()
        _display_logo()
        
        st.markdown(f'<p style="text-align: right; color: #94a3b8; font-size: 0.9rem;">Welcome, {st.session_state.user_name}!</p>', unsafe_allow_html=True)
        
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
            After recognizing the need for efficient audio conversation analysis in government and organizational surveys, we developed this platform to bridge the gap between raw audio data and actionable insights. This platform was created as an independent solution, performing direct audio transcription and intelligent analysis without relying on multiple third-party services.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<h2 class="section-title">Our Solution & Key Benefits</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<h3 class="column-title">Our Solution</h3>', unsafe_allow_html=True)
            st.markdown("""
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Complete independence from third-party APIs</div></div>
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Direct audio processing for accurate transcription</div></div>
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Intelligent context-aware analysis system</div></div>
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Speaker diarization capabilities</div></div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown('<h3 class="column-title">Key Benefits</h3>', unsafe_allow_html=True)
            st.markdown("""
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Stable API without dependencies</div></div>
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">JSON-based survey templates</div></div>
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Real-time processing</div></div>
            <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Hindi language support</div></div>
            """, unsafe_allow_html=True)
        
        st.markdown('<h2 class="faq-title">Frequently Asked Questions</h2>', unsafe_allow_html=True)
        
        with st.expander("How can organizations use this platform?"):
            st.markdown("Organizations can upload audio recordings of surveys with JSON configuration files for automatic transcription and analysis.")
        
        with st.expander("Can I customize survey questions?"):
            st.markdown("Yes! Two JSON configuration files allow custom questions, responses, and analysis parameters.")
        
        with st.expander("Does it work for long conversations?"):
            st.markdown("Absolutely. Handles short 2-3 minute calls to extended interviews with accurate timestamps.")
        
        with st.expander("How accurate is Hindi transcription?"):
            st.markdown("Uses advanced AI models trained for Hindi, including dialects and code-switching with English.")
    
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
    
    # ==================== JSON FILE 1 ====================
    elif st.session_state.step == "json1":
        _stepper()
        _display_logo()
        
        st.markdown('<h2 style="color: #f87171; font-weight: 700;">📄 Step 2: Upload JSON File 1</h2>', unsafe_allow_html=True)
        json_file_1 = st.file_uploader("Choose first JSON file", type=["json"], key="json1_uploader")
        
        if json_file_1:
            st.session_state.json_file_1 = json_file_1
            st.success(f"✅ JSON File 1: {json_file_1.name}")
            
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
    
    # ==================== JSON FILE 2 ====================
    elif st.session_state.step == "json2":
        _stepper()
        _display_logo()
        
        st.markdown('<h2 style="color: #f87171; font-weight: 700;">📄 Step 3: Upload JSON File 2</h2>', unsafe_allow_html=True)
        json_file_2 = st.file_uploader("Choose second JSON file", type=["json"], key="json2_uploader")
        
        if json_file_2:
            st.session_state.json_file_2 = json_file_2
            st.success(f"✅ JSON File 2: {json_file_2.name}")
            
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
    
    # ==================== READY ====================
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
            st.error(f"❌ Error: {str(e)}")
            if st.button("🔄 Try Again"):
                st.session_state.step = "ready"
                st.rerun()
    
    # ==================== RESULTS ====================
    elif st.session_state.step == "result":
        _stepper()
        _display_logo()
        
        st.markdown('<h2 style="color: #10b981; font-weight: 700;">📊 Results</h2>', unsafe_allow_html=True)
        
        st.markdown("### 🎵 Audio Playback")
        try:
            with open(st.session_state.audio_path, 'rb') as audio_file:
                st.audio(audio_file.read())
        except Exception as e:
            st.warning(f"Could not load audio: {str(e)}")
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📝 Transcription", "📈 Analysis"])
        
        with tab1:
            st.markdown("### Transcription Output")
            if st.session_state.transcription_raw:
                st.markdown('<div class="json-viewer">', unsafe_allow_html=True)
                st.json(st.session_state.transcription_raw)
                st.markdown('</div>', unsafe_allow_html=True)
                
                with open(st.session_state.transcription_path, "rb") as f:
                    st.download_button("⬇️ Download Transcription JSON", f.read(), "transcription.json", "application/json")
        
        with tab2:
            st.markdown("### Analysis Output")
            if st.session_state.analysis_raw:
                st.markdown('<div class="json-viewer">', unsafe_allow_html=True)
                st.json(st.session_state.analysis_raw)
                st.markdown('</div>', unsafe_allow_html=True)
                
                with open(st.session_state.analysis_path, "rb") as f:
                    st.download_button("⬇️ Download Analysis JSON", f.read(), "analysis.json", "application/json")
        
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
                
                def highlight_symantic(row):
                    colors = []
                    for col in matrix_df.columns:
                        if col == 'symantic':
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
                
                styled_df = matrix_df.style.apply(highlight_symantic, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)
                
                csv = matrix_df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 Download Matrix as CSV", csv, "matrix_output.csv", "text/csv", use_container_width=True, key="download_csv")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
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
