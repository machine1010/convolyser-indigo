with tab1:
    st.markdown("### Transcription Output")

    if st.session_state.transcription_raw:
        # Build 2-column table
        tdf = _generate_transcript_table(st.session_state.transcription_raw)

        if not tdf.empty:
            st.dataframe(
                tdf,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No transcript segments found.")

        # Keep the existing download button
        with open(st.session_state.transcription_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Transcription JSON",
                data=f.read(),
                file_name="transcription.json",
                mime="application/json"
            )
    else:
        st.info("Transcription not available yet.")
