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
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* General styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hero section */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    
    /* Stepper */
    .stepper {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 0 2rem;
    }
    
    .step {
        flex: 1;
        text-align: center;
        padding: 1rem;
        background: #f8f9fa;
        margin: 0 0.5rem;
        border-radius: 8px;
        font-weight: 600;
        color: #6c757d;
        transition: all 0.3s;
    }
    
    .step.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Cards */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .feature-card h3 {
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    /* Login form styling */
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .login-title {
        text-align: center;
        color: #667eea;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    
    /* Info boxes */
    .info-box {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Dummy users for login
DUMMY_USERS = {
    "admin": "admin123",
    "user1": "password1",
    "demo": "demo123",
    "test": "test123"
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
        "authenticated": False,
        "username": None,
        "show_login": False,
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
    stages = ["landing", "audio", "json1", "json2", "ready", "processing", "result"]
    labels = ["Upload Audio", "JSON File 1", "JSON File 2", "Explore", "Result"]
    
    try:
        idx = max(1, min(5, stages.index(st.session_state.step)))
    except ValueError:
        idx = 1
    
    chips = []
    for i, lbl in enumerate(labels, 1):
        cls = "step active" if i <= idx else "step"
        chips.append(f'<div class="{cls}">{lbl}</div>')
    
    st.markdown(
        f'<div class="stepper">{"".join(chips)}</div>',
        unsafe_allow_html=True
    )

def _login_page():
    """Display login page"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">🔐 Login</h2>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display available demo credentials
    with st.expander("ℹ️ Demo Credentials"):
        st.markdown("""
        **Available demo users:**
        - Username: `admin` | Password: `admin123`
        - Username: `user1` | Password: `password1`
        - Username: `demo` | Password: `demo123`
        - Username: `test` | Password: `test123`
        """)
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", placeholder="Enter your password", type="password")
        
        col1, col2 = st.columns(2)
        login_button = col1.form_submit_button("Login", use_container_width=True)
        cancel_button = col2.form_submit_button("Cancel", use_container_width=True)
        
        if login_button:
            if not username or not password:
                st.warning("⚠️ Please fill in both username and password.")
            elif username in DUMMY_USERS and DUMMY_USERS[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.show_login = False
                st.session_state.step = "audio"
                st.success(f"✅ Welcome, {username}!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")
        
        if cancel_button:
            st.session_state.show_login = False
            st.session_state.step = "landing"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def _landing_page():
    """Display landing page"""
    # Hero section
    st.markdown('<h1 class="hero-title">🎧 YBrantWorks</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">From Voice to Value with AI Insight</p>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Get Started button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
    
    # ==================== NEW SECTIONS ====================
    
    # Section 1: Why We Created This Platform
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Why We Created This Platform")
    st.markdown("""
    In today's fast-paced business environment, understanding customer conversations is crucial. 
    We built this platform to transform raw audio conversations into actionable intelligence, 
    helping businesses improve their customer service quality and agent performance.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section 2: What This Platform Does
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 What This Platform Does")
    st.markdown("""
    - **Transcription**: Converts audio conversations into accurate text transcripts
    - **Analysis**: Evaluates agent performance and question compliance
    - **Insights**: Identifies gaps in conversation flow and data collection
    - **Reporting**: Generates comprehensive reports with actionable metrics
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section 3: Key Features
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### ⚡ Key Features")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **AI-Powered Analysis**
        - Smart conversation parsing
        - Automated quality checks
        - Performance scoring
        """)
    
    with col2:
        st.markdown("""
        **Easy to Use**
        - Simple file upload
        - Intuitive interface
        - Fast processing
        """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section 4: How It Works
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 🔄 How It Works")
    st.markdown("""
    1. **Upload Audio**: Upload your conversation recording
    2. **Add Context**: Provide reference JSON files
    3. **Process**: Our AI analyzes the conversation
    4. **Review**: Get detailed insights and reports
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section 5: Who Can Benefit
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("### 👥 Who Can Benefit")
    st.markdown("""
    - **Quality Assurance Teams**: Monitor agent performance at scale
    - **Training Managers**: Identify coaching opportunities
    - **Operations Leaders**: Track compliance and quality metrics
    - **Business Analysts**: Extract insights from customer conversations
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer CTA
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Analyzing Now", use_container_width=True, key="footer_cta"):
            st.session_state.show_login = True
            st.rerun()

def _audio_page():
    """Audio upload page"""
    _stepper()
    
    st.markdown("## 🎤 Step 1: Upload Audio File")
    st.markdown("Upload the conversation audio file you want to analyze.")
    
    uploaded = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "ogg"],
        help="Supported formats: MP3, WAV, M4A, OGG"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()
    
    with col2:
        if uploaded and st.button("Next ➡️", use_container_width=True):
            st.session_state.audio_file = uploaded
            st.session_state.audio_path = _save_temp(uploaded, ".mp3")
            st.session_state.step = "json1"
            st.rerun()
    
    if uploaded:
        st.audio(uploaded)
        st.success(f"✅ Loaded: {uploaded.name}")

def _json1_page():
    """First JSON upload page"""
    _stepper()
    
    st.markdown("## 📄 Step 2: Upload First JSON File")
    st.markdown("Upload the first reference JSON file.")
    
    uploaded = st.file_uploader(
        "Choose JSON file 1",
        type=["json"],
        help="Upload your first JSON configuration file"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "audio"
            st.rerun()
    
    with col2:
        if uploaded and st.button("Next ➡️", use_container_width=True):
            st.session_state.json_file_1 = uploaded
            st.session_state.json_path_1 = _save_temp(uploaded, ".json")
            st.session_state.step = "json2"
            st.rerun()
    
    if uploaded:
        try:
            content = json.loads(uploaded.read())
            st.json(content)
            st.success(f"✅ Loaded: {uploaded.name}")
        except Exception as e:
            st.error(f"❌ Error reading JSON: {str(e)}")

def _json2_page():
    """Second JSON upload page"""
    _stepper()
    
    st.markdown("## 📄 Step 3: Upload Second JSON File")
    st.markdown("Upload the second reference JSON file.")
    
    uploaded = st.file_uploader(
        "Choose JSON file 2",
        type=["json"],
        help="Upload your second JSON configuration file"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "json1"
            st.rerun()
    
    with col2:
        if uploaded and st.button("Next ➡️", use_container_width=True):
            st.session_state.json_file_2 = uploaded
            st.session_state.json_path_2 = _save_temp(uploaded, ".json")
            st.session_state.step = "ready"
            st.rerun()
    
    if uploaded:
        try:
            content = json.loads(uploaded.read())
            st.json(content)
            st.success(f"✅ Loaded: {uploaded.name}")
        except Exception as e:
            st.error(f"❌ Error reading JSON: {str(e)}")

def _ready_page():
    """Ready to process page"""
    _stepper()
    
    st.markdown("## ✅ Ready to Process")
    st.markdown("All files uploaded successfully. Review and start processing.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎤 Audio File")
        if st.session_state.audio_file:
            st.success(st.session_state.audio_file.name)
    
    with col2:
        st.markdown("### 📄 JSON File 1")
        if st.session_state.json_file_1:
            st.success(st.session_state.json_file_1.name)
    
    with col3:
        st.markdown("### 📄 JSON File 2")
        if st.session_state.json_file_2:
            st.success(st.session_state.json_file_2.name)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.step = "json2"
            st.rerun()
    
    with col2:
        if st.button("🚀 Start Processing", use_container_width=True):
            st.session_state.step = "processing"
            st.rerun()

def _processing_page():
    """Processing page with progress"""
    _stepper()
    
    st.markdown("## ⚙️ Processing...")
    st.markdown("Analyzing your conversation. This may take a few moments.")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Simulate processing with progress updates
        status_text.text("📝 Transcribing audio...")
        progress_bar.progress(20)
        time.sleep(1)
        
        status_text.text("🔍 Analyzing conversation...")
        progress_bar.progress(40)
        
        # Run actual processing
        transcription_path, analysis_path = run_pipeline(
            str(st.session_state.audio_path),
            str(st.session_state.json_path_1),
            str(st.session_state.json_path_2)
        )
        
        progress_bar.progress(70)
        status_text.text("📊 Generating insights...")
        time.sleep(1)
        
        # Load results
        with open(transcription_path, 'r', encoding='utf-8') as f:
            st.session_state.transcription_raw = json.load(f)
        
        with open(analysis_path, 'r', encoding='utf-8') as f:
            st.session_state.analysis_raw = json.load(f)
        
        st.session_state.transcription_path = transcription_path
        st.session_state.analysis_path = analysis_path
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        time.sleep(1)
        
        st.session_state.step = "result"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        if st.button("⬅️ Go Back"):
            st.session_state.step = "ready"
            st.rerun()

def _result_page():
    """Results display page"""
    _stepper()
    
    st.markdown("## 📊 Analysis Results")
    
    # Display user info
    if st.session_state.username:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Logged in as:** {st.session_state.username}")
        with col2:
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.step = "landing"
                st.rerun()
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📝 Transcription", "📊 Analysis", "📋 Matrix View"])
    
    with tab1:
        st.markdown("### Conversation Transcription")
        if st.session_state.transcription_raw:
            st.json(st.session_state.transcription_raw)
            
            # Download button
            json_str = json.dumps(st.session_state.transcription_raw, indent=2)
            st.download_button(
                label="⬇️ Download Transcription",
                data=json_str,
                file_name="transcription.json",
                mime="application/json"
            )
    
    with tab2:
        st.markdown("### Detailed Analysis")
        if st.session_state.analysis_raw:
            st.json(st.session_state.analysis_raw)
            
            # Download button
            json_str = json.dumps(st.session_state.analysis_raw, indent=2)
            st.download_button(
                label="⬇️ Download Analysis",
                data=json_str,
                file_name="analysis.json",
                mime="application/json"
            )
    
    with tab3:
        st.markdown("### Matrix View")
        if st.session_state.analysis_raw:
            try:
                df = _generate_matrix_table(st.session_state.analysis_raw)
                st.dataframe(df, use_container_width=True)
                
                # Download CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download as CSV",
                    data=csv,
                    file_name="analysis_matrix.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error generating matrix: {str(e)}")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Analyze Another", use_container_width=True):
            # Reset file-related state
            st.session_state.step = "audio"
            st.session_state.audio_file = None
            st.session_state.json_file_1 = None
            st.session_state.json_file_2 = None
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.step = "landing"
            st.rerun()

# ==================== MAIN ROUTER ====================

def main():
    """Main application router"""
    
    # Check if login page should be shown
    if st.session_state.show_login and not st.session_state.authenticated:
        _login_page()
        return
    
    # Route based on step
    if st.session_state.step == "landing":
        _landing_page()
    elif st.session_state.step == "audio":
        if not st.session_state.authenticated:
            st.warning("⚠️ Please login first")
            st.session_state.show_login = True
            st.rerun()
        _audio_page()
    elif st.session_state.step == "json1":
        _json1_page()
    elif st.session_state.step == "json2":
        _json2_page()
    elif st.session_state.step == "ready":
        _ready_page()
    elif st.session_state.step == "processing":
        _processing_page()
    elif st.session_state.step == "result":
        _result_page()
    else:
        _landing_page()

if __name__ == "__main__":
    main()
