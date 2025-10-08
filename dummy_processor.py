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

        self.project_id = project_id if project_id else str(os.environ.get("GOOGLE_CLOUD_PROJECT"))
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

        # Your full prompts (as you gave them)
        self.transcription_prompt = '''
This is a Hindi language conversation happens between a caller from the govt organisation and a tribal people . U need to pay close attention to the conversation and generate the transcript of it . Also make sure to do the speaker diarization. Donot pay much attention to the background noise and try not to include it in the transcript. Output it in the below mentioned json format .
If a speaker cannot be identified, label them as "Unknown."
Context about the caller and conversation - The conversation is all about the a speaker  asking  citizens about to whom they want to see as their next cheif minister and to whom they want to see as their next local leader. The speaker will give them multiple options of leader name as well as their party and the citizen have to choose between them. It is just for information purpose and not for actual casting of vote. The speaker may ask the vidhansabha constituency details and the mobile number and the religion of the citizen .The speaker may ask question about wheather they are satisfied by the work of the current leader or chief minister etc. and take opinion of the people.
OUTPUT THE EXACT NUMBER OF SPEAKER.DONOT BIASED BY THE CONTEXT. ANALYSE THE AUDIO PROPERLY .
Provide the output in the following JSON structure:
{
  "Call Details": {
    "Number of Speakers": "<total_number_of_speakers>",
    "Transcript": [
      {
        "Speaker": "<Speaker>",
        "Timestamp": {
          "Start": "<start_time>",
          "End": "<end_time>"
        },
        "Voice": "<extracted_text_from_audio>"
      },
      ...
    ]
  }
}
'''

        self.analysis_prompt = '''
You are an expert analyst tasked with extracting specific information from Hindi language audio call transcripts. Your job is to carefully analyze the provided transcript and extract answers to predefined survey questions.

[...your full analysis prompt continues here...]
'''

        print("✓ Prompts configured")
        print("=" * 80)
        print()

    def _load_audio_to_base64(self, file_path: str) -> str:
        with open(file_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
        return audio_data

    def _load_json_to_base64(self, file_path: str) -> str:
        with open(file_path, "rb") as json_file:
            json_data = base64.standard_b64encode(json_file.read()).decode("utf-8")
        return json_data

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

        # Transcription
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

        # Analysis
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

# ------------------------------------------------------------------------------
# Main Streamlit-compatible entry point. UI expects 4 return values.
# ------------------------------------------------------------------------------
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

