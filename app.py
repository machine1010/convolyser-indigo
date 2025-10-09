import streamlit as st
import dummy_processor

# Apply custom CSS for styling resembling Cockatoo UI
st.markdown(
    """
    <style>
    /* General page styles */
    .main {
        background-color: #f9fafa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #334d4d;
    }
    /* Page title */
    .title {
        font-size: 3rem;
        font-weight: 700;
        color: #2a7f7f;
        padding-bottom: 0.2rem;
        border-bottom: 3px solid #52c6ba;
        margin-bottom: 1.5rem;
    }
    /* Section heading */
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2a7f7f;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    /* Primary buttons */
    .stButton>button {
        background-color: #52c6ba;
        color: #ffffff;
        font-weight: 600;
        border-radius: 12px;
        padding: 0.6em 2em;
        box-shadow: 0 4px 6px rgba(82,198,186,0.3);
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #3a918f;
        box-shadow: 0 6px 8px rgba(58,145,143,0.5);
    }
    /* File uploader area */
    .css-1b7b44y {
        border: 2px dashed #52c6ba;
        border-radius: 16px;
        padding: 2rem;
        background-color: #e3f4f4;
        margin-bottom: 1.5rem;
    }
    /* Expander and info block background */
    .stExpander {
        background-color: #d9f0f0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    /* Text input fields */
    input[type="text"], textarea {
        border-radius: 12px;
        border: 1.5px solid #52c6ba;
        padding: 0.7rem;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main app UI
st.markdown('<div class="title">AI Transcription & Processing</div>', unsafe_allow_html=True)

# File uploader
st.markdown('<div class="section-header">Upload Audio/Video File</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Drag and drop or select a file", type=["mp3","wav","mp4","m4a","mov","avi"])

if uploaded_file:
    st.success("File uploaded successfully.")
    # Show dummy processor options if needed
    with st.expander("Processing Options", expanded=True):
        option_1 = st.checkbox("Enable option 1", value=True)
        option_2 = st.checkbox("Enable option 2", value=False)
        # Add other options based on dummy_processor usage
    
    if st.button("Start Transcription and Processing"):
        # Call dummy_processor with options & file (replicate your existing logic)
        result = dummy_processor.process_file(uploaded_file, option_1, option_2)
        st.markdown('<div class="section-header">Transcription Output</div>', unsafe_allow_html=True)
        st.text_area("Output Text", value=result, height=300)
        st.success("Processing completed.")
