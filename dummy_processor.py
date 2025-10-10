import json
import base64
import os
import google.generativeai as genai
import vertexai
import tempfile
from pathlib import Path
from datetime import datetime


class HindiAudioAnalysisPipeline:
    def __init__(self, credentials_path: str, json_config_1_path: str, json_config_2_path: str, 
                 project_id: str = None, location: str = "us-central1"):
        """
        Initialize the pipeline with credentials and two JSON configuration files
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
            json_config_1_path: Path to first JSON configuration file
            json_config_2_path: Path to second JSON configuration file
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
        
        # Load JSON configuration files
        self.json_config_1 = self._load_json_file(json_config_1_path)
        self.json_config_2 = self._load_json_file(json_config_2_path)
        
        self.transcription_prompt = '''
This is a Hindi language conversation happens between a caller from the govt organisation and a tribal people . U need to pay close attention to the conversation and generate the transcript of it . Also make sure to do the speaker diarization. Donot pay much attention to the background noise and try not to include it in the transcript. Output it in the below mentioned json format .

If a speaker cannot be identified, label them as "Unknown."

Context about the caller and conversation - The conversation is all about the a speaker asking citizens about to whom they want to see as their next cheif minister and to whom they want to see as their next local leader. The speaker will give them multiple options of leader name as well as their party and the citizen have to choose between them. It is just for information purpose and not for actual casting of vote. The speaker may ask the vidhansabha constituency details and the mobile number and the religion of the citizen .The speaker may ask question about wheather they are satisfied by the work of the current leader or chief minister etc. and take opinion of the people.

OUTPUT THE EXACT NUMBER OF SPEAKER.DONOT BIASED BY THE CONTEXT. ANALYSE THE AUDIO PROPERLY .

Provide the output in the following JSON structure:

{
  "Call Details": {
    "Number of Speakers": "",
    "Transcript": [
      {
        "Speaker": "",
        "Timestamp": {
          "Start": "",
          "End": ""
        },
        "Voice": ""
      },
      {
        "Speaker": "",
        "Timestamp": {
          "Start": "",
          "End": ""
        },
        "Voice": ""
      },
      ...
    ]
  }
}
'''

        self.analysis_prompt = '''
You are an expert analyst tasked with extracting specific information from Hindi language audio call transcripts. Your job is to carefully analyze the provided transcript and extract answers to predefined survey questions.

## CRITICAL INSTRUCTIONS:
1. **READ THE ENTIRE TRANSCRIPT CAREFULLY** before answering any question
2. **EXTRACT ANSWERS ONLY FROM THE TRANSCRIPT** - Do not make assumptions or infer answers
3. **MATCH ANSWERS TO PROVIDED OPTIONS** - You must select from the given options only
4. **LANGUAGE HANDLING**: The transcript is in Hindi. Understand the context and meaning in Hindi to match with the provided options
5. **HANDLE MISSING INFORMATION**: If an answer to a question is not found in the transcript, output "Not Available"
6. **BE PRECISE**: Match the respondent's answer to the closest provided option based on the meaning and context
7. **OUTPUT FORMAT**: Return responses in valid JSON format only

## SURVEY QUESTIONS WITH OPTIONS:

### Section 1 – Personal Questions

**Question 1:** क्या आपका वोट इसी विधानसभा में बना हुआ है ?
**Options:**
- हाँ
- नहीं

**Question 2:** क्या मैं आपकी उम्र जान सकता हूँ ?
**Options:**
- 18-30 वर्ष
- 31-45 वर्ष
- 46-60 वर्ष
- 60 वर्ष से अधिक
- बताना नहीं चाहते

**Question 3:** लिंग: (पूछना नहीं है देखकर भरें)
**Options:**
- पुरुष
- महिला

**Question 4:** आप क्या काम करते हैं ?
**Options:**
- कृषि
- मजदूरी/दैनिक वेतन
- सरकारी नौकरी
- निजी नौकरी
- स्वरोजगार/व्यवसाय
- बेरोजगार
- हाउसवाइफ / गृहिणी
- छात्र / पढाई
- अन्य (कृपया उल्लेख करें)

**Question 5:** आप कौन से धर्म से हैं?
**Options:**
- हिन्दू
- मुस्लिम
- सिख
- क्रिस्चियन
- जैन
- बुद्धिस्ट
- किसी धर्म को नहीं मानता
- बताना नहीं चाहते

**Question 6:** आपकी जाति क्या है ?
**Options:**
- (विधानसभा के टॉप 12 जातियों की लिस्ट के अनुसार)

---

### Section 2 – Political Questions

**Question 7:** आपके एमएलए/ विधायक का क्या नाम है?
**Options:**
- MLA का नाम सही बताया
- MLA का नाम नहीं पता
- MLA का नाम गलत बताया

**Question 8:** क्या आप अपने विधायक के काम से खुश हैं ?
**Options:**
- हाँ
- नहीं
- कुछ कह नहीं सकते

**Question 9:** अगर आपका विधायक फिर से चुनाव लड़ता है तो क्या आप उन्हें वोट देंगे ?
**Options:**
- हाँ
- नहीं
- कुछ कह नहीं सकते

**Question 9.1:** अगर नहीं तो, आप अगले विधायक के रूप में किसे देखना चाहते हैं ?
**Options:**
- (संभावित उम्मीदवारों की सुची के अनुसार)

**Question 10:** आप आने वाले विधानसभा चुनाव में किस पार्टी को वोट देंगे?
**Options:**
- JDU | NDA
- महागठबंधन | MGB
- जन सुराज पार्टी
- अन्य
- बीएसपि | BSP
- NOTA
- कह नहीं सकते

**Question 11:** 2020 के पिछले विधानसभा चुनाव में आपने किस पार्टी को वोट दिया था?
**Options:**
- JDU | NDA
- महागठबंधन | MGB
- लोक जनशक्ति पार्टी (लोजपा)
- अन्य
- बीएसपि | BSP
- NOTA
- कह नहीं सकते / याद नहीं
- वोट नहीं दिया

**Question 12:** क्या आप बिहार सरकार द्वारा 2020 – 25 में किए गए काम से शंतुष्ट हैं ?
**Options:**
- बिलकुल शंतुष्ट हैं
- बिलकुल शंतुष्ट नहीं
- कुछ हद तक शंतुष्ट हैं
- कुछ कह नहीं सकते

**Question 13:** आप अगले मुख्यमंत्री के रूप में किसे देखना चाहते हैं ?
**Options:**
- नितीश कुमार
- तेजश्वी यादव
- सम्राट चौधरी
- चिराग पासवान
- प्रशांत किशोर
- अन्य

---

### Section 3 – Observational Questions

**Question 14:** आप गाँव में रहते हैं या शहर में?
**Options:**
- गाँव
- शहर

**Question 15:** ब्लाक का नाम (आप जहाँ है उस ब्लाक का नाम चुनें)
**Note:** Extract the exact block name mentioned in the transcript

**Question 16:** गाँव / पंचायत का नाम (आप जिस गाँव/ पंचायत में है उस पंचायत का नाम चुनें)
**Note:** Extract the exact village/panchayat name mentioned in the transcript

**Question 17:** सर क्या मैं आपका मोबाइल नंबर जान सकता हूँ ?
**Note:** Extract the mobile number if provided in the transcript

---

## ANALYSIS GUIDELINES:
1. **For Questions 1-14**: Select EXACTLY ONE option from the provided list that best matches the respondent's answer
2. **For Question 15-17**: Extract the exact information (block name, village/panchayat name, mobile number) as mentioned in the transcript
3. **Contextual Understanding**: Understand variations in Hindi responses. For example:
   - "हाँ", "जी हाँ", "बिल्कुल", "ठीक है" all mean "Yes"
   - "नहीं", "जी नहीं", "बिल्कुल नहीं" all mean "No"
   - Age ranges: Listen for specific numbers and categorize appropriately
4. **Partial Answers**: If the respondent gives an incomplete or unclear answer, choose "कुछ कह नहीं सकते" or equivalent option if available
5. **Question 9.1**: Only answer this if the respondent answered "नहीं" to Question 9

## OUTPUT FORMAT:
Return your analysis in the following JSON structure:

{
  "section_1": {
    "question_1": "selected option or Not Available",
    "question_2": "selected option or Not Available",
    "question_3": "selected option or Not Available",
    "question_4": "selected option or Not Available",
    "question_5": "selected option or Not Available",
    "question_6": "answer or Not Available"
  },
  "section_2": {
    "question_7": "selected option or Not Available",
    "question_8": "selected option or Not Available",
    "question_9": "selected option or Not Available",
    "question_9_1": "answer or Not Available",
    "question_10": "selected option or Not Available",
    "question_11": "selected option or Not Available",
    "question_12": "selected option or Not Available",
    "question_13": "selected option or Not Available"
  },
  "section_3": {
    "question_14": "selected option or Not Available",
    "question_15": "block name or Not Available",
    "question_16": "village/panchayat name or Not Available",
    "question_17": "mobile number or Not Available"
  }
}

## IMPORTANT REMINDERS:
- **DO NOT TRANSLATE** the options - keep them in Hindi as provided
- **DO NOT INVENT** answers - only extract from the transcript. U can do a bit assumption by taking word from the transcript but DONOT GUESS COMPLETELY.
- **ENSURE VALID JSON** - proper formatting with quotes and commas
- **ONE ANSWER PER QUESTION** - select only one option from the provided list
- **EXACT OPTION MATCH** - use the exact text of the option as provided above

Now, please analyze the given Hindi transcript and provide the extracted information in the specified JSON format:
'''

    def _load_json_file(self, file_path: str) -> dict:
        """Load JSON file and return as dictionary"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_audio_to_base64(self, file_path: str) -> str:
        """Convert audio file to base64 encoding"""
        with open(file_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")

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

    def process_audio(
        self,
        audio_file_path: str,
        output_dir: str = "./output",
        transcription_filename: str = "hindi_audio_output.json",
        analysis_filename: str = "hindi_analysis_output.json",
        audio_mime_type: str = "audio/m4a"
    ) -> dict:
        """
        Process audio file with transcription and analysis using the two JSON configs
        
        Args:
            audio_file_path: Path to the audio file
            output_dir: Directory to save output files
            transcription_filename: Name for transcription output file
            analysis_filename: Name for analysis output file
            audio_mime_type: MIME type of the audio file
            
        Returns:
            Dictionary containing paths and content of transcription and analysis
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        transcription_path = os.path.join(output_dir, transcription_filename)
        analysis_path = os.path.join(output_dir, analysis_filename)
        
        # Load audio as base64
        audio_base64 = self._load_audio_to_base64(audio_file_path)
        
        # Perform transcription
        contents_transcription = [
            {'mime_type': audio_mime_type, 'data': audio_base64},
            self.transcription_prompt
        ]
        
        transcription_response = self.model.generate_content(
            contents_transcription,
            generation_config=self.generation_config
        )
        
        # Save transcription
        self._save_output(transcription_response.text, transcription_path, clean=True)
        
        # Load transcription for analysis
        transcript_base64 = self._load_json_to_base64(transcription_path)
        
        # Perform analysis
        contents_analysis = [
            {'mime_type': 'text/plain', 'data': transcript_base64},
            self.analysis_prompt
        ]
        
        analysis_response = self.model.generate_content(
            contents_analysis,
            generation_config=self.generation_config
        )
        
        # Save analysis
        self._save_output(analysis_response.text, analysis_path, clean=True)
        
        # Load results
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
            'analysis': analysis_content,
            'json_config_1': self.json_config_1,
            'json_config_2': self.json_config_2
        }


def run_pipeline(audio_path: Path, json_path_1: Path, json_path_2: Path):
    """
    Run the complete pipeline with audio file and two JSON configuration files
    
    Args:
        audio_path: Path to audio file
        json_path_1: Path to first JSON configuration file
        json_path_2: Path to second JSON configuration file
        
    Returns:
        Tuple of (transcription_path, analysis_path, transcription_content, analysis_content)
    """
    # The first JSON file is used as credentials (maintaining backward compatibility)
    credentials_path = str(json_path_1)
    
    # Create output directory
    out_dir = tempfile.mkdtemp(prefix="hindi-audio-pipeline-")
    
    # Initialize pipeline with all three files
    pipeline = HindiAudioAnalysisPipeline(
        credentials_path=credentials_path,
        json_config_1_path=str(json_path_1),
        json_config_2_path=str(json_path_2)
    )
    
    # Process audio
    result = pipeline.process_audio(
        audio_file_path=str(audio_path),
        output_dir=out_dir
    )
    
    return (
        result['transcription_path'],
        result['analysis_path'],
        result['transcription'],
        result['analysis']
    )
