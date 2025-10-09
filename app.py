import json
import time
import tempfile
from pathlib import Path
import streamlit as st
from dummyprocessor import runpipeline

# Page config
st.set_page_config(
    page_title="BrantWorks Conversation Intelligence",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS for violet gradient background with animated lines
st.markdown(
    """
    <style>
    /* Violet gradient background */
    body, .main {
        background: linear-gradient(135deg, #7F00FF, #E100FF);
        background-attachment: fixed;
        position: relative;
        overflow-x: hidden;
    }
    /* Animated diagonal lines */
    body::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: 100vw;
        pointer-events: none;
        background:
            repeating-linear-gradient(
                45deg,
                rgba(255,255,255,0.1),
                rgba(255,255,255,0.1) 1px,
                transparent 1px,
                transparent 10px
            );
        animation: moveLines 15s linear infinite;
        z-index: 0;
    }
    @keyframes moveLines {
        0% { background-position: 0 0; }
        100% { background-position: 100px 100px; }
    }
    /* Ensure main containers stack above the lines */
    .main > div {
        position: relative;
        z-index: 1;
    }
    /* Position Get Started button bottom left */
    .cta-row {
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 2;
        width: auto !important;
    }
    /* Optional: style button if needed */
    .stButton>button {
        background-color: #7F00FF;
        border-color: #E100FF;
        color: white;
        font-weight: bold;
        padding: 0.5em 1.5em;
        border-radius: 8px;
        box-shadow: 0 3px 6px rgba(225, 0, 255, 0.3);
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background
