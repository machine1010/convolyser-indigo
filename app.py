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
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .step {
        display: inline-block;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 20px;
        background: #e0e0e0;
        color: #666;
        font-weight: 600;
    }
    .step.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .highlight {
        background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Dummy credentials
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"

def _init_state():
    """Initialize session state variables"""
    for k, v in {
        "step": "landing",
        "authenticated": False,
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
        chips.append(f'<span class="{cls}">{lbl}</span>')
    
    st.markdown(
        f'<div style="text-align:center;margin:20px 0;">{"".join(chips)}</div>',
        unsafe_allow_html=True
    )

def show_login_page():
    """Display login page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.markdown("""
        <h1 style='text-align: center; font-size: 3em; margin-bottom: 10px;'>
            🎧 YBrantWorks
        </h1>
        <p style='text-align: center; font-size: 1.5em; color: #7f8c8d; margin-bottom: 40px;'>
            Conversation Intelligence Platform
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Login", use_container_width=True):
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.step = "audio"
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
        
        st.markdown("""
            <p style='text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 0.9em;'>
                Demo credentials: admin / password123
            </p>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_landing_page():
    """Display landing page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.markdown("""
        <h1 style='text-align: center; font-size: 3em; margin-bottom: 10px;'>
            🎧 YBrantWorks
        </h1>
        <p style='text-align: center; font-size: 1.5em; color: #7f8c8d; margin-bottom: 40px;'>
            From Voice to Value with AI Insight
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.step = "login"
            st.rerun()
    
    # ==================== NEW SECTIONS ====================
    # Section 1: Why We Created This Platform
    st.markdown('<div class="highlight">', unsafe_allow_html=True)
    st.markdown("### 🎯 Why We Created This Platform")
    st.markdown("""
        In today's fast-paced business environment, understanding customer conversations is critical.
        Our platform leverages cutting-edge AI to transform audio conversations into actionable insights,
        helping businesses improve customer service, compliance, and operational efficiency.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section 2: Key Features
    st.markdown("### ✨ Key Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            **🎙️ Audio Transcription**
            - High-accuracy Hindi transcription
            - Speaker diarization
            - Timestamp tracking
        """)
    
    with col2:
        st.markdown("""
            **📊 Quality Analysis**
            - Survey compliance checking
            - Question evaluation
            - Performance metrics
        """)
    
    with col3:
        st.markdown("""
            **🤖 AI-Powered Insights**
            - Semantic analysis
            - Response comparison
            - Comprehensive reports
        """)
    
    # Section 3: How It Works
    st.markdown("### 🔄 How It Works")
    st.markdown("""
        1. **Upload Audio**: Provide your conversation recording
        2. **Add Survey Data**: Upload survey questionnaire and agent responses
        3. **AI Processing**: Our system transcribes and analyzes the conversation
        4. **Get Results**: Receive detailed insights and quality metrics
    """)
    
    # Section 4: Benefits
    st.markdown('<div class="highlight">', unsafe_allow_html=True)
    st.markdown("### 💡 Benefits")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            - ⚡ **Fast Processing**: Get results in minutes
            - 🎯 **High Accuracy**: Advanced AI models
            - 📈 **Scalable**: Handle multiple conversations
        """)
    
    with col2:
        st.markdown("""
            - 🔒 **Secure**: Your data is protected
            - 📱 **Easy to Use**: Intuitive interface
            - 💼 **Business Ready**: Enterprise-grade solution
        """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_upload_audio():
    """Display audio upload page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("📤 Upload Audio File")
    _stepper()
    
    st.markdown("### Step 1: Upload your audio conversation file")
    uploaded = st.file_uploader(
        "Choose an audio file (M4A, MP3, WAV, MP4)",
        type=["m4a", "mp3", "wav", "mp4"],
        key="audio_uploader"
    )
    
    if uploaded:
        st.success(f"✅ File uploaded: {uploaded.name}")
        st.session_state.audio_file = uploaded
        st.session_state.audio_path = _save_temp(uploaded, ".m4a")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = "landing"
            st.rerun()
    with col2:
        if st.button("Next ➡️", disabled=not st.session_state.audio_file):
            st.session_state.step = "json1"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_upload_json1():
    """Display JSON 1 upload page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("📤 Upload Gemini Credentials JSON")
    _stepper()
    
    st.markdown("### Step 2: Upload your Gemini API credentials JSON file")
    uploaded = st.file_uploader(
        "Choose Gemini credentials JSON file",
        type=["json"],
        key="json1_uploader"
    )
    
    if uploaded:
        st.success(f"✅ File uploaded: {uploaded.name}")
        st.session_state.json_file_1 = uploaded
        st.session_state.json_path_1 = _save_temp(uploaded, ".json")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = "audio"
            st.rerun()
    with col2:
        if st.button("Next ➡️", disabled=not st.session_state.json_file_1):
            st.session_state.step = "json2"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_upload_json2():
    """Display JSON 2 upload page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("📤 Upload Agent Survey JSON")
    _stepper()
    
    st.markdown("### Step 3: Upload the agent's survey response JSON file")
    uploaded = st.file_uploader(
        "Choose agent survey JSON file",
        type=["json"],
        key="json2_uploader"
    )
    
    if uploaded:
        st.success(f"✅ File uploaded: {uploaded.name}")
        st.session_state.json_file_2 = uploaded
        st.session_state.json_path_2 = _save_temp(uploaded, ".json")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = "json1"
            st.rerun()
    with col2:
        if st.button("Next ➡️", disabled=not st.session_state.json_file_2):
            st.session_state.step = "ready"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ready():
    """Display ready to process page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("🚀 Ready to Process")
    _stepper()
    
    st.markdown("### All files uploaded successfully!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"🎵 Audio: {st.session_state.audio_file.name if st.session_state.audio_file else 'Not uploaded'}")
    with col2:
        st.info(f"📄 Credentials: {st.session_state.json_file_1.name if st.session_state.json_file_1 else 'Not uploaded'}")
    with col3:
        st.info(f"📋 Survey: {st.session_state.json_file_2.name if st.session_state.json_file_2 else 'Not uploaded'}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = "json2"
            st.rerun()
    with col2:
        if st.button("▶️ Start Processing", use_container_width=True):
            st.session_state.step = "processing"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_processing():
    """Display processing page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("⚙️ Processing Your Data")
    _stepper()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🎙️ Transcribing audio...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        status_text.text("📊 Analyzing conversation...")
        progress_bar.progress(40)
        
        # Run the pipeline
        (
            st.session_state.transcription_path,
            st.session_state.analysis_path,
            final_path,
            st.session_state.transcription_raw,
            st.session_state.analysis_raw,
        ) = run_pipeline(
            st.session_state.audio_path,
            st.session_state.json_path_2,
            st.session_state.json_path_1,
        )
        
        progress_bar.progress(60)
        status_text.text("🔍 Comparing responses...")
        time.sleep(0.5)
        
        progress_bar.progress(80)
        status_text.text("✅ Generating final report...")
        time.sleep(0.5)
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        time.sleep(1)
        st.session_state.step = "result"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
        if st.button("🔄 Try Again"):
            st.session_state.step = "ready"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_result():
    """Display results page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("📊 Analysis Results")
    _stepper()
    
    tab1, tab2, tab3 = st.tabs(["📝 Transcription", "📊 Analysis Matrix", "📥 Downloads"])
    
    with tab1:
        st.markdown("### Audio Transcription")
        if st.session_state.transcription_raw:
            st.json(st.session_state.transcription_raw)
        else:
            st.warning("No transcription data available")
    
    with tab2:
        st.markdown("### Analysis Matrix")
        if st.session_state.analysis_raw:
            try:
                df = _generate_matrix_table(st.session_state.analysis_raw)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating matrix: {str(e)}")
                st.json(st.session_state.analysis_raw)
        else:
            st.warning("No analysis data available")
    
    with tab3:
        st.markdown("### Download Results")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.transcription_path and Path(st.session_state.transcription_path).exists():
                with open(st.session_state.transcription_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Download Transcription",
                        data=f.read(),
                        file_name="transcription.json",
                        mime="application/json"
                    )
        
        with col2:
            if st.session_state.analysis_path and Path(st.session_state.analysis_path).exists():
                with open(st.session_state.analysis_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Download Analysis",
                        data=f.read(),
                        file_name="analysis.json",
                        mime="application/json"
                    )
    
    if st.button("🔄 Start New Analysis", use_container_width=True):
        # Reset state
        for key in ["audio_file", "json_file_1", "json_file_2", "audio_path", 
                    "json_path_1", "json_path_2", "transcription_path", 
                    "analysis_path", "transcription_raw", "analysis_raw"]:
            st.session_state[key] = None
        st.session_state.step = "audio"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main routing logic
if not st.session_state.authenticated:
    if st.session_state.step == "landing":
        show_landing_page()
    elif st.session_state.step == "login":
        show_login_page()
elif st.session_state.step == "audio":
    show_upload_audio()
elif st.session_state.step == "json1":
    show_upload_json1()
elif st.session_state.step == "json2":
    show_upload_json2()
elif st.session_state.step == "ready":
    show_ready()
elif st.session_state.step == "processing":
    show_processing()
elif st.session_state.step == "result":
    show_result()
