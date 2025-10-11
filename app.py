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
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin: 20px 0;
        background: linear-gradient(90deg, #dc2626, #ef4444, #f87171);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: #d1d5db;
        margin-bottom: 30px;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 600;
        color: #dc2626;
        margin: 40px 0 20px 0;
        text-align: center;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        margin: 15px 0;
        border-left: 4px solid #dc2626;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(5px);
    }
    
    .why-section {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 30px;
        margin: 20px 0;
        line-height: 1.8;
        font-size: 1.1rem;
    }
    
    .logo-container {
        text-align: center;
        margin: 20px 0;
    }
    
    .logo-text {
        font-size: 2.5rem;
        font-weight: 700;
        color: #dc2626;
        letter-spacing: 2px;
    }
    
    .stProgress > div > div > div > div {
        background-color: #dc2626;
    }
    
    .success-box {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(22, 163, 74, 0.1) 100%);
        border: 2px solid #22c55e;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .info-box {
        background: rgba(59, 130, 246, 0.1);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .login-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 40px;
        margin: 50px auto;
        max-width: 500px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    
    .login-title {
        font-size: 2rem;
        font-weight: 600;
        text-align: center;
        color: #dc2626;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Dummy users database
DUMMY_USERS = {
    "admin": "admin123",
    "user1": "password1",
    "user2": "password2",
    "demo": "demo123"
}

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
        "logged_in": False,
        "username": None,
        "return_to_step": None,
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
    """
    Generate a matrix table from the analysis JSON output
    Args:
        analysis_json: The final output JSON with structure:
                      {section_key: {question_key: [agent_recorded, ai_finding, agent_asked, symantic]}}
    Returns:
        pandas DataFrame formatted as a table
    """
    table_rows = []
    
    # Iterate through sections
    for section_key, section_data in analysis_json.items():
        if section_key == "summary":
            continue
        
        # Get questions for this section
        questions = section_data
        
        for question_key, responses in questions.items():
            # responses is a list: [response1, response2, response3, response4]
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
                # Handle cases with fewer responses
                row = {
                    "Section": section_key,
                    "Question_no": question_key,
                    "agent_recorded": responses[0] if len(responses) > 0 else "Not Available",
                    "ai_finding": responses[1] if len(responses) > 1 else "Not Available",
                    "agent_asked": responses[2] if len(responses) > 2 else "Not Available",
                    "symantic": responses[3] if len(responses) > 3 else "Not Available"
                }
            
            table_rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(table_rows)
    return df

def _stepper():
    """Display progress stepper"""
    stages = ["landing", "login", "audio", "json1", "json2", "ready", "processing", "result"]
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
        f'<div style="text-align: center; margin: 30px 0;">{" ".join(chips)}</div>',
        unsafe_allow_html=True
    )

def _display_logo():
    """Display the logo"""
    st.markdown('<div class="logo-container"><div class="logo-text">YBrantWorks</div></div>', unsafe_allow_html=True)

def _login_page():
    """Display login page"""
    _display_logo()
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">🔐 Login</h2>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login_button = st.form_submit_button("Login", use_container_width=True)
        
        if login_button:
            if username in DUMMY_USERS and DUMMY_USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                # Redirect to the step they were trying to access
                if st.session_state.return_to_step:
                    st.session_state.step = st.session_state.return_to_step
                    st.session_state.return_to_step = None
                else:
                    st.session_state.step = "audio"
                st.success(f"Welcome {username}!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display available demo credentials
    st.markdown("---")
    st.markdown("### Demo Credentials")
    st.markdown("""
    - **admin** / admin123
    - **user1** / password1
    - **user2** / password2
    - **demo** / demo123
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ==================== LOGIN PAGE ====================
if st.session_state.step == "login":
    _login_page()

# ==================== LANDING PAGE ====================
elif st.session_state.step == "landing":
    _stepper()
    _display_logo()
    
    st.markdown('<h1 class="hero-title">🎧 SurveyScribe AI </h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle"> From Voice to Value with AI Insight </p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.return_to_step = "audio"
            st.session_state.step = "login"
            st.rerun()

    
    # ==================== NEW SECTIONS ====================
    
    # Section 1: Why We Created This Platform
    st.markdown('<h2 class="section-title"> The Story Behind Our Innovation </h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="why-section">
        This product was built to revolutionize the way telephone surveys are conducted by bringing the power
        of artificial intelligence to every conversation. Traditional survey processes are time-consuming, 
        error-prone, and difficult to analyze at scale. Our platform transforms raw audio conversations into 
        actionable insights, ensuring survey quality, compliance, and efficiency like never before.
        
        <br><br>
        
        We recognized that human oversight alone cannot guarantee the consistency and accuracy needed in modern
        survey operations. By leveraging advanced AI models, we empower organizations to validate survey 
        interactions, identify compliance issues, and extract valuable insights—all in real-time.
    </div>
    """, unsafe_allow_html=True)
    
    # Section 2: Key Features
    st.markdown('<h2 class="section-title"> What Makes Us Different </h2>', unsafe_allow_html=True)
    
    features = [
        ("🎯", "Automated Transcription", "Convert audio conversations to text with industry-leading accuracy using state-of-the-art speech recognition."),
        ("🔍", "Intelligent Analysis", "AI-powered evaluation of survey quality, agent performance, and response validation."),
        ("📊", "Comprehensive Reports", "Generate detailed compliance reports, performance metrics, and actionable insights."),
        ("⚡", "Real-Time Processing", "Process and analyze conversations in minutes, not hours or days."),
        ("🔒", "Secure & Compliant", "Enterprise-grade security with full GDPR and compliance standards."),
        ("🎨", "Intuitive Interface", "Beautiful, user-friendly design that makes complex analysis simple."),
    ]
    
    cols = st.columns(2)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="feature-card">
                <h3>{icon} {title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Section 3: How It Works
    st.markdown('<h2 class="section-title"> How It Works </h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>📝 Step 1: Upload Your Audio</h3>
        <p>Simply upload your telephone survey recording in any common audio format (MP3, WAV, etc.)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>📄 Step 2: Provide Survey Context</h3>
        <p>Upload your survey questionnaire and expected responses in JSON format for accurate validation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>🤖 Step 3: AI Processing</h3>
        <p>Our advanced AI models transcribe, analyze, and validate the conversation against your survey criteria.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>📊 Step 4: Review Results</h3>
        <p>Get comprehensive reports with transcription, analysis, compliance scores, and actionable insights.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Section 4: Use Cases
    st.markdown('<h2 class="section-title"> Who Can Benefit </h2>', unsafe_allow_html=True)
    
    use_cases = [
        ("🏢 Market Research Firms", "Ensure survey quality and compliance across thousands of interviews."),
        ("🏥 Healthcare Organizations", "Validate patient surveys and maintain regulatory compliance."),
        ("🏦 Financial Institutions", "Monitor customer service quality and adherence to protocols."),
        ("📞 Call Centers", "Improve agent performance and customer satisfaction tracking."),
        ("🎓 Academic Research", "Streamline qualitative research analysis and data collection."),
        ("🏛️ Government Agencies", "Ensure transparency and accuracy in public opinion surveys."),
    ]
    
    cols = st.columns(2)
    for i, (title, desc) in enumerate(use_cases):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="feature-card">
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Call to Action
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<h2 class="section-title"> Ready to Transform Your Survey Process? </h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Your First Analysis", use_container_width=True, key="cta_button"):
            st.session_state.return_to_step = "audio"
            st.session_state.step = "login"
            st.rerun()

# ==================== AUDIO UPLOAD ====================
elif st.session_state.step == "audio":
    if not st.session_state.logged_in:
        st.session_state.return_to_step = "audio"
        st.session_state.step = "login"
        st.rerun()
    
    _stepper()
    _display_logo()
    
    st.markdown(f'<h2 class="section-title">Welcome, {st.session_state.username}! 👋</h2>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">Step 1: Upload Audio File 🎵</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your Survey Audio Recording</h3>
        <p>Supported formats: MP3, WAV, M4A, FLAC</p>
    </div>
    """, unsafe_allow_html=True)
    
    audio = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "flac"],
        help="Upload the telephone survey recording you want to analyze"
    )
    
    if audio:
        st.session_state.audio_file = audio
        st.session_state.audio_path = _save_temp(audio, ".mp3")
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success(f"✅ Audio file '{audio.name}' uploaded successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 File size: {audio.size / 1024:.2f} KB")
        with col2:
            st.info(f"📝 File type: {audio.type}")
        
        st.audio(audio)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Next: Upload Survey JSON →", use_container_width=True):
                st.session_state.step = "json1"
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()

# ==================== JSON FILE 1 UPLOAD ====================
elif st.session_state.step == "json1":
    if not st.session_state.logged_in:
        st.session_state.return_to_step = "json1"
        st.session_state.step = "login"
        st.rerun()
    
    _stepper()
    _display_logo()
    
    st.markdown('<h2 class="section-title">Step 2: Upload Survey Questionnaire (JSON File 1) 📄</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-section">
        <h3>📋 Upload Your Survey Questions JSON</h3>
        <p>This file should contain the survey questionnaire structure and expected responses</p>
    </div>
    """, unsafe_allow_html=True)
    
    json1 = st.file_uploader(
        "Choose first JSON file",
        type=["json"],
        help="Upload the survey questionnaire JSON file",
        key="json1_uploader"
    )
    
    if json1:
        st.session_state.json_file_1 = json1
        st.session_state.json_path_1 = _save_temp(json1, ".json")
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success(f"✅ JSON file '{json1.name}' uploaded successfully!")
        
        try:
            json_data = json.loads(json1.getvalue().decode("utf-8"))
            st.json(json_data, expanded=False)
        except Exception as e:
            st.warning(f"⚠️ Could not preview JSON: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous Step", use_container_width=True):
                st.session_state.step = "audio"
                st.rerun()
        with col2:
            if st.button("Next: Upload Additional JSON →", use_container_width=True):
                st.session_state.step = "json2"
                st.rerun()
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Previous Step", use_container_width=True):
                st.session_state.step = "audio"
                st.rerun()

# ==================== JSON FILE 2 UPLOAD ====================
elif st.session_state.step == "json2":
    if not st.session_state.logged_in:
        st.session_state.return_to_step = "json2"
        st.session_state.step = "login"
        st.rerun()
    
    _stepper()
    _display_logo()
    
    st.markdown('<h2 class="section-title">Step 3: Upload Survey Responses (JSON File 2) 📄</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-section">
        <h3>📊 Upload Your Expected Survey Responses JSON</h3>
        <p>This file should contain the expected response patterns and validation criteria</p>
    </div>
    """, unsafe_allow_html=True)
    
    json2 = st.file_uploader(
        "Choose second JSON file",
        type=["json"],
        help="Upload the survey responses validation JSON file",
        key="json2_uploader"
    )
    
    if json2:
        st.session_state.json_file_2 = json2
        st.session_state.json_path_2 = _save_temp(json2, ".json")
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success(f"✅ JSON file '{json2.name}' uploaded successfully!")
        
        try:
            json_data = json.loads(json2.getvalue().decode("utf-8"))
            st.json(json_data, expanded=False)
        except Exception as e:
            st.warning(f"⚠️ Could not preview JSON: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous Step", use_container_width=True):
                st.session_state.step = "json1"
                st.rerun()
        with col2:
            if st.button("Next: Review & Process →", use_container_width=True):
                st.session_state.step = "ready"
                st.rerun()
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Previous Step", use_container_width=True):
                st.session_state.step = "json1"
                st.rerun()

# ==================== READY TO PROCESS ====================
elif st.session_state.step == "ready":
    if not st.session_state.logged_in:
        st.session_state.return_to_step = "ready"
        st.session_state.step = "login"
        st.rerun()
    
    _stepper()
    _display_logo()
    
    st.markdown('<h2 class="section-title">Step 4: Ready to Process 🚀</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>✅ All Files Uploaded Successfully!</h3>
        <p>Review your uploaded files below and click "Start Processing" to begin the AI analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎵 Audio File")
        if st.session_state.audio_file:
            st.success(f"✅ {st.session_state.audio_file.name}")
            st.audio(st.session_state.audio_file)
        else:
            st.error("❌ No audio file")
    
    with col2:
        st.markdown("### 📄 JSON File 1")
        if st.session_state.json_file_1:
            st.success(f"✅ {st.session_state.json_file_1.name}")
        else:
            st.error("❌ No JSON file 1")
    
    with col3:
        st.markdown("### 📄 JSON File 2")
        if st.session_state.json_file_2:
            st.success(f"✅ {st.session_state.json_file_2.name}")
        else:
            st.error("❌ No JSON file 2")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    all_ready = all([
        st.session_state.audio_path,
        st.session_state.json_path_1,
        st.session_state.json_path_2
    ])
    
    if all_ready:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous Step", use_container_width=True):
                st.session_state.step = "json2"
                st.rerun()
        with col2:
            if st.button("🚀 Start Processing", use_container_width=True):
                st.session_state.step = "processing"
                st.rerun()
    else:
        st.error("⚠️ Please upload all required files before processing")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Go Back", use_container_width=True):
                st.session_state.step = "audio"
                st.rerun()

# ==================== PROCESSING ====================
elif st.session_state.step == "processing":
    if not st.session_state.logged_in:
        st.session_state.return_to_step = "processing"
        st.session_state.step = "login"
        st.rerun()
    
    _stepper()
    _display_logo()
    
    st.markdown('<h2 class="section-title">Processing Your Survey... 🤖</h2>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Stage 1: Starting
        status_text.markdown("### 🎬 Initializing AI pipeline...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        # Stage 2: Transcribing
        status_text.markdown("### 🎤 Transcribing audio to text...")
        progress_bar.progress(40)
        
        # Stage 3: Processing
        status_text.markdown("### 🧠 Running AI analysis...")
        progress_bar.progress(60)
        
        # Run the actual pipeline
        transcription_path, analysis_path = run_pipeline(
            str(st.session_state.audio_path),
            str(st.session_state.json_path_1),
            str(st.session_state.json_path_2)
        )
        
        progress_bar.progress(80)
        status_text.markdown("### 📊 Generating reports...")
        
        # Load results
        with open(transcription_path, 'r', encoding='utf-8') as f:
            st.session_state.transcription_raw = json.load(f)
        
        with open(analysis_path, 'r', encoding='utf-8') as f:
            st.session_state.analysis_raw = json.load(f)
        
        st.session_state.transcription_path = transcription_path
        st.session_state.analysis_path = analysis_path
        
        progress_bar.progress(100)
        status_text.markdown("### ✅ Processing complete!")
        
        time.sleep(1)
        st.session_state.step = "result"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during processing: {e}")
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Try Again", use_container_width=True):
                st.session_state.step = "ready"
                st.rerun()

# ==================== RESULTS ====================
elif st.session_state.step == "result":
    if not st.session_state.logged_in:
        st.session_state.return_to_step = "result"
        st.session_state.step = "login"
        st.rerun()
    
    _stepper()
    _display_logo()
    
    st.markdown('<h2 class="section-title">Analysis Results 📊</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Transcription", "🔍 Analysis", "📊 Matrix View", "💾 Downloads"])
    
    with tab1:
        st.markdown("### 🎤 Full Transcription")
        if st.session_state.transcription_raw:
            st.json(st.session_state.transcription_raw, expanded=True)
        else:
            st.warning("No transcription data available")
    
    with tab2:
        st.markdown("### 🧠 AI Analysis Results")
        if st.session_state.analysis_raw:
            st.json(st.session_state.analysis_raw, expanded=True)
        else:
            st.warning("No analysis data available")
    
    with tab3:
        st.markdown("### 📊 Survey Validation Matrix")
        
        if st.button("🔄 Generate Matrix Table", use_container_width=False):
            st.session_state.show_matrix = True
        
        if st.session_state.show_matrix and st.session_state.analysis_raw:
            try:
                matrix_df = _generate_matrix_table(st.session_state.analysis_raw)
                st.dataframe(matrix_df, use_container_width=True)
                
                # Option to download matrix as CSV
                csv = matrix_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Matrix as CSV",
                    data=csv,
                    file_name="survey_validation_matrix.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error generating matrix: {e}")
    
    with tab4:
        st.markdown("### 💾 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.transcription_raw:
                st.download_button(
                    label="📥 Download Transcription JSON",
                    data=json.dumps(st.session_state.transcription_raw, indent=2),
                    file_name="transcription.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            if st.session_state.analysis_raw:
                st.download_button(
                    label="📥 Download Analysis JSON",
                    data=json.dumps(st.session_state.analysis_raw, indent=2),
                    file_name="analysis.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process Another Survey", use_container_width=True):
            # Reset session state for new analysis
            st.session_state.step = "audio"
            st.session_state.audio_file = None
            st.session_state.json_file_1 = None
            st.session_state.json_file_2 = None
            st.session_state.show_matrix = False
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()
