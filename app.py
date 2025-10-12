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
    
    * { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: #ffffff; }

    .stButton>button {
        background: linear-gradient(90deg, #dc2626 0%, #b91c1c 100%);
        color: white; border: none; border-radius: 8px;
        padding: 12px 24px; font-weight: 600;
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
        border: 2px dashed #dc2626; border-radius: 12px;
        padding: 30px; text-align: center; margin: 20px 0;
        transition: all 0.3s ease;
    }
    .upload-section:hover { background: rgba(255, 255, 255, 0.08); border-color: #ef4444; }

    .step {
        display: inline-block; padding: 8px 16px; margin: 0 8px;
        border-radius: 20px; background: rgba(255, 255, 255, 0.1);
        color: #9ca3af; font-size: 14px; font-weight: 500;
    }
    .step.active {
        background: linear-gradient(90deg, #dc2626 0%, #b91c1c 100%);
        color: white; box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
    }

    .hero-title {
        font-size: 3rem; font-weight: 700;
        background: linear-gradient(90deg, #dc2626 0%, #ef4444 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 20px;
    }
    .subtitle { text-align: center; color: #d1d5db; font-size: 1.2rem; margin-bottom: 40px; }

    .info-card {
        background: rgba(220, 38, 38, 0.1); border-left: 4px solid #dc2626;
        padding: 20px; border-radius: 8px; margin: 20px 0;
    }

    .stDownloadButton>button {
        background: linear-gradient(90deg, #059669 0%, #047857 100%);
        color: white; border: none; border-radius: 8px;
        padding: 10px 20px; font-weight: 600; transition: all 0.3s ease;
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #047857 0%, #065f46 100%);
        transform: translateY(-2px);
    }

    .json-viewer {
        background: #1f2937; border: 1px solid #374151; border-radius: 8px;
        padding: 20px; max-height: 500px; overflow-y: auto;
        font-family: 'Courier New', monospace; font-size: 14px; color: #d1fae5;
    }

    .stepper-container { text-align: center; padding: 30px 0; margin-bottom: 30px; }

    .section-title { font-size: 1.8rem; font-weight: 600; color: #ffffff; margin-top: 60px; margin-bottom: 30px; }
    .why-section {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(29, 78, 216, 0.05) 100%);
        border-left: 4px solid #3b82f6; padding: 30px; border-radius: 8px;
        margin: 30px 0; color: #d1d5db; font-size: 1.05rem; line-height: 1.8;
    }

    .two-column-section { display: grid; grid-template-columns: 1fr 1fr; gap: 50px; margin: 40px 0; }
    .column-title { font-size: 1.3rem; font-weight: 600; color: #ffffff; margin-bottom: 25px; }

    .benefit-item { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 18px; }
    .benefit-icon { color: #10b981; font-size: 1.2rem; margin-top: 2px; flex-shrink: 0; }
    .benefit-text { color: #e5e7eb; font-size: 0.95rem; line-height: 1.6; }

    .faq-title { font-size: 1.8rem; font-weight: 600; color: #ffffff; margin-top: 60px; margin-bottom: 30px; }
    .stExpander { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; margin-bottom: 12px; }
    .stExpander:hover { background: rgba(255, 255, 255, 0.05); border-color: rgba(220, 38, 38, 0.3); }

    @media (max-width: 768px) {
        .two-column-section { grid-template-columns: 1fr; gap: 30px; }
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
        # login gate
        "show_login": False,
        "authenticated": False,
        "username": "",
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
    {section_key: {question_key: [agent_recorded, ai_finding, agent_asked, symantic]}}
    """
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
                    "symantic": responses[3],
                }
            else:
                row = {
                    "Section": section_key,
                    "Question_no": question_key,
                    "agent_recorded": responses[0] if len(responses) > 0 else "Not Available",
                    "ai_finding": responses[1] if len(responses) > 1 else "Not Available",
                    "agent_asked": responses[2] if len(responses) > 2 else "Not Available",
                    "symantic": responses[3] if len(responses) > 3 else "Not Available",
                }
            table_rows.append(row)
    df = pd.DataFrame(table_rows)
    return df

def _generate_transcript_table(transcription_json):
    """
    Build a 2-column table from transcription JSON.
    Columns: Speaker, Text
    """
    try:
        if isinstance(transcription_json, str):
            transcription_json = json.loads(transcription_json)
    except Exception:
        transcription_json = {}

    rows = []
    call_block = (
        transcription_json.get("Call Details")
        or transcription_json.get("Call_Details")
        or transcription_json
    )
    segments = (
        (call_block or {}).get("Transcript")
        or (call_block or {}).get("transcript")
        or []
    )
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        speaker = seg.get("Speaker", "Unknown")
        text = seg.get("Voice") or seg.get("Text") or seg.get("Utterance") or ""
        if isinstance(text, dict):
            text = text.get("content", "") or str(text)
        rows.append({"Speaker": speaker, "Text": text})
    return pd.DataFrame(rows, columns=["Speaker", "Text"])

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
        f'<div class="stepper-container">{"".join(chips)}</div>',
        unsafe_allow_html=True
    )

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

    st.markdown('<h1 class="hero-title">🎧 SurveyScribe AI </h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle"> From Voice to Value with AI Insight </p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.show_login = True

        if st.session_state.get("show_login", False):
            st.markdown("---")
            st.subheader("Sign in to continue")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Continue", type="primary"):
                    if username.strip() and password.strip():
                        st.session_state.username = username.strip()
                        st.session_state.authenticated = True
                        st.session_state.show_login = False
                        st.session_state.step = "audio"
                        st.rerun()
                    else:
                        st.error("Please enter both username and password.")
            with c2:
                if st.button("Cancel"):
                    st.session_state.show_login = False
                    st.rerun()

    # Info sections (unchanged)
    st.markdown('<h2 class="section-title"> The Story Behind Our Innovation </h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="why-section">
        This product was built to revolutionize the way telephone surveys are conducted by bringing the power of AI to every conversation. It matters because accurate transcripts and intelligent analysis ensure that each interaction is meaningful, helping organizations capture true insights and improve customer experiences. By validating answers and assessing how well agents ask questions, this platform drives higher survey quality and smarter decision-making.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<h2 class="section-title"> Unlocking Value for You </h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3 class="column-title">Our Solution</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Complete independence from third-party APIs and their limitations</div></div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Direct audio processing for accurate and detailed transcription results</div></div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Intelligent analysis system with context-aware question extraction</div></div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Speaker diarization to identify and separate multiple speakers</div></div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown('<h3 class="column-title">Key Benefits</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text"> Improved survey accuracy and reliability </div></div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Configurable JSON-based survey question templates</div></div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Real-time processing with instant downloadable outputs</div></div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="benefit-item"><div class="benefit-icon">✓</div><div class="benefit-text">Support for Hindi language conversations with cultural context understanding</div></div>
        """, unsafe_allow_html=True)

    st.markdown('<h2 class="faq-title">Frequently Asked Questions</h2>', unsafe_allow_html=True)
    with st.expander("How can organizations use this platform for survey analysis?"):
        st.markdown("""
        Organizations can upload audio recordings along with custom JSON configuration files. 
        The platform transcribes, diarizes speakers, and extracts answers to predefined survey questions.
        """)
    with st.expander("Can I customize the survey questions and analysis parameters?"):
        st.markdown("""
        Yes, two JSON configuration files allow defining questions, response options, and analysis parameters.
        """)
    with st.expander("Does the platform work for long-form conversations?"):
        st.markdown("""
        It handles short calls to extended interviews with timestamps and comprehensive analysis.
        """)
    with st.expander("How accurate is Hindi language handling?"):
        st.markdown("""
        Advanced models support conversational Hindi, including code-switching, with contextual matching.
        """)
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==================== AUDIO UPLOAD ====================
elif st.session_state.step == "audio":
    _stepper()
    _display_logo()
    st.markdown('<h2 style="color: #dc2626;">📁 Step 1: Upload Audio File</h2>', unsafe_allow_html=True)
    st.markdown("Upload your audio file (supported formats: MP3, WAV, M4A, etc.)")

    audio_file = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "ogg", "flac"],
        key="audio_uploader"
    )
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
    st.markdown('<h2 style="color: #dc2626;">📄 Step 2: Upload User Auth File </h2>', unsafe_allow_html=True)
    st.markdown("Upload the User Auth configuration file")
    json_file_1 = st.file_uploader("Choose JSON file", type=["json"], key="json1_uploader")
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
    st.markdown('<h2 style="color: #dc2626;">📄 Step 3: Upload Survey Response JSON File </h2>', unsafe_allow_html=True)
    st.markdown("Upload the Survey JSON file")
    json_file_2 = st.file_uploader("Choose Survey JSON file", type=["json"], key="json2_uploader")
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
    st.markdown('<h2 style="color: #dc2626;">✅ Start Your Insight</h2>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("**Selected Files uploaded successfully, Please verify:**")
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
        if st.button("🚀 Start Analysis", use_container_width=True):
            st.session_state.step = "processing"
            st.rerun()

# ==================== PROCESSING ====================
elif st.session_state.step == "processing":
    _stepper()
    _display_logo()
    st.markdown('<h2 style="color: #dc2626;">⚙️ Processing...</h2>', unsafe_allow_html=True)
    progress_bar = st.progress(0)
    status_text = st.empty()
    try:
        status_text.text("📤 Uploading files...")
        progress_bar.progress(20)
        time.sleep(0.5)
        status_text.text("🔄 Crunching the Conversation...")
        progress_bar.progress(40)
        transcription_path, _, final_path, transcription_raw, final_raw = run_pipeline(
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
    st.markdown('<h2 style="color: #dc2626;">📊 Insight Scoop</h2>', unsafe_allow_html=True)

    # Audio Player
    st.markdown("### 🎵 Spin the Track")
    st.markdown("Play & Verify:")
    try:
        with open(st.session_state.audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes)
    except Exception as e:
        st.warning(f"Could not load audio file: {str(e)}")

    st.markdown("---")

    # Three tabs: JSON, Table, Analysis
    tab_json, tab_table, tab_analysis = st.tabs(["🧾 Transcription JSON", "📋 Transcript Table", "📈 Analysis"])

    with tab_json:
        st.markdown("### Transcription JSON")
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
        else:
            st.info("Transcription not available yet.")

    with tab_table:
        st.markdown("### Transcript Table")
        if st.session_state.transcription_raw:
            tdf = _generate_transcript_table(st.session_state.transcription_raw)
            if not tdf.empty:
                st.dataframe(tdf, use_container_width=True, hide_index=True)
                csv_t = tdf.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="💾 Download Transcript CSV",
                    data=csv_t,
                    file_name="transcript_table.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No transcript segments found.")
        else:
            st.info("Transcription not available yet.")

    with tab_analysis:
        st.markdown("### Response Audit (Analysis JSON)")
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
        else:
            st.info("Analysis not available yet.")

    # Matrix button
    st.markdown("---")
    if st.button("📊 Survey Matrix", use_container_width=True, key="matrix_btn"):
        st.session_state.show_matrix = True

# Display matrix if button was clicked
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
                if col == 'symantic':
                    val = str(row[col]).lower()
                    if 'matched' == val:
                        colors.append('color: #10b981')
                    elif 'not matched' == val:
                        colors.append('color: #ef4444')
                    elif 'fuzzy match' == val:
                        colors.append('color: #f59e0b')
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
