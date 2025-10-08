# dummy_processor.py
import json, random, time, uuid, tempfile
from pathlib import Path
import tempfile
from pathlib import Path
from HindiAudioAnalysisPipeline import HindiAudioAnalysisPipeline  # assuming the class is in HindiAudioAnalysisPipeline.py, use your actual module path

def run_pipeline(audio_path: Path, license_path: Path):
    # --- Use the license key as the credentials file ---
    credentials_path = str(license_path)
    project_id = None  # Optional: can be extracted from .json if needed

    # The output directory is a fresh temp folder per run
    out_dir = tempfile.mkdtemp(prefix="hindi-audio-pipeline-")
    out_dir_path = str(out_dir)

    # Instantiate pipeline object
    pipeline = HindiAudioAnalysisPipeline(
        credentials_path=credentials_path, project_id=project_id
    )

    # Call actual pipeline; audio_path is a full file path
    result = pipeline.process_audio(
        audio_file_path=str(audio_path),
        output_dir=out_dir_path
    )

    # Return output file paths (so the UI can load them and enable downloads)
    return result['transcription_path'], result['analysis_path'], result['transcription'], result['analysis']
