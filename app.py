# ---------------------------------------------------------------------
# Navbar + Hero (Get started moved under H1)
# ---------------------------------------------------------------------
col_logo, col_cta = st.columns([0.7, 0.3])

with col_logo:
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    left, right = st.columns([0.8, 0.2])
    with left:
        st.markdown('<div class="brand">', unsafe_allow_html=True)
        try:
            st.image("assets/logo.png", use_container_width=False)
        except Exception:
            st.markdown("YBrantWorks", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        try:
            st.image("assets/icon.png", use_container_width=False)
        except Exception:
            pass
    st.markdown("</div>", unsafe_allow_html=True)

with col_logo:
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("<h1>Conversation insights, instantly</h1>", unsafe_allow_html=True)

    # Get started button directly below H1
    if st.session_state.step == "landing":
        if st.button("Get started", type="primary", key="get_started_btn"):
            st.session_state.step = "audio"

    st.markdown(
        '<p class="small-muted">Upload a call, apply a license, then explore real‑time outputs — now on a cosmic purple theme.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_cta:
    # Right-side carousel only
    carousel_images = [
        "assets/carousel_1.jpg",
        "assets/carousel_2.jpg",
        "assets/carousel_3.jpg",
    ]
    _render_carousel(carousel_images, height=260)

st.markdown("<hr>", unsafe_allow_html=True)
_stepper()
