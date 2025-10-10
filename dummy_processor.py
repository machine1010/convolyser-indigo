import json
import base64
import os
import google.generativeai as genai
import vertexai
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any


class AudioAnalysisPipeline:
    """
    Complete 6-step pipeline for Hindi audio transcription, evaluation, analysis,
    comparison, and final consolidated output generation.
    """
    
    def __init__(self, credentials_path: str, project_id: str = None, location: str = "us-central1"):
        """
        Initialize the pipeline with credentials
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file (Gemini API key)
            project_id: Google Cloud project ID
            location: Google Cloud location
        """
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.project_id = project_id if project_id else str(os.environ.get("GOOGLE_CLOUD_PROJECT"))
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model = genai.GenerativeModel("gemini-2.0-flash-lite-001")
        self.generation_config = genai.GenerationConfig(temperature=0.1)
        
        # Initialize all prompts
        self.transcription_prompt = '''prompt here'''
        
        self.evaluation_prompt = '''prompt here'''
        
        self.analysis_prompt = '''prompt here'''
        
        self.comparison_prompt = '''prompt here'''

    def _load_audio_to_base64(self, file_path: str) -> Tuple[str, str]:
        """Convert audio file to base64 encoding and determine mime type"""
        with open(file_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        mime_type = {
            '.m4a': 'audio/m4a',
            '.mp4': 'audio/mp4',
            '.mp3': 'audio/mp3',
            '.wav': 'audio/wav'
        }.get(file_extension, 'application/octet-stream')
        
        return audio_data, mime_type

    def _load_json_to_base64(self, file_path: str) -> str:
        """Convert JSON file to base64 encoding"""
        with open(file_path, "rb") as json_file:
            return base64.standard_b64encode(json_file.read()).decode("utf-8")

    def _clean_json_output(self, content: str) -> str:
        """Clean JSON output by removing markdown code blocks"""
        lines = content.splitlines(keepends=True)
        if len(lines) >= 2:
            lines = lines[1:-1]
        return ''.join(lines)

    def _save_output(self, content: str, output_path: str, clean: bool = True) -> None:
        """Save content to file"""
        if clean:
            content = self._clean_json_output(content)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _merge_survey_jsons(self, json1_path: str, json2_path: str, output_path: str) -> None:
        """Merge two survey JSONs side by side"""
        with open(json1_path, 'r', encoding='utf-8') as f:
            json1 = json.load(f)
        with open(json2_path, 'r', encoding='utf-8') as f:
            json2 = json.load(f)

        merged_json = {}
        all_sections = set(json1.keys()) | set(json2.keys())

        for section_key in all_sections:
            merged_json[section_key] = {}
            section1 = json1.get(section_key, {})
            section2 = json2.get(section_key, {})
            all_questions = set(section1.keys()) | set(section2.keys())

            for question_key in all_questions:
                value1 = section1.get(question_key, "Not Available")
                value2 = section2.get(question_key, "Not Available")
                merged_json[section_key][question_key] = [value1, value2]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_json, f, ensure_ascii=False, indent=2)

    def _create_final_output(self, answers_path: str, quality_path: str, 
                            comparison_path: str, output_path: str) -> None:
        """Merge three JSONs into final comprehensive output"""
        with open(answers_path, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        with open(quality_path, 'r', encoding='utf-8') as f:
            quality = json.load(f)
        with open(comparison_path, 'r', encoding='utf-8') as f:
            comparison = json.load(f)

        final_output = {}
        for section_key in answers.keys():
            final_output[section_key] = {}
            for question_key in answers[section_key].keys():
                ans = answers[section_key][question_key]
                qual = quality.get("quality_assessment", {}).get(question_key, "Not Available")
                comp = comparison.get(section_key, {}).get(question_key, "Not Available")
                final_output[section_key][question_key] = ans + [qual, comp]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)

    def process_audio(
        self,
        audio_file_path: str,
        agent_json_path: str,
        output_dir: str = "./output",
        transcription_filename: str = "audio_transcript.json",
        evaluation_filename: str = "evaluation_output.json",
        analysis_filename: str = "audio_analysis.json",
        merged_filename: str = "merged_survey.json",
        comparison_filename: str = "comparison_output.json",
        final_filename: str = "final_output.json",
        audio_mime_type: str = "audio/m4a"
    ) -> dict:
        """
        Execute the complete 6-step analysis pipeline
        
        Args:
            audio_file_path: Path to Hindi audio file
            agent_json_path: Path to agent's survey JSON
            output_dir: Directory to save output files
            transcription_filename: Name for transcription output file
            evaluation_filename: Name for evaluation output file
            analysis_filename: Name for analysis output file
            merged_filename: Name for merged survey file
            comparison_filename: Name for comparison output file
            final_filename: Name for final output file
            audio_mime_type: MIME type of the audio file
            
        Returns:
            Dictionary containing all output paths and loaded content
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output paths
        transcript_path = os.path.join(output_dir, transcription_filename)
        evaluation_path = os.path.join(output_dir, evaluation_filename)
        analysis_path = os.path.join(output_dir, analysis_filename)
        merged_path = os.path.join(output_dir, merged_filename)
        comparison_path = os.path.join(output_dir, comparison_filename)
        final_path = os.path.join(output_dir, final_filename)

        # Step 1: Transcribe audio
        print("Step 1/6: Transcribing audio...")
        audio_data, detected_mime = self._load_audio_to_base64(audio_file_path)
        mime_type = audio_mime_type if audio_mime_type != "audio/m4a" else detected_mime
        
        contents_transcription = [
            {'mime_type': mime_type, 'data': audio_data},
            self.transcription_prompt
        ]
        
        response = self.model.generate_content(
            contents_transcription,
            generation_config=self.generation_config
        )
        self._save_output(response.text, transcript_path, clean=True)
        print(f"   -> Saved transcript to {transcript_path}")

        # Step 2: Evaluate agent questions
        print("Step 2/6: Evaluating agent performance...")
        transcript_b64 = self._load_json_to_base64(transcript_path)
        
        contents_evaluation = [
            {'mime_type': 'text/plain', 'data': transcript_b64},
            self.evaluation_prompt
        ]
        
        response = self.model.generate_content(
            contents_evaluation,
            generation_config=self.generation_config
        )
        self._save_output(response.text, evaluation_path, clean=True)
        print(f"   -> Saved evaluation to {evaluation_path}")

        # Step 3: Analyze transcript content
        print("Step 3/6: Analyzing transcript...")
        contents_analysis = [
            {'mime_type': 'text/plain', 'data': transcript_b64},
            self.analysis_prompt
        ]
        
        response = self.model.generate_content(
            contents_analysis,
            generation_config=self.generation_config
        )
        self._save_output(response.text, analysis_path, clean=True)
        print(f"   -> Saved analysis to {analysis_path}")

        # Step 4: Merge agent and analysis JSONs
        print("Step 4/6: Merging survey responses...")
        self._merge_survey_jsons(agent_json_path, analysis_path, merged_path)
        print(f"   -> Saved merged data to {merged_path}")

        # Step 5: Compare merged answers
        print("Step 5/6: Comparing responses...")
        merged_b64 = self._load_json_to_base64(merged_path)
        
        contents_comparison = [
            {'mime_type': 'text/plain', 'data': merged_b64},
            self.comparison_prompt
        ]
        
        response = self.model.generate_content(
            contents_comparison,
            generation_config=self.generation_config
        )
        self._save_output(response.text, comparison_path, clean=True)
        print(f"   -> Saved comparison to {comparison_path}")

        # Step 6: Create final output
        print("Step 6/6: Generating final output...")
        self._create_final_output(merged_path, evaluation_path, comparison_path, final_path)
        print(f"   -> Saved final output to {final_path}")

        # Load all outputs for return
        result = {
            'transcription_path': transcript_path,
            'evaluation_path': evaluation_path,
            'analysis_path': analysis_path,
            'merged_path': merged_path,
            'comparison_path': comparison_path,
            'final_path': final_path
        }

        # Load JSON content
        for key in ['transcription', 'evaluation', 'analysis', 'merged', 'comparison', 'final']:
            path_key = f"{key}_path"
            try:
                with open(result[path_key], 'r', encoding='utf-8') as f:
                    result[key] = json.load(f)
            except json.JSONDecodeError:
                with open(result[path_key], 'r', encoding='utf-8') as f:
                    result[key] = f.read()

        print("\n✓ Pipeline completed successfully!")
        return result


def run_pipeline(audio_path, json_path_2, json_path_1):
    """
    Run the complete 6-step pipeline with audio file, agent JSON, and Gemini credentials
    
    Args:
        audio_path: Path to audio file
        agent_json_path: Path to agent's survey JSON file
        gemini_json_path: Path to Gemini API credentials JSON file
        
    Returns:
        Tuple of (transcription_path, analysis_path, final_path, transcription_content, 
                  analysis_content, final_content)
    """
    # Use Gemini JSON as credentials
    credentials_path = str(json_path_1)
    
    # Create output directory
    out_dir = tempfile.mkdtemp(prefix="audio-analysis-pipeline-")
    
    # Initialize pipeline
    pipeline = AudioAnalysisPipeline(credentials_path=credentials_path)
    
    # Process audio with full 6-step pipeline
    result = pipeline.process_audio(
        audio_file_path=str(audio_path),
        agent_json_path=str(agent_json_path),
        output_dir=out_dir
    )
    
    return (
        result['transcription_path'],
        result['analysis_path'],
        result['final_path'],
        result['transcription'],
        
        result['final']
    )


# Example usage
if __name__ == '__main__':
    # For direct script execution
    pipeline = AudioAnalysisPipeline(
        credentials_path="path/to/gemini_credentials.json"
    )
    
    result = pipeline.process_audio(
        audio_file_path="path/to/audio.m4a",
        agent_json_path="path/to/agent_data.json",
        output_dir="./output"
    )
    
    print(f"Final output saved to: {result['final_path']}")
