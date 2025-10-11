import json
import time
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd
# from dummyprocessor import runpipeline

# This is a dummy function to replace the actual pipeline for standalone running
def run_pipeline(audio_path, json_path1, json_path2):
    print(f"Running pipeline with: {audio_path}, {json_path1}, {json_path2}")
    time.sleep(2) # Simulate processing time

    # Create dummy output files and raw data
    dummy_transcription = {"text": "This is a dummy transcription."}
    dummy_analysis = {"summary": "This is a dummy analysis."}
    
    transcription_path = Path(tempfile.gettempdir()) / "transcription.json"
    analysis_path = Path(tempfile.gettempdir()) / "analysis.json"
    
    with open(transcription_path, 'w') as f:
        json.dump(dummy_transcription, f)
        
    with open(analysis_path, 'w') as f:
        json.dump(dummy_analysis, f)
        
    return str(transcription_path), str(analysis_path), dummy_transcription, dummy_analysis


st.set_page_config(
    page_title="YBrantWorks - Conversation Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="st-"] {
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
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 20px;
    max-height: 500px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    color: #d1fae5;
}
.stepper-container {
    text-align: center;
    padding: 30px 0;
    margin-bottom: 30px;
}
.section-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #ffffff;
    margin-top: 60px;
    margin-bottom: 30px;
    text-align: center;
}
.why-section {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(29, 78, 216, 0.05) 100%);
    border-left: 4px solid #3b82f6;
    padding: 30px;
    border-radius: 8px;
    margin: 30px auto;
    color: #d1d5db;
    font-size: 1.05rem;
    line-height: 1.8;
    max-width: 900px;
}
.two-column-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 50px;
    margin: 40px 0;
}
.column-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 25px;
}
.benefit-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 18px;
}
.benefit-icon {
    color: #10b981;
    font-size: 1.2rem;
    margin-top: 2px;
    flex-shrink: 0;
}
.benefit-text {
    color: #e5e7eb;
    font-size: 0.95rem;
    line-height: 1.6;
}
.faq-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #ffffff;
    margin-top: 60px;
    margin-bottom: 30px;
    text-align: center;
}
.stExpander {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin-bottom: 12px;
}
.stExpander:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(220, 38, 38, 0.3);
}
@media (max-width: 768px) {
    .two-column-section {
        grid-template-columns: 1fr;
        gap: 30px;
    }
}
</style>
""", unsafe_allow_html=True)


def init_state():
    """Initialize session state variables."""
    default_values = {
        'step': 'landing',
        'authenticated': False,
        'audio_file': None,
        'json_file1': None,
        'json_file2': None,
        'audio_path': None,
        'json_path1': None,
        'json_path2': None,
        'transcription_path': None,
        'analysis_path': None,
        'transcription_raw': None,
        'analysis_raw': None,
        'show_matrix': False,
    }
    for k, v in default_values.items():
        if k not in st.session_state:
            st.session_state[k] = v

def save_temp_uploaded_file(uploaded_file, suffix: str) -> Path:
    """Save uploaded file to temporary location."""
    ext = Path(uploaded_file.name).suffix or suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(uploaded_file.getvalue())
    return Path(tmp.name)


def generate_matrix_table(analysis_json: dict) -> pd.DataFrame:
    """Generate a matrix table from the analysis JSON output."""
    table_rows = []
    for section_key, section_data in analysis_json.items():
        if section_key == "summary":
            continue
        questions = section_data.get("questions", {})
        for question_key, responses in questions.items():
            if len(responses) >= 4:
                row = {
                    "Section": section_key,
                    "Question No": question_key,
                    "Agent Recorded": responses[0],
                    "AI Finding": responses[1],
                    "Agent Asked": responses[2],
                    "Symantic": responses[3],
                }
            else:
                row = {
                    "Section": section_key,
                    "Question No": question_key,
                    "Agent Recorded": responses[0] if len(responses) > 0 else "Not Available",
                    "AI Finding": responses[1] if len(responses) > 1 else "Not Available",
                    "Agent Asked": responses[2] if len(responses) > 2 else "Not Available",
                    "Symantic": responses[3] if len(responses) > 3 else "Not Available",
                }
            table_rows.append(row)
    df = pd.DataFrame(table_rows)
    return df


def stepper():
    """Display progress stepper."""
    stages = ['landing', 'audio', 'json1', 'json2', 'ready', 'processing', 'result']
    labels = ["Upload Audio", "JSON File 1", "JSON File 2", "Explore", "Result"]
    try:
        current_stage_index = stages.index(st.session_state.step)
        # Map current stage index to display index (1-5)
        display_idx = max(1, min(5, current_stage_index - 1))
    except ValueError:
        display_idx = 1
    
    chips = []
    for i, lbl in enumerate(labels, 1):
        cls = "step active" if i == display_idx else "step"
        chips.append(f'<span class="{cls}">{lbl}</span>')
    
    st.markdown(f'<div class="stepper-container">{"".join(chips)}</div>', unsafe_allow_html=True)


def display_logo():
    """Display logo on every page."""
    col_logo, _ = st.columns([1, 4])
    with col_logo:
        # st.image("logo.png", width=150)
        st.markdown("## 🤖 SurveyScribe AI")
    st.markdown("<br>", unsafe_allow_html=True)


# --- MAIN APP LOGIC ---
init_state()

if st.session_state.step == 'landing':
    display_logo()
    st.markdown('<h1 class="hero-title">From Voice to Value with AI Insight</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transforming Telephone Surveys with Advanced Conversation Intelligence</p>', unsafe_allow_html=True)
    st.markdown("---")

    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        if st.button("Get Started", use_container_width=True):
            st.session_state.step = 'login'
            st.rerun()

    st.markdown('<h2 class="section-title">The Story Behind Our Innovation</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="why-section">
        This product was built to revolutionize the way telephone surveys are conducted by bringing the power of AI to every conversation. It matters because accurate transcripts and intelligent analysis ensure that each interaction is meaningful, helping organizations capture true insights and improve customer experiences. By validating answers and assessing how well agents ask questions, this platform drives higher survey quality and smarter decision-making.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-title">Unlocking Value for You</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3 class="column-title">Our Solution</h3>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">✔️</div><div class="benefit-text">Complete independence from third-party APIs and their limitations</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">✔️</div><div class="benefit-text">Direct audio processing for accurate and detailed transcription results</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">✔️</div><div class="benefit-text">Intelligent analysis system with context-aware question extraction</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">✔️</div><div class="benefit-text">Speaker diarization to identify and separate multiple speakers</div></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<h3 class="column-title">Key Benefits</h3>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">🚀</div><div class="benefit-text">Improved survey accuracy and reliability</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">🚀</div><div class="benefit-text">Configurable JSON-based survey question templates</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">🚀</div><div class="benefit-text">Real-time processing with instant downloadable outputs</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div><div class="benefit-item"><div class="benefit-icon">🚀</div><div class="benefit-text">Support for Hindi language conversations with cultural context understanding</div></div></div>', unsafe_allow_html=True)
    
    st.markdown('<h2 class="faq-title">Frequently Asked Questions</h2>', unsafe_allow_html=True)
    with st.expander("How can organizations use this platform for survey analysis?"):
        st.markdown("Organizations can upload audio recordings of telephone surveys or field interviews along with their custom JSON configuration files. The platform automatically transcribes the conversation, performs speaker diarization, and extracts specific answers to predefined survey questions. This significantly reduces manual data entry time and improves accuracy in capturing survey responses.")
    with st.expander("Can I customize the survey questions and analysis parameters?"):
        st.markdown("Yes! The platform accepts two JSON configuration files that allow you to define custom survey questions, response options, and analysis parameters. This makes it highly flexible for different types of surveys, whether political, social, or organizational research. You can adapt the question sets to match your specific research needs.")
    with st.expander("Does the platform work for long-form conversations?"):
        st.markdown("Absolutely. The platform is designed to handle conversations of varying lengths, from short 2-3 minute calls to extended interviews. The transcription engine accurately captures timestamps for each speaker segment, and the analysis module can process comprehensive conversations while extracting relevant information across the entire audio duration.")
    with st.expander("How accurate is the Hindi language transcription and analysis?"):
        st.markdown("The platform uses advanced AI models specifically trained for Hindi language understanding, including various dialects and regional variations. It can handle conversational Hindi with high accuracy, including code-switching between Hindi and English. The analysis engine understands contextual meanings and can match responses to predefined options even when respondents use colloquial or varied phrasing.")
    st.markdown("<br><br>", unsafe_allow_html=True)

# --- NEW LOGIN STEP ---
elif st.session_state.step == 'login':
    display_logo()
    st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>User Login</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #d1d5db;'>Please enter your credentials to continue.</p>", unsafe_allow_html=True)
    
    _, col_form, _ = st.columns([1, 1.5, 1])

    with col_form:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="user")
            password = st.text_input("Password", type="password", placeholder="pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                if username == "user" and password == "pass":
                    st.session_state.authenticated = True
                    st.session_state.step = 'audio'
                    st.rerun()
                else:
                    st.error("Incorrect username or password. Please try again.")
    
    # Back button to return to the landing page
    if st.button("← Back to Home"):
        st.session_state.step = 'landing'
        st.rerun()


elif st.session_state.step == 'audio':
    stepper()
    display_logo()
    st.markdown('<h2 style="color: #dc2626;">Step 1: Upload Audio File</h2>', unsafe_allow_html=True)
    st.markdown("Upload your audio file (supported formats: MP3, WAV, M4A, etc.)")
    audio_file = st.file_uploader("Choose an audio file", type=['mp3', 'wav', 'm4a', 'ogg', 'flac'], key="audio_uploader")

    if audio_file:
        st.session_state.audio_file = audio_file
        st.success(f"Audio file uploaded: **{audio_file.name}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state.step = 'landing'
            st.rerun()
    with col2:
        if st.button("Next →", use_container_width=True, disabled=not st.session_state.audio_file):
            st.session_state.audio_path = save_temp_uploaded_file(st.session_state.audio_file, '.m4a')
            st.session_state.step = 'json1'
            st.rerun()

elif st.session_state.step == 'json1':
    stepper()
    display_logo()
    st.markdown('<h2 style="color: #dc2626;">Step 2: Upload User Auth File</h2>', unsafe_allow_html=True)
    st.markdown("Upload the User Auth configuration file")
    json_file1 = st.file_uploader("Choose JSON file", type=['json'], key="json1_uploader")

    if json_file1:
        st.session_state.json_file1 = json_file1
        st.success(f"JSON File 1 uploaded: **{json_file1.name}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.step = 'audio'
            st.rerun()
    with col2:
        if st.button("Next →", use_container_width=True, disabled=not st.session_state.json_file1):
            st.session_state.json_path1 = save_temp_uploaded_file(st.session_state.json_file1, '.json')
            st.session_state.step = 'json2'
            st.rerun()

elif st.session_state.step == 'json2':
    stepper()
    display_logo()
    st.markdown('<h2 style="color: #dc2626;">Step 3: Upload Survey Response JSON File</h2>', unsafe_allow_html=True)
    st.markdown("Upload the Survey JSON file")
    json_file2 = st.file_uploader("Choose Survey JSON file", type=['json'], key="json2_uploader")
    
    if json_file2:
        st.session_state.json_file2 = json_file2
        st.success(f"JSON File 2 uploaded: **{json_file2.name}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.step = 'json1'
            st.rerun()
    with col2:
        if st.button("Process All Files →", use_container_width=True, disabled=not st.session_state.json_file2):
            st.session_state.json_path2 = save_temp_uploaded_file(st.session_state.json_file2, '.json')
            st.session_state.step = 'ready'
            st.rerun()

elif st.session_state.step == 'ready':
    stepper()
    display_logo()
    st.markdown('<h2 style="color: #dc2626;">Start Your Insight</h2>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("Selected Files uploaded successfully, Please verify:")
    st.markdown(f"- **Audio:** {st.session_state.audio_file.name if st.session_state.audio_file else 'NA'}")
    st.markdown(f"- **JSON File 1:** {st.session_state.json_file1.name if st.session_state.json_file1 else 'NA'}")
    st.markdown(f"- **JSON File 2:** {st.session_state.json_file2.name if st.session_state.json_file2 else 'NA'}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.step = 'json2'
            st.rerun()
    with col2:
        if st.button("🚀 Start Analysis", use_container_width=True):
            st.session_state.step = 'processing'
            st.rerun()

elif st.session_state.step == 'processing':
    stepper()
    display_logo()
    st.markdown('<h2 style="color: #dc2626;">Processing...</h2>', unsafe_allow_html=True)
    progress_bar = st.progress(0)
    status_text = st.empty()
    try:
        status_text.text("Uploading files...")
        progress_bar.progress(20)
        time.sleep(0.5)

        status_text.text("Crunching the Conversation...")
        progress_bar.progress(40)
        
        transcription_path, final_path, transcription_raw, final_raw = run_pipeline(
            audio_path=st.session_state.audio_path,
            json_path1=st.session_state.json_path1,
            json_path2=st.session_state.json_path2
        )
        
        progress_bar.progress(80)
        status_text.text("Processing complete!")
        
        st.session_state.transcription_path = transcription_path
        st.session_state.analysis_path = final_path
        st.session_state.transcription_raw = transcription_raw
        st.session_state.analysis_raw = final_raw
        
        progress_bar.progress(100)
        time.sleep(1)
        st.session_state.step = 'result'
        st.rerun()
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        if st.button("Try Again"):
            st.session_state.step = 'ready'
            st.rerun()

elif st.session_state.step == 'result':
    stepper()
    display_logo()
    st.markdown('<h2 style="color: #dc2626;">Insight Scoop</h2>', unsafe_allow_html=True)
    
    st.markdown("### Spin the Track")
    st.markdown("Play & Verify")
    try:
        with open(st.session_state.audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
        st.audio(audio_bytes)
    except Exception as e:
        st.warning(f"Could not load audio file: {str(e)}")

    st.markdown("---")
    tab1, tab2 = st.tabs(["Transcription", "Analysis"])

    with tab1:
        st.markdown("#### Transcription Output")
        if st.session_state.transcription_raw:
            st.markdown('<div class="json-viewer">', unsafe_allow_html=True)
            st.json(st.session_state.transcription_raw)
            st.markdown('</div>', unsafe_allow_html=True)
            with open(st.session_state.transcription_path, "rb") as f:
                st.download_button(
                    label="Download Transcription JSON",
                    data=f.read(),
                    file_name="transcription.json",
                    mime="application/json"
                )

    with tab2:
        st.markdown("#### Response Audit")
        if st.session_state.analysis_raw:
            st.markdown('<div class="json-viewer">', unsafe_allow_html=True)
            st.json(st.session_state.analysis_raw)
            st.markdown('</div>', unsafe_allow_html=True)
            with open(st.session_state.analysis_path, "rb") as f:
                st.download_button(
                    label="Download Analysis JSON",
                    data=f.read(),
                    file_name="analysis.json",
                    mime="application/json"
                )

    st.markdown("---")
    if st.button("📊 Survey Matrix", use_container_width=True, key="matrix_btn"):
        st.session_state.show_matrix = not st.session_state.show_matrix

    if st.session_state.show_matrix:
        st.markdown("#### Matrix Output")
        st.markdown("---")
        try:
            with open(st.session_state.analysis_path, 'r', encoding='utf-8') as f:
                final_json = json.load(f)

            matrix_df = generate_matrix_table(final_json)

            def highlight_response_4(row):
                colors = [''] * len(row)
                cols_to_check = matrix_df.columns
                if 'Symantic' in cols_to_check:
                    val = str(row['Symantic']).lower()
                    color = ''
                    if "matched" in val:
                        color = 'color: #10b981'  # Green text
                    elif "not matched" in val:
                        color = 'color: #ef4444'  # Red text
                    elif "fuzzy match" in val:
                        color = 'color: #f59e0b'  # Amber text
                    
                    colors[list(cols_to_check).index('Symantic')] = color
                return colors

            styled_df = matrix_df.style.apply(highlight_response_4, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)
            
            csv = matrix_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Matrix as CSV",
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
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Process New Files", use_container_width=True):
            for key in ['audio_file', 'json_file1', 'json_file2', 'audio_path', 'json_path1', 'json_path2', 'transcription_path', 'analysis_path', 'transcription_raw', 'analysis_raw', 'show_matrix']:
                if key in st.session_state:
                    st.session_state[key] = None
            st.session_state.step = 'landing'
            st.rerun()
    with col2:
        if st.button("← Back to Ready", use_container_width=True):
            st.session_state.step = 'ready'
            st.rerun()
