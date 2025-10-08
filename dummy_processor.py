import json
import base64
import os
import google.generativeai as genai
import vertexai
import tempfile
from pathlib import Path
from datetime import datetime

class HindiAudioAnalysisPipeline:
    def __init__(self, credentials_path: str, project_id: str = None, location: str = "us-central1"):
        print("=" * 80)
        print("INITIALIZING HINDI AUDIO ANALYSIS PIPELINE")
        print("=" * 80)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        print(f"✓ Credentials loaded from: {credentials_path}")
        self.project_id = project_id or str(os.environ.get("GOOGLE_CLOUD_PROJECT"))
        self.location = location
        print(f"✓ Project ID: {self.project_id}")
        print(f"✓ Location: {self.location}")
        vertexai.init(project=self.project_id, location=self.location)
        print("✓ Vertex AI initialized")
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        print("✓ Gemini 2.5 Pro model loaded")
        self.generation_config = genai.GenerationConfig(
            temperature=0.1
        )
        self.transcription_prompt = '''
(Paste your full transcription prompt here)
        '''
        self.analysis_prompt = '''
(Paste your full analysis prompt here)
        '''
        print("✓ Prompts configured")
        print("=" * 80)
        print()

    def _load_audio_to_base64(self, file_path: str) -> str:
        with open(file_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")

    def _load_json_to_base64(self, file_path: str) -> str:
        with open(file_path, "rb") as json_file:
            return base64.standard_b64encode(json_file.read()).decode("utf-8")

    def _clean_json_output(self, content: str) -> str:
        lines = content.splitlines(keepends=True)
        if len(lines) >= 2:
            lines = lines[1:-1]
        return ''.join(lines)

    def _save_output(self, content: str, output_path: str, clean: bool = True) -> None:
        if clean:
            content = self._clean_json_output(content)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def process_audio(
        self,
        audio_file_path: str,
        output_dir: str = "./output",
        transcription_filename: str = "hindi_audio_output.json",
        analysis_filename: str = "hindi_analysis_output.json",
        audio_mime_type: str = "audio/m4a"
    ) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        transcription_path = os.path.join(output_dir, transcription_filename)
        analysis_path = os.path.join(output_dir, analysis_filename)

        audio_base64 = self._load_audio_to_base64(audio_file_path)
        contents_transcription = [
            {'mime_type': audio_mime_type, 'data': audio_base64},
            self.transcription_prompt
        ]
        transcription_response = self.model.generate_content(
            contents_transcription,
            generation_config=self.generation_config
        )
        self._save_output(transcription_response.text, transcription_path, clean=True)

        transcript_base64 = self._load_json_to_base64(transcription_path)
        contents_analysis = [
            {'mime_type': 'text/plain', 'data': transcript_base64},
            self.analysis_prompt
        ]
        analysis_response = self.model.generate_content(
            contents_analysis,
            generation_config=self.generation_config
        )
        self._save_output(analysis_response.text, analysis_path, clean=True)

        try:
            with open(transcription_path, 'r', encoding='utf-8') as f:
                transcription_content = json.loads(f.read())
        except json.JSONDecodeError:
            with open(transcription_path, 'r', encoding='utf-8') as f:
                transcription_content = f.read()
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_content = json.loads(f.read())
        except json.JSONDecodeError:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_content = f.read()

        return {
            'transcription_path': transcription_path,
            'analysis_path': analysis_path,
            'transcription': transcription_content,
            'analysis': analysis_content
        }

def run_pipeline(audio_path: Path, license_path: Path):
    credentials_path = str(license_path)
    project_id = None
    out_dir = tempfile.mkdtemp(prefix="hindi-audio-pipeline-")
    pipeline = HindiAudioAnalysisPipeline(
        credentials_path=credentials_path, project_id=project_id
    )
    result = pipeline.process_audio(
        audio_file_path=str(audio_path),
        output_dir=out_dir
    )
    return result['transcription_path'], result['analysis_path'], result['transcription'], result['analysis']
